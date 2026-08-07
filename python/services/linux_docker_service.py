"""远程主机 Docker 管理：经 SSH 执行 docker CLI，返回结构化结果。"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime
from io import StringIO
from typing import Any, Optional

import paramiko

from db import get_connection
from services.linux_host_service import get_host_credentials, is_windows_os

# 操作审计表由 db/linux.init 创建


def _fmt_dt(v: Any) -> str:
    if isinstance(v, datetime):
        return v.strftime('%Y-%m-%d %H:%M:%S')
    return str(v or '')


def _open_client(host_id: int) -> paramiko.SSHClient:
    cred = get_host_credentials(host_id)
    if is_windows_os(cred.get('osName')):
        raise ValueError('Docker 管理暂不支持 Windows 主机')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict[str, Any] = {
        'hostname': cred['host'],
        'port': cred['port'],
        'username': cred['username'],
        'timeout': 20,
        'allow_agent': False,
        'look_for_keys': False,
    }
    if cred['authType'] == 'key' and cred.get('privateKey'):
        try:
            kwargs['pkey'] = paramiko.RSAKey.from_private_key(StringIO(cred['privateKey']))
        except Exception:
            kwargs['pkey'] = paramiko.Ed25519Key.from_private_key(StringIO(cred['privateKey']))
    else:
        kwargs['password'] = cred.get('password') or ''
    client.connect(**kwargs)
    return client


def ssh_exec(host_id: int, command: str, timeout: int = 60) -> tuple[int, str, str]:
    """执行远程命令，返回 (exit_code, stdout, stderr)。"""
    client = _open_client(host_id)
    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = (stdout.read() or b'').decode('utf-8', errors='ignore')
        err = (stderr.read() or b'').decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        return code, out, err
    finally:
        client.close()


def _require_ok(host_id: int, command: str, timeout: int = 60) -> str:
    code, out, err = ssh_exec(host_id, command, timeout=timeout)
    if code != 0:
        msg = (err or out or f'命令失败 exit={code}').strip()
        raise ValueError(msg[:500])
    return out


def _parse_json_lines(raw: str) -> list[Any]:
    items: list[Any] = []
    for line in (raw or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def _parse_json(raw: str) -> Any:
    text = (raw or '').strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 某些版本输出 NDJSON
        lines = _parse_json_lines(text)
        return lines if lines else None


def log_audit(
    host_id: int,
    username: str,
    action: str,
    target: str = '',
    detail: str = '',
    ok: bool = True,
) -> None:
    user = (username or '').strip() or 'unknown'
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_docker_audit
                    (host_id, username, action, target, detail, success)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    int(host_id),
                    user[:64],
                    (action or '')[:64],
                    (target or '')[:255],
                    (detail or '')[:2000],
                    1 if ok else 0,
                ),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def list_audit(
    host_id: Optional[int] = None,
    username: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ['1=1']
    args: list[Any] = []
    if host_id:
        clauses.append('host_id = %s')
        args.append(int(host_id))
    if username:
        clauses.append('username = %s')
        args.append(username.strip())
    args.append(min(max(int(limit or 100), 1), 500))
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM linux_docker_audit
                WHERE {' AND '.join(clauses)}
                ORDER BY id DESC
                LIMIT %s
                """,
                tuple(args),
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()
    return [
        {
            'id': r['id'],
            'hostId': r['host_id'],
            'username': r['username'],
            'action': r['action'],
            'target': r['target'],
            'detail': r['detail'],
            'success': bool(r['success']),
            'createdAt': _fmt_dt(r.get('created_at')),
        }
        for r in rows
    ]


def overview(host_id: int) -> dict[str, Any]:
    """Docker 概览。"""
    version_raw = _require_ok(host_id, 'docker version --format "{{json .}}" 2>/dev/null || docker version', 30)
    version_json = _parse_json(version_raw)
    engine = ''
    if isinstance(version_json, dict):
        engine = (
            ((version_json.get('Server') or {}).get('Version'))
            or ((version_json.get('Client') or {}).get('Version'))
            or ''
        )
    if not engine:
        # 纯文本兜底
        for line in version_raw.splitlines():
            if 'Version:' in line or 'Server Version' in line:
                engine = line.split(':', 1)[-1].strip()
                break

    info_raw = _require_ok(host_id, 'docker info --format "{{json .}}"', 30)
    info = _parse_json(info_raw) or {}
    running = int(info.get('ContainersRunning') or 0)
    paused = int(info.get('ContainersPaused') or 0)
    stopped = int(info.get('ContainersStopped') or 0)
    total = int(info.get('Containers') or (running + paused + stopped))
    images = int(info.get('Images') or 0)

    try:
        vol_raw = _require_ok(host_id, 'docker volume ls -q | wc -l', 20)
        volumes = int((vol_raw or '0').strip().split()[0])
    except Exception:
        volumes = 0
    try:
        net_raw = _require_ok(host_id, 'docker network ls -q | wc -l', 20)
        networks = int((net_raw or '0').strip().split()[0])
    except Exception:
        networks = 0

    storage = ''
    try:
        df_raw = _require_ok(host_id, 'docker system df --format "{{json .}}"', 40)
        # docker system df 输出多行 JSON（Type/Size/...）
        rows = _parse_json_lines(df_raw)
        if rows:
            parts = [f"{r.get('Type')}:{r.get('Size')}" for r in rows if isinstance(r, dict)]
            storage = ' · '.join(parts)
        else:
            storage = df_raw.strip()[:200]
    except Exception:
        storage = ''

    status = 'Running' if info.get('ServerVersion') or engine else 'Stop'
    return {
        'version': engine or str(info.get('ServerVersion') or ''),
        'status': status,
        'containers': {
            'total': total,
            'running': running,
            'stopped': stopped,
            'paused': paused,
        },
        'images': images,
        'volumes': volumes,
        'networks': networks,
        'storage': storage,
        'driver': str(info.get('Driver') or ''),
        'os': str(info.get('OperatingSystem') or ''),
    }


def list_containers(host_id: int, all_: bool = True, with_stats: bool = True) -> list[dict[str, Any]]:
    flag = '-a' if all_ else ''
    raw = _require_ok(
        host_id,
        f'docker ps {flag} --format "{{{{json .}}}}"',
        40,
    )
    items = []
    for row in _parse_json_lines(raw):
        if not isinstance(row, dict):
            continue
        names = str(row.get('Names') or '').lstrip('/')
        ports = str(row.get('Ports') or '')
        state = str(row.get('State') or row.get('Status') or '')
        items.append(
            {
                'id': str(row.get('ID') or ''),
                'name': names.split(',')[0] if names else '',
                'image': str(row.get('Image') or ''),
                'status': str(row.get('Status') or ''),
                'state': state.lower(),
                'created': str(row.get('CreatedAt') or ''),
                'ports': ports,
                'networks': str(row.get('Networks') or ''),
                'command': str(row.get('Command') or ''),
                'cpu': '',
                'mem': '',
                'memPerc': '',
            }
        )
    if with_stats and items:
        try:
            stats_map = {
                (s.get('name') or '').lstrip('/'): s for s in container_stats(host_id)
            }
            for it in items:
                s = stats_map.get(it['name']) or stats_map.get(it['id'])
                if not s:
                    continue
                it['cpu'] = s.get('cpu') or ''
                it['mem'] = s.get('memUsage') or ''
                it['memPerc'] = s.get('memPerc') or ''
        except Exception:
            pass
    return items


def container_detail(host_id: int, container: str) -> dict[str, Any]:
    """结构化容器详情（便于前端展示，同时附带 raw inspect）。"""
    raw = container_inspect(host_id, container)
    cfg = raw.get('Config') or {}
    host_cfg = raw.get('HostConfig') or {}
    state = raw.get('State') or {}
    net = raw.get('NetworkSettings') or {}
    mounts = raw.get('Mounts') or []
    ports = net.get('Ports') or {}
    port_list = []
    if isinstance(ports, dict):
        for cport, binds in ports.items():
            if not binds:
                port_list.append({'container': cport, 'host': ''})
                continue
            for b in binds or []:
                port_list.append(
                    {
                        'container': cport,
                        'host': f"{b.get('HostIp', '')}:{b.get('HostPort', '')}".strip(':'),
                    }
                )
    networks = []
    nets = net.get('Networks') or {}
    if isinstance(nets, dict):
        for name, info in nets.items():
            networks.append(
                {
                    'name': name,
                    'ip': (info or {}).get('IPAddress') or '',
                    'gateway': (info or {}).get('Gateway') or '',
                }
            )
    resources = {
        'nanoCpus': host_cfg.get('NanoCpus'),
        'memory': host_cfg.get('Memory'),
        'memorySwap': host_cfg.get('MemorySwap'),
        'cpuShares': host_cfg.get('CpuShares'),
        'deviceRequests': host_cfg.get('DeviceRequests') or [],
    }
    return {
        'id': str(raw.get('Id') or '')[:12],
        'name': str(raw.get('Name') or '').lstrip('/'),
        'created': str(raw.get('Created') or ''),
        'status': str(state.get('Status') or ''),
        'image': str(cfg.get('Image') or ''),
        'command': ' '.join(cfg.get('Cmd') or []) if isinstance(cfg.get('Cmd'), list) else str(cfg.get('Cmd') or ''),
        'entrypoint': cfg.get('Entrypoint') or [],
        'env': cfg.get('Env') or [],
        'ports': port_list,
        'networks': networks,
        'mounts': [
            {
                'type': m.get('Type'),
                'source': m.get('Source') or m.get('Name'),
                'destination': m.get('Destination'),
                'mode': m.get('Mode'),
                'rw': m.get('RW'),
            }
            for m in mounts
            if isinstance(m, dict)
        ],
        'restartPolicy': (host_cfg.get('RestartPolicy') or {}).get('Name') or '',
        'resources': resources,
        'platform': str(raw.get('Platform') or ''),
        'raw': raw,
    }


def container_inspect(host_id: int, container: str) -> dict[str, Any]:
    cid = (container or '').strip()
    if not cid:
        raise ValueError('请指定容器')
    raw = _require_ok(host_id, f'docker inspect {shlex.quote(cid)}', 40)
    data = _parse_json(raw)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError('无法解析容器详情')


def container_stats(host_id: int, container: str = '') -> list[dict[str, Any]]:
    target = shlex.quote(container.strip()) if container.strip() else ''
    cmd = (
        f'docker stats {target} --no-stream --format "{{{{json .}}}}"'
        if target
        else 'docker stats --no-stream --format "{{json .}}"'
    )
    raw = _require_ok(host_id, cmd, 60)
    items = []
    for row in _parse_json_lines(raw):
        if not isinstance(row, dict):
            continue
        items.append(
            {
                'id': str(row.get('ID') or row.get('Container') or ''),
                'name': str(row.get('Name') or ''),
                'cpu': str(row.get('CPUPerc') or ''),
                'memUsage': str(row.get('MemUsage') or ''),
                'memPerc': str(row.get('MemPerc') or ''),
                'netIO': str(row.get('NetIO') or ''),
                'blockIO': str(row.get('BlockIO') or ''),
            }
        )
    return items


_CONTAINER_ACTIONS = {
    'start': 'start',
    'stop': 'stop',
    'restart': 'restart',
    'pause': 'pause',
    'unpause': 'unpause',
    'remove': 'rm',
    'forceRemove': 'rm -f',
}


def container_action(
    host_id: int,
    container: str,
    action: str,
    username: str = '',
) -> dict[str, Any]:
    cid = (container or '').strip()
    act = (action or '').strip()
    if not cid:
        raise ValueError('请指定容器')
    if act not in _CONTAINER_ACTIONS:
        raise ValueError(f'不支持的操作：{act}')
    docker_act = _CONTAINER_ACTIONS[act]
    try:
        out = _require_ok(host_id, f'docker {docker_act} {shlex.quote(cid)}', 90)
        log_audit(host_id, username, act, cid, out.strip()[:500], True)
        return {'ok': True, 'output': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, act, cid, str(exc), False)
        raise


def container_logs(
    host_id: int,
    container: str,
    tail: int = 200,
    since: str = '',
    timestamps: bool = False,
) -> dict[str, Any]:
    cid = (container or '').strip()
    if not cid:
        raise ValueError('请指定容器')
    n = min(max(int(tail or 200), 1), 5000)
    parts = [f'docker logs --tail {n}']
    if timestamps:
        parts.append('--timestamps')
    if since.strip():
        parts.append(f'--since {shlex.quote(since.strip())}')
    parts.append(shlex.quote(cid))
    code, out, err = ssh_exec(host_id, ' '.join(parts) + ' 2>&1', timeout=60)
    text = out or err
    if code != 0 and not text.strip():
        raise ValueError((err or out or '读取日志失败').strip()[:500])
    return {'container': cid, 'tail': n, 'logs': text}


def list_images(host_id: int) -> list[dict[str, Any]]:
    raw = _require_ok(host_id, 'docker images --format "{{json .}}"', 40)
    # 统计镜像被哪些容器使用
    used: dict[str, list[str]] = {}
    try:
        ps = _require_ok(host_id, 'docker ps -a --format "{{json .}}"', 40)
        for row in _parse_json_lines(ps):
            if not isinstance(row, dict):
                continue
            img = str(row.get('Image') or '')
            name = str(row.get('Names') or '').lstrip('/').split(',')[0]
            if img:
                used.setdefault(img, []).append(name)
                # 也按短 ID 索引
                used.setdefault(img.split(':')[0], []).append(name)
    except Exception:
        pass

    items = []
    for row in _parse_json_lines(raw):
        if not isinstance(row, dict):
            continue
        repo = str(row.get('Repository') or '')
        tag = str(row.get('Tag') or '')
        ref = f'{repo}:{tag}' if repo and tag else repo
        iid = str(row.get('ID') or '')
        users = list(dict.fromkeys((used.get(ref) or []) + (used.get(repo) or []) + (used.get(iid) or [])))
        items.append(
            {
                'id': iid,
                'repository': repo,
                'tag': tag,
                'size': str(row.get('Size') or ''),
                'created': str(row.get('CreatedAt') or row.get('CreatedSince') or ''),
                'usedBy': users,
                'usedCount': len(users),
            }
        )
    return items


def image_inspect(host_id: int, image: str) -> dict[str, Any]:
    ref = (image or '').strip()
    if not ref:
        raise ValueError('请指定镜像')
    raw = _require_ok(host_id, f'docker image inspect {shlex.quote(ref)}', 40)
    data = _parse_json(raw)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError('无法解析镜像详情')


def image_pull(host_id: int, image: str, username: str = '') -> dict[str, Any]:
    ref = (image or '').strip()
    if not ref:
        raise ValueError('请填写镜像名称')
    try:
        out = _require_ok(host_id, f'docker pull {shlex.quote(ref)}', 300)
        log_audit(host_id, username, 'pull', ref, out[-500:], True)
        return {'ok': True, 'output': out[-2000:]}
    except ValueError as exc:
        log_audit(host_id, username, 'pull', ref, str(exc), False)
        raise


def image_remove(host_id: int, image: str, force: bool = False, username: str = '') -> dict[str, Any]:
    ref = (image or '').strip()
    if not ref:
        raise ValueError('请指定镜像')
    flag = '-f ' if force else ''
    try:
        out = _require_ok(host_id, f'docker rmi {flag}{shlex.quote(ref)}', 90)
        log_audit(host_id, username, 'rmi', ref, out.strip()[:500], True)
        return {'ok': True, 'output': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, 'rmi', ref, str(exc), False)
        raise


def image_export_bytes(host_id: int, image: str) -> tuple[str, bytes]:
    """导出镜像 tar（经远程临时文件 + base64，适合中小镜像）。"""
    import base64

    ref = (image or '').strip()
    if not ref:
        raise ValueError('请指定镜像')
    safe = re.sub(r'[^\w.-]+', '_', ref)[:80]
    remote = f'/tmp/maxadmin_img_{safe}.tar'
    try:
        _require_ok(host_id, f'docker save -o {shlex.quote(remote)} {shlex.quote(ref)}', 600)
        code, b64, err = ssh_exec(
            host_id,
            f'base64 {shlex.quote(remote)}; rm -f {shlex.quote(remote)}',
            timeout=600,
        )
        if code != 0:
            raise ValueError((err or '导出失败').strip()[:500])
        data = base64.b64decode(''.join(b64.split()))
        log_audit(host_id, '', 'imageExport', ref, f'size={len(data)}', True)
        return f'{safe}.tar', data
    except Exception:
        ssh_exec(host_id, f'rm -f {shlex.quote(remote)}', 20)
        raise


def image_import_file(host_id: int, filename: str, content: bytes, username: str = '') -> dict[str, Any]:
    if not content:
        raise ValueError('空文件')
    if len(content) > 800 * 1024 * 1024:
        raise ValueError('导入文件过大（限制 800MB）')
    import uuid

    remote = f'/tmp/maxadmin_load_{uuid.uuid4().hex}.tar'
    client = _open_client(host_id)
    try:
        sftp = client.open_sftp()
        try:
            with sftp.file(remote, 'wb') as f:
                f.write(content)
        finally:
            sftp.close()
        _stdin, stdout, stderr = client.exec_command(
            f'docker load -i {shlex.quote(remote)}; rm -f {shlex.quote(remote)}',
            timeout=600,
        )
        out = (stdout.read() or b'').decode('utf-8', errors='ignore')
        err = (stderr.read() or b'').decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        if code != 0:
            log_audit(host_id, username, 'imageImport', filename, err or out, False)
            raise ValueError((err or out or '导入失败').strip()[:500])
        log_audit(host_id, username, 'imageImport', filename, out[-500:], True)
        return {'ok': True, 'output': out.strip()}
    finally:
        client.close()


def list_networks(host_id: int) -> list[dict[str, Any]]:
    raw = _require_ok(host_id, 'docker network ls --format "{{json .}}"', 30)
    items = []
    for row in _parse_json_lines(raw):
        if not isinstance(row, dict):
            continue
        name = str(row.get('Name') or '')
        containers: list[str] = []
        try:
            detail = network_inspect(host_id, name)
            cons = (detail.get('Containers') or {}) if isinstance(detail, dict) else {}
            if isinstance(cons, dict):
                containers = [
                    str((v or {}).get('Name') or k) for k, v in cons.items()
                ]
        except Exception:
            pass
        items.append(
            {
                'id': str(row.get('ID') or ''),
                'name': name,
                'driver': str(row.get('Driver') or ''),
                'scope': str(row.get('Scope') or ''),
                'containers': containers,
                'containerCount': len(containers),
            }
        )
    return items


def network_inspect(host_id: int, name: str) -> dict[str, Any]:
    n = (name or '').strip()
    if not n:
        raise ValueError('请指定网络')
    raw = _require_ok(host_id, f'docker network inspect {shlex.quote(n)}', 30)
    data = _parse_json(raw)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError('无法解析网络详情')


def network_create(
    host_id: int,
    name: str,
    driver: str = 'bridge',
    username: str = '',
) -> dict[str, Any]:
    n = (name or '').strip()
    d = (driver or 'bridge').strip() or 'bridge'
    if not n:
        raise ValueError('请填写网络名称')
    try:
        out = _require_ok(
            host_id,
            f'docker network create --driver {shlex.quote(d)} {shlex.quote(n)}',
            40,
        )
        log_audit(host_id, username, 'networkCreate', n, out.strip(), True)
        return {'ok': True, 'id': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, 'networkCreate', n, str(exc), False)
        raise


def network_remove(host_id: int, name: str, username: str = '') -> dict[str, Any]:
    n = (name or '').strip()
    if not n:
        raise ValueError('请指定网络')
    try:
        out = _require_ok(host_id, f'docker network rm {shlex.quote(n)}', 40)
        log_audit(host_id, username, 'networkRm', n, out.strip(), True)
        return {'ok': True, 'output': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, 'networkRm', n, str(exc), False)
        raise


def list_volumes(host_id: int) -> list[dict[str, Any]]:
    raw = _require_ok(host_id, 'docker volume ls --format "{{json .}}"', 30)
    used: dict[str, list[str]] = {}
    try:
        ps = _require_ok(host_id, 'docker ps -a --format "{{.Names}}\t{{.Mounts}}"', 40)
        for line in ps.splitlines():
            if '\t' not in line:
                continue
            name, mounts = line.split('\t', 1)
            name = name.lstrip('/')
            for part in mounts.split(','):
                part = part.strip()
                if part:
                    used.setdefault(part, []).append(name)
    except Exception:
        pass

    items = []
    names = []
    for row in _parse_json_lines(raw):
        if not isinstance(row, dict):
            continue
        names.append(str(row.get('Name') or ''))
        items.append(
            {
                'name': str(row.get('Name') or ''),
                'driver': str(row.get('Driver') or ''),
                'mountpoint': str(row.get('Mountpoint') or ''),
                'created': '',
                'usedBy': [],
                'usedCount': 0,
            }
        )
    if names:
        try:
            quoted = ' '.join(shlex.quote(n) for n in names if n)
            insp = _require_ok(host_id, f'docker volume inspect {quoted}', 60)
            data = _parse_json(insp)
            rows = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
            by_name = {str(r.get('Name') or ''): r for r in rows if isinstance(r, dict)}
            for it in items:
                r = by_name.get(it['name']) or {}
                it['mountpoint'] = str(r.get('Mountpoint') or it['mountpoint'])
                it['created'] = str(r.get('CreatedAt') or '')
                users = used.get(it['name']) or []
                it['usedBy'] = users
                it['usedCount'] = len(users)
        except Exception:
            for it in items:
                users = used.get(it['name']) or []
                it['usedBy'] = users
                it['usedCount'] = len(users)
    return items


def volume_inspect(host_id: int, name: str) -> dict[str, Any]:
    n = (name or '').strip()
    if not n:
        raise ValueError('请指定数据卷')
    raw = _require_ok(host_id, f'docker volume inspect {shlex.quote(n)}', 30)
    data = _parse_json(raw)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError('无法解析数据卷详情')


def volume_create(host_id: int, name: str, username: str = '') -> dict[str, Any]:
    n = (name or '').strip()
    if not n:
        raise ValueError('请填写数据卷名称')
    try:
        out = _require_ok(host_id, f'docker volume create {shlex.quote(n)}', 30)
        log_audit(host_id, username, 'volumeCreate', n, out.strip(), True)
        return {'ok': True, 'name': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, 'volumeCreate', n, str(exc), False)
        raise


def volume_remove(host_id: int, name: str, username: str = '') -> dict[str, Any]:
    n = (name or '').strip()
    if not n:
        raise ValueError('请指定数据卷')
    try:
        out = _require_ok(host_id, f'docker volume rm {shlex.quote(n)}', 40)
        log_audit(host_id, username, 'volumeRm', n, out.strip(), True)
        return {'ok': True, 'output': out.strip()}
    except ValueError as exc:
        log_audit(host_id, username, 'volumeRm', n, str(exc), False)
        raise


def volume_backup_bytes(host_id: int, name: str, username: str = '') -> tuple[str, bytes]:
    """备份 volume 为 tar.gz。"""
    import base64
    import uuid

    n = (name or '').strip()
    if not n:
        raise ValueError('请指定数据卷')
    fname = f'maxadmin_vol_{uuid.uuid4().hex}.tgz'
    remote = f'/tmp/{fname}'
    cmd = (
        f'docker run --rm -v {shlex.quote(n)}:/data:ro -v /tmp:/backup alpine:3.19 '
        f'sh -c "tar czf /backup/{fname} -C /data ."'
    )
    try:
        _require_ok(host_id, cmd, 600)
        code, b64, err = ssh_exec(host_id, f'base64 {shlex.quote(remote)}; rm -f {shlex.quote(remote)}', 600)
        if code != 0:
            raise ValueError((err or '备份失败').strip()[:500])
        data = base64.b64decode(''.join(b64.split()))
        log_audit(host_id, username, 'volumeBackup', n, f'size={len(data)}', True)
        return f'{n}.tgz', data
    except Exception:
        ssh_exec(host_id, f'rm -f {shlex.quote(remote)}', 20)
        raise


def volume_restore_file(
    host_id: int,
    name: str,
    content: bytes,
    username: str = '',
) -> dict[str, Any]:
    """从 tar.gz 恢复到指定 volume（覆盖写入）。"""
    import uuid

    n = (name or '').strip()
    if not n:
        raise ValueError('请指定数据卷')
    if not content:
        raise ValueError('空备份文件')
    # 确保 volume 存在
    try:
        volume_create(host_id, n, username=username)
    except ValueError:
        pass
    fname = f'maxadmin_restore_{uuid.uuid4().hex}.tgz'
    remote = f'/tmp/{fname}'
    client = _open_client(host_id)
    try:
        sftp = client.open_sftp()
        try:
            with sftp.file(remote, 'wb') as f:
                f.write(content)
        finally:
            sftp.close()
        cmd = (
            f'docker run --rm -v {shlex.quote(n)}:/data -v /tmp:/backup alpine:3.19 '
            f'sh -c "tar xzf /backup/{fname} -C /data"; rm -f {shlex.quote(remote)}'
        )
        _stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
        out = (stdout.read() or b'').decode('utf-8', errors='ignore')
        err = (stderr.read() or b'').decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        if code != 0:
            log_audit(host_id, username, 'volumeRestore', n, err or out, False)
            raise ValueError((err or out or '恢复失败').strip()[:500])
        log_audit(host_id, username, 'volumeRestore', n, 'ok', True)
        return {'ok': True, 'output': out.strip() or 'restored'}
    finally:
        client.close()


def compose_ls(host_id: int) -> list[dict[str, Any]]:
    # 优先 docker compose，兼容 docker-compose
    code, out, err = ssh_exec(
        host_id,
        'docker compose ls --format json 2>/dev/null || docker-compose ls --format json 2>/dev/null',
        40,
    )
    if code != 0 and not out.strip():
        return []
    data = _parse_json(out)
    rows: list[Any]
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = [data]
    else:
        rows = _parse_json_lines(out)
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get('Name') or '')
        status = str(row.get('Status') or '')
        # Status 形如 "running(3)" / "exited(1)"
        service_count = 0
        m = re.search(r'\((\d+)\)', status)
        if m:
            service_count = int(m.group(1))
        else:
            try:
                ps_out = _require_ok(
                    host_id,
                    f'(docker compose -p {shlex.quote(name)} ps -q || docker-compose -p {shlex.quote(name)} ps -q) | wc -l',
                    40,
                )
                service_count = int((ps_out or '0').strip().split()[0])
            except Exception:
                service_count = 0
        items.append(
            {
                'name': name,
                'status': status,
                'configFiles': str(row.get('ConfigFiles') or ''),
                'serviceCount': service_count,
                'updatedAt': str(row.get('UpdatedAt') or row.get('updatedAt') or ''),
            }
        )
    return items


def compose_config(host_id: int, project: str, file: str = '') -> dict[str, Any]:
    name = (project or '').strip()
    if not name:
        raise ValueError('请指定 Compose 应用名')
    file_flag = f'-f {shlex.quote(file.strip())} ' if file.strip() else ''
    cmd = (
        f'(docker compose -p {shlex.quote(name)} {file_flag}config '
        f'|| docker-compose -p {shlex.quote(name)} {file_flag}config)'
    )
    out = _require_ok(host_id, cmd, 60)
    return {'project': name, 'config': out}


def compose_logs(
    host_id: int,
    project: str,
    tail: int = 200,
    file: str = '',
) -> dict[str, Any]:
    name = (project or '').strip()
    if not name:
        raise ValueError('请指定 Compose 应用名')
    n = min(max(int(tail or 200), 1), 5000)
    file_flag = f'-f {shlex.quote(file.strip())} ' if file.strip() else ''
    cmd = (
        f'(docker compose -p {shlex.quote(name)} {file_flag}logs --tail {n} '
        f'|| docker-compose -p {shlex.quote(name)} {file_flag}logs --tail {n}) 2>&1'
    )
    code, out, err = ssh_exec(host_id, cmd, 90)
    text = out or err
    if code != 0 and not text.strip():
        raise ValueError((err or out or '读取失败').strip()[:500])
    return {'project': name, 'logs': text}


def compose_action(
    host_id: int,
    project: str,
    action: str,
    file: str = '',
    username: str = '',
) -> dict[str, Any]:
    name = (project or '').strip()
    act = (action or '').strip()
    if not name:
        raise ValueError('请指定 Compose 应用名')
    mapping = {
        'up': 'up -d',
        'down': 'down',
        'restart': 'restart',
        'stop': 'stop',
        'start': 'start',
        'ps': 'ps',
        'pull': 'pull',
        'update': 'update',
    }
    if act not in mapping:
        raise ValueError(f'不支持的 Compose 操作：{act}')
    file_flag = f'-f {shlex.quote(file.strip())} ' if file.strip() else ''
    if act == 'update':
        cmd = (
            f'(docker compose -p {shlex.quote(name)} {file_flag}pull '
            f'&& docker compose -p {shlex.quote(name)} {file_flag}up -d) '
            f'|| (docker-compose -p {shlex.quote(name)} {file_flag}pull '
            f'&& docker-compose -p {shlex.quote(name)} {file_flag}up -d)'
        )
    else:
        cmd = (
            f'(docker compose -p {shlex.quote(name)} {file_flag}{mapping[act]} '
            f'|| docker-compose -p {shlex.quote(name)} {file_flag}{mapping[act]})'
        )
    try:
        out = _require_ok(host_id, cmd, 300)
        log_audit(host_id, username, f'compose:{act}', name, out[-500:], True)
        return {'ok': True, 'output': out[-3000:]}
    except ValueError as exc:
        log_audit(host_id, username, f'compose:{act}', name, str(exc), False)
        raise


def bridge_exec_websocket(ws, host_id: int, container: str, username: str = '') -> None:
    """docker exec -it 交互终端，桥接到 WebSocket。"""
    cid = (container or '').strip()
    if not cid:
        try:
            ws.send('{"type":"error","message":"缺少容器名"}')
        except Exception:
            pass
        ws.close()
        return

    client = None
    channel = None
    try:
        client = _open_client(host_id)
        # 优先 bash，其次 sh
        shell = (
            f'docker exec -it {shlex.quote(cid)} /bin/bash 2>/dev/null '
            f'|| docker exec -it {shlex.quote(cid)} /bin/sh'
        )
        transport = client.get_transport()
        if not transport:
            raise ValueError('SSH 传输不可用')
        channel = transport.open_session()
        channel.get_pty(term='xterm-256color', width=120, height=36)
        channel.exec_command(shell)
        log_audit(host_id, username, 'exec', cid, 'open terminal', True)

        import threading

        stop = threading.Event()

        def pump():
            try:
                while not stop.is_set():
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if not data:
                            break
                        ws.send(data)
                    elif channel.exit_status_ready():
                        break
                    else:
                        stop.wait(0.02)
            except Exception:
                pass
            finally:
                stop.set()
                try:
                    ws.close()
                except Exception:
                    pass

        t = threading.Thread(target=pump, daemon=True)
        t.start()

        while not stop.is_set():
            message = ws.receive()
            if message is None:
                break
            if isinstance(message, bytes):
                channel.send(message)
                continue
            text = str(message)
            if text.startswith('{'):
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    channel.send(text.encode('utf-8'))
                    continue
                if payload.get('type') == 'resize':
                    cols = int(payload.get('cols') or 120)
                    rows = int(payload.get('rows') or 36)
                    try:
                        channel.resize_pty(width=cols, height=rows)
                    except Exception:
                        pass
                    continue
                if payload.get('type') == 'ping':
                    ws.send(json.dumps({'type': 'pong'}))
                    continue
            channel.send(text.encode('utf-8'))
    except Exception as exc:  # noqa: BLE001
        try:
            ws.send(json.dumps({'type': 'error', 'message': str(exc)}))
        except Exception:
            pass
        log_audit(host_id, username, 'exec', cid, str(exc), False)
    finally:
        try:
            if channel is not None:
                channel.close()
        except Exception:
            pass
        try:
            if client is not None:
                client.close()
        except Exception:
            pass
