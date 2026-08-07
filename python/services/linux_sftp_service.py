"""远程文件 SFTP 服务（支持 Linux 与 Windows OpenSSH）。"""

from __future__ import annotations

import os
import re
import stat
from io import BytesIO
from typing import Any, Optional

import paramiko
from werkzeug.datastructures import FileStorage

from services.linux_host_service import get_host_credentials, is_windows_os, mark_connected


TEXT_EXTS = {
    '.sh', '.py', '.java', '.vue', '.html', '.htm', '.css', '.js', '.ts', '.tsx',
    '.jsx', '.yml', '.yaml', '.json', '.xml', '.ini', '.conf', '.cfg', '.log',
    '.md', '.txt', '.env', '.properties', '.toml', '.sql', '.go', '.rs', '.c',
    '.h', '.cpp', '.hpp', '.rb', '.php', '.scss', '.less', '.ps1', '.bat', '.cmd',
}

_DRIVE_RE = re.compile(r'^[A-Za-z]:')


def _open_sftp(host_id: int) -> tuple[paramiko.SSHClient, paramiko.SFTPClient, bool]:
    cred = get_host_credentials(host_id)
    windows = is_windows_os(cred.get('osName'))
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
        from io import StringIO

        try:
            kwargs['pkey'] = paramiko.RSAKey.from_private_key(StringIO(cred['privateKey']))
        except Exception:
            kwargs['pkey'] = paramiko.Ed25519Key.from_private_key(StringIO(cred['privateKey']))
    else:
        kwargs['password'] = cred.get('password') or ''

    client.connect(**kwargs)
    sftp = client.open_sftp()
    mark_connected(host_id, 'online')
    return client, sftp, windows


def default_root(windows: bool) -> str:
    return 'C:/' if windows else '/'


def _safe_path(path: str, *, windows: bool = False) -> str:
    raw = (path or '').replace('\\', '/').strip()
    if windows:
        if not raw or raw in {'/', '.'}:
            return 'C:/'
        # OpenSSH 偶发形式：/C:/Users -> C:/Users
        if len(raw) >= 3 and raw[0] == '/' and raw[2] == ':':
            raw = raw[1:]
        if not _DRIVE_RE.match(raw):
            raw = 'C:/' + raw.lstrip('/')
        # 规范化 ..
        drive = raw[:2]
        rest = raw[2:].lstrip('/')
        parts: list[str] = []
        for part in rest.split('/'):
            if not part or part == '.':
                continue
            if part == '..':
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return drive + '/' + '/'.join(parts) if parts else drive + '/'

    raw = raw or '/'
    if not raw.startswith('/'):
        raw = '/' + raw
    parts = []
    for part in raw.split('/'):
        if not part or part == '.':
            continue
        if part == '..':
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return '/' + '/'.join(parts)


def _join_child(parent: str, name: str, *, windows: bool) -> str:
    parent = _safe_path(parent, windows=windows)
    if windows:
        base = parent.rstrip('/')
        return f'{base}/{name}'
    if parent == '/':
        return '/' + name
    return parent.rstrip('/') + '/' + name


def _breadcrumbs(path: str, *, windows: bool) -> list[dict[str, str]]:
    path = _safe_path(path, windows=windows)
    if windows:
        crumbs = [{'name': 'C:', 'path': 'C:/'}]
        if path.rstrip('/') == 'C:':
            return crumbs
        rest = path[2:].strip('/')
        if not rest:
            return crumbs
        acc = 'C:'
        for part in rest.split('/'):
            acc += '/' + part
            crumbs.append({'name': part, 'path': acc if acc.endswith(':') else acc})
        # 保证目录 path 带尾部一致性：中间节点用无尾斜杠也可，list 时会 normalize
        for i, c in enumerate(crumbs):
            if i == 0:
                crumbs[i]['path'] = 'C:/'
            elif not c['path'].endswith('/') and i < len(crumbs) - 1:
                pass
        return crumbs

    crumbs = [{'name': '/', 'path': '/'}]
    if path == '/':
        return crumbs
    acc = ''
    for part in path.strip('/').split('/'):
        acc += '/' + part
        crumbs.append({'name': part, 'path': acc})
    return crumbs


def list_dir(host_id: int, path: str = '') -> dict[str, Any]:
    client, sftp, windows = _open_sftp(host_id)
    try:
        if not (path or '').strip():
            path = default_root(windows)
        path = _safe_path(path, windows=windows)
        entries = []
        for attr in sftp.listdir_attr(path):
            name = attr.filename
            if name in {'.', '..'}:
                continue
            is_dir = stat.S_ISDIR(attr.st_mode)
            full = _join_child(path, name, windows=windows)
            ext = os.path.splitext(name)[1].lower()
            entries.append(
                {
                    'name': name,
                    'path': full,
                    'isDir': is_dir,
                    'size': int(attr.st_size or 0),
                    'mtime': int(attr.st_mtime or 0),
                    'mode': oct(attr.st_mode & 0o777),
                    'ext': ext.lstrip('.'),
                    'editable': (not is_dir) and ext in TEXT_EXTS,
                }
            )
        entries.sort(key=lambda x: (not x['isDir'], x['name'].lower()))
        return {
            'path': path,
            'windows': windows,
            'breadcrumbs': _breadcrumbs(path, windows=windows),
            'list': entries,
        }
    finally:
        sftp.close()
        client.close()


def mkdir(host_id: int, path: str) -> None:
    client, sftp, windows = _open_sftp(host_id)
    try:
        sftp.mkdir(_safe_path(path, windows=windows))
    finally:
        sftp.close()
        client.close()


def rename(host_id: int, old_path: str, new_path: str) -> None:
    client, sftp, windows = _open_sftp(host_id)
    try:
        sftp.rename(
            _safe_path(old_path, windows=windows),
            _safe_path(new_path, windows=windows),
        )
    finally:
        sftp.close()
        client.close()


def remove(host_id: int, path: str) -> None:
    client, sftp, windows = _open_sftp(host_id)
    try:
        _rm_recursive(sftp, _safe_path(path, windows=windows), windows=windows)
    finally:
        sftp.close()
        client.close()


def _rm_recursive(sftp: paramiko.SFTPClient, path: str, *, windows: bool) -> None:
    try:
        attr = sftp.stat(path)
    except FileNotFoundError as exc:
        raise ValueError('路径不存在') from exc
    if stat.S_ISDIR(attr.st_mode):
        for child in sftp.listdir_attr(path):
            child_path = _join_child(path, child.filename, windows=windows)
            _rm_recursive(sftp, child_path, windows=windows)
        sftp.rmdir(path)
    else:
        sftp.remove(path)


def upload(host_id: int, path: str, upload: FileStorage) -> dict[str, Any]:
    if upload is None:
        raise ValueError('请选择文件（未收到 multipart 文件字段）')
    client, sftp, windows = _open_sftp(host_id)
    try:
        dir_path = _safe_path(path, windows=windows)
        raw_name = (upload.filename or '').replace('\\', '/')
        name = os.path.basename(raw_name) or 'upload.bin'
        if name in {'.', '..'}:
            raise ValueError('文件名无效')
        target = _join_child(dir_path, name, windows=windows)

        try:
            sftp.stat(dir_path)
        except FileNotFoundError as exc:
            raise ValueError(f'目标目录不存在：{dir_path}') from exc

        # FileStorage.stream 可能不可 seek；用块写入更稳，且避免 putfo confirm 误报
        try:
            if hasattr(upload.stream, 'seek'):
                upload.stream.seek(0)
        except Exception:
            pass

        with sftp.file(target, 'wb') as remote:
            try:
                remote.set_pipelined(True)
            except Exception:
                pass
            while True:
                chunk = upload.stream.read(1024 * 64)
                if not chunk:
                    break
                remote.write(chunk)

        return {'name': name, 'path': target}
    finally:
        sftp.close()
        client.close()


def download_bytes(host_id: int, path: str) -> tuple[bytes, str]:
    client, sftp, windows = _open_sftp(host_id)
    try:
        path = _safe_path(path, windows=windows)
        buf = BytesIO()
        sftp.getfo(path, buf)
        return buf.getvalue(), os.path.basename(path.rstrip('/'))
    finally:
        sftp.close()
        client.close()


def read_text(host_id: int, path: str, max_bytes: int = 2_000_000) -> dict[str, Any]:
    data, name = download_bytes(host_id, path)
    if len(data) > max_bytes:
        raise ValueError('文件过大，无法在线编辑')
    try:
        content = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('无法以 UTF-8 解码该文件') from exc
    return {'name': name, 'path': path, 'content': content}


def write_text(host_id: int, path: str, content: str) -> None:
    client, sftp, windows = _open_sftp(host_id)
    try:
        path = _safe_path(path, windows=windows)
        with sftp.file(path, 'w') as f:
            f.write(content.encode('utf-8'))
    finally:
        sftp.close()
        client.close()


def chmod(host_id: int, path: str, mode: str) -> None:
    raw = (mode or '').strip().lower().replace('0o', '')
    if raw.startswith('0') and len(raw) > 1 and raw[1].isdigit():
        raw = raw.lstrip('0') or '0'
    try:
        mode_int = int(raw, 8)
    except ValueError as exc:
        raise ValueError('权限格式无效，例如 755 或 0o644') from exc
    client, sftp, windows = _open_sftp(host_id)
    try:
        sftp.chmod(_safe_path(path, windows=windows), mode_int)
    finally:
        sftp.close()
        client.close()


def chown(host_id: int, path: str, uid: int, gid: int) -> None:
    if uid is None or gid is None:
        raise ValueError('uid/gid 必填')
    client, sftp, windows = _open_sftp(host_id)
    try:
        if windows:
            raise ValueError('Windows 主机不支持 chown')
        sftp.chown(_safe_path(path, windows=windows), int(uid), int(gid))
    finally:
        sftp.close()
        client.close()


def upload_init(host_id: int, dir_path: str, file_name: str, size: int, username: str) -> dict[str, Any]:
    import uuid

    from db import get_connection

    if not file_name:
        raise ValueError('文件名不能为空')
    if size < 0:
        raise ValueError('文件大小无效')

    client, sftp, windows = _open_sftp(host_id)
    try:
        parent = _safe_path(dir_path, windows=windows)
        target = _join_child(parent, os.path.basename(file_name), windows=windows)
        offset = 0
        try:
            attr = sftp.stat(target)
            existing = int(attr.st_size or 0)
            if existing > 0 and existing <= size:
                offset = existing
            else:
                # 尺寸不符，截断重传
                with sftp.file(target, 'wb') as f:
                    f.truncate(0)
                offset = 0
        except FileNotFoundError:
            with sftp.file(target, 'wb') as f:
                f.write(b'')
            offset = 0
    finally:
        sftp.close()
        client.close()

    token = uuid.uuid4().hex
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_sftp_upload (
                    token, host_id, username, remote_path, file_name,
                    total_size, offset_bytes, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
                """,
                (token, host_id, username or '', target, os.path.basename(file_name), size, offset),
            )
        conn.commit()
    finally:
        conn.close()

    return {
        'token': token,
        'path': target,
        'offset': offset,
        'size': size,
    }


def upload_status(token: str) -> dict[str, Any]:
    from db import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM linux_sftp_upload WHERE token = %s LIMIT 1',
                (token,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    if not row:
        raise ValueError('上传令牌无效')
    return {
        'token': row['token'],
        'path': row['remote_path'],
        'offset': int(row['offset_bytes'] or 0),
        'size': int(row['total_size'] or 0),
        'status': row['status'],
        'hostId': row['host_id'],
        'fileName': row['file_name'],
    }


def upload_chunk(token: str, offset: int, chunk: Optional[FileStorage]) -> dict[str, Any]:
    from db import get_connection

    if chunk is None:
        raise ValueError('缺少分片数据')
    meta = upload_status(token)
    if meta['status'] != 'active':
        raise ValueError('上传已结束')
    expected = int(meta['offset'])
    if int(offset) != expected:
        raise ValueError(f'偏移不匹配，期望 {expected}')

    data = chunk.read()
    if not data:
        raise ValueError('空分片')

    host_id = int(meta['hostId'])
    client, sftp, windows = _open_sftp(host_id)
    try:
        path = _safe_path(meta['path'], windows=windows)
        with sftp.file(path, 'ab') as f:
            f.write(data)
        new_offset = expected + len(data)
    finally:
        sftp.close()
        client.close()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE linux_sftp_upload
                SET offset_bytes = %s
                WHERE token = %s
                """,
                (new_offset, token),
            )
        conn.commit()
    finally:
        conn.close()

    return {'token': token, 'offset': new_offset, 'size': meta['size']}


def upload_complete(token: str) -> dict[str, Any]:
    from db import get_connection

    meta = upload_status(token)
    if int(meta['offset']) < int(meta['size']):
        raise ValueError(f"上传未完成：{meta['offset']}/{meta['size']}")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE linux_sftp_upload SET status = 'done' WHERE token = %s",
                (token,),
            )
        conn.commit()
    finally:
        conn.close()

    return {
        'name': meta['fileName'],
        'path': meta['path'],
        'size': meta['size'],
    }


def download_zip_stream(host_id: int, paths: list[str]):
    """生成 zip 字节流（先写临时文件再 yield，避免内存暴涨）。"""
    import tempfile
    import zipfile

    client, sftp, windows = _open_sftp(host_id)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    tmp_path = tmp.name
    tmp.close()

    def _add_file(zf: zipfile.ZipFile, remote: str, arcname: str) -> None:
        buf = BytesIO()
        sftp.getfo(remote, buf)
        zf.writestr(arcname, buf.getvalue())

    def _walk_dir(zf: zipfile.ZipFile, remote: str, arc_prefix: str) -> None:
        for attr in sftp.listdir_attr(remote):
            name = attr.filename
            if name in {'.', '..'}:
                continue
            child = _join_child(remote, name, windows=windows)
            arc = f'{arc_prefix}/{name}' if arc_prefix else name
            if stat.S_ISDIR(attr.st_mode):
                _walk_dir(zf, child, arc)
            else:
                _add_file(zf, child, arc)

    try:
        with zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for raw in paths:
                path = _safe_path(raw, windows=windows)
                base = os.path.basename(path.rstrip('/')) or 'root'
                try:
                    attr = sftp.stat(path)
                except FileNotFoundError:
                    continue
                if stat.S_ISDIR(attr.st_mode):
                    _walk_dir(zf, path, base)
                else:
                    _add_file(zf, path, base)
    finally:
        sftp.close()
        client.close()

    def generate():
        try:
            with open(tmp_path, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    name = 'download.zip'
    if len(paths) == 1:
        name = os.path.basename(paths[0].rstrip('/')) or 'download'
        if not name.endswith('.zip'):
            name = f'{name}.zip'
    return generate(), name


def search(
    host_id: int,
    path: str,
    keyword: str,
    *,
    recursive: bool = True,
    max_depth: int = 5,
) -> dict[str, Any]:
    keyword = (keyword or '').strip().lower()
    if not keyword:
        raise ValueError('请输入搜索关键词')
    max_depth = max(0, min(int(max_depth), 12))
    results: list[dict[str, Any]] = []
    limit = 300

    client, sftp, windows = _open_sftp(host_id)
    try:
        root = _safe_path(path or default_root(windows), windows=windows)

        def walk(cur: str, depth: int) -> None:
            if len(results) >= limit:
                return
            try:
                attrs = sftp.listdir_attr(cur)
            except Exception:
                return
            for attr in attrs:
                if len(results) >= limit:
                    return
                name = attr.filename
                if name in {'.', '..'}:
                    continue
                full = _join_child(cur, name, windows=windows)
                is_dir = stat.S_ISDIR(attr.st_mode)
                if keyword in name.lower():
                    ext = os.path.splitext(name)[1].lower()
                    results.append(
                        {
                            'name': name,
                            'path': full,
                            'isDir': is_dir,
                            'size': int(attr.st_size or 0),
                            'mtime': int(attr.st_mtime or 0),
                            'mode': oct(attr.st_mode & 0o777),
                            'ext': ext.lstrip('.'),
                            'parent': cur,
                        }
                    )
                if recursive and is_dir and depth < max_depth:
                    walk(full, depth + 1)

        walk(root, 0)
        return {
            'path': root,
            'keyword': keyword,
            'recursive': recursive,
            'maxDepth': max_depth,
            'truncated': len(results) >= limit,
            'list': results,
        }
    finally:
        sftp.close()
        client.close()
