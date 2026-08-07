"""Linux 主机 / 分组 / 标签服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import paramiko
from flask import g

from db import get_connection
from utils.crypto_util import decrypt_text, encrypt_text


def _user() -> Optional[str]:
    return getattr(g, 'current_user', None)


def _fmt_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


# ─── 分组 ─────────────────────────────────────────────


def list_groups() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT g.*, (
                    SELECT COUNT(*) FROM linux_host h WHERE h.group_id = g.id
                ) AS host_count
                FROM linux_host_group g
                ORDER BY g.sort_order ASC, g.id ASC
                """
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()

    nodes = {
        row['id']: {
            'id': row['id'],
            'parentId': row['parent_id'],
            'name': row['name'],
            'sortOrder': row['sort_order'],
            'hostCount': int(row['host_count'] or 0),
            'children': [],
        }
        for row in rows
    }
    roots: list[dict[str, Any]] = []
    for node in nodes.values():
        pid = node['parentId']
        if pid and pid in nodes:
            nodes[pid]['children'].append(node)
        else:
            roots.append(node)
    return roots


def create_group(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get('name') or '').strip()
    if not name:
        raise ValueError('分组名称不能为空')
    parent_id = data.get('parentId')
    sort_order = int(data.get('sortOrder') or 0)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if parent_id is not None:
                cursor.execute('SELECT id FROM linux_host_group WHERE id = %s', (parent_id,))
                if not cursor.fetchone():
                    raise ValueError('父分组不存在')
            cursor.execute(
                """
                INSERT INTO linux_host_group (parent_id, name, sort_order)
                VALUES (%s, %s, %s)
                """,
                (parent_id, name, sort_order),
            )
            new_id = cursor.lastrowid
    finally:
        conn.close()
    return {'id': new_id, 'parentId': parent_id, 'name': name, 'sortOrder': sort_order, 'hostCount': 0, 'children': []}


def update_group(group_id: int, data: dict[str, Any]) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_host_group WHERE id = %s', (group_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError('分组不存在')
            name = str(data.get('name') if data.get('name') is not None else row['name']).strip()
            if not name:
                raise ValueError('分组名称不能为空')
            parent_id = data.get('parentId', row['parent_id'])
            if parent_id == group_id:
                raise ValueError('不能将分组设为自身子级')
            sort_order = int(data.get('sortOrder') if data.get('sortOrder') is not None else row['sort_order'])
            cursor.execute(
                """
                UPDATE linux_host_group
                SET parent_id = %s, name = %s, sort_order = %s
                WHERE id = %s
                """,
                (parent_id, name, sort_order, group_id),
            )
    finally:
        conn.close()
    return {'id': group_id, 'parentId': parent_id, 'name': name, 'sortOrder': sort_order}


def delete_group(group_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM linux_host_group WHERE parent_id = %s LIMIT 1', (group_id,))
            if cursor.fetchone():
                raise ValueError('请先删除子分组')
            cursor.execute('SELECT id FROM linux_host WHERE group_id = %s LIMIT 1', (group_id,))
            if cursor.fetchone():
                raise ValueError('分组下仍有主机，无法删除')
            cursor.execute('DELETE FROM linux_host_group WHERE id = %s', (group_id,))
            if cursor.rowcount == 0:
                raise ValueError('分组不存在')
    finally:
        conn.close()


# ─── 标签 ─────────────────────────────────────────────


def list_tags() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_tag ORDER BY id ASC')
            rows = cursor.fetchall() or []
    finally:
        conn.close()
    return [{'id': r['id'], 'name': r['name'], 'color': r.get('color')} for r in rows]


def create_tag(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get('name') or '').strip()
    if not name:
        raise ValueError('标签名称不能为空')
    color = data.get('color')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM linux_tag WHERE name = %s', (name,))
            if cursor.fetchone():
                raise ValueError('标签已存在')
            cursor.execute(
                'INSERT INTO linux_tag (name, color) VALUES (%s, %s)',
                (name, color),
            )
            new_id = cursor.lastrowid
    finally:
        conn.close()
    return {'id': new_id, 'name': name, 'color': color}


def update_tag(tag_id: int, data: dict[str, Any]) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_tag WHERE id = %s', (tag_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError('标签不存在')
            name = str(data.get('name') if data.get('name') is not None else row['name']).strip()
            color = data.get('color', row.get('color'))
            cursor.execute(
                'UPDATE linux_tag SET name = %s, color = %s WHERE id = %s',
                (name, color, tag_id),
            )
    finally:
        conn.close()
    return {'id': tag_id, 'name': name, 'color': color}


def delete_tag(tag_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM linux_host_tag WHERE tag_id = %s', (tag_id,))
            cursor.execute('DELETE FROM linux_tag WHERE id = %s', (tag_id,))
            if cursor.rowcount == 0:
                raise ValueError('标签不存在')
    finally:
        conn.close()


# ─── 主机 ─────────────────────────────────────────────


def _load_tags(cursor, host_id: int) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT t.id, t.name, t.color
        FROM linux_tag t
        INNER JOIN linux_host_tag ht ON ht.tag_id = t.id
        WHERE ht.host_id = %s
        ORDER BY t.id
        """,
        (host_id,),
    )
    return [{'id': r['id'], 'name': r['name'], 'color': r.get('color')} for r in (cursor.fetchall() or [])]


def _serialize_host(row: dict[str, Any], tags: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        'id': row['id'],
        'name': row['name'],
        'host': row['host'],
        'port': row['port'],
        'username': row['username'],
        'authType': row['auth_type'],
        'hasPassword': bool(row.get('password_enc')),
        'hasPrivateKey': bool(row.get('private_key_enc')),
        'groupId': row.get('group_id'),
        'osName': row.get('os_name') or '',
        'envType': row.get('env_type') or '',
        'owner': row.get('owner') or '',
        'remark': row.get('remark') or '',
        'isFavorite': bool(row.get('is_favorite')),
        'status': row.get('status') or 'unknown',
        'lastConnectedAt': _fmt_dt(row.get('last_connected_at')),
        'createdBy': row.get('created_by'),
        'updatedBy': row.get('updated_by'),
        'createdAt': _fmt_dt(row.get('created_at')),
        'updatedAt': _fmt_dt(row.get('updated_at')),
        'tags': tags or [],
    }


def list_hosts(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    sql = 'SELECT * FROM linux_host WHERE 1=1'
    params: list[Any] = []

    keyword = str(filters.get('keyword') or '').strip()
    if keyword:
        sql += ' AND (name LIKE %s OR host LIKE %s OR remark LIKE %s OR owner LIKE %s)'
        like = f'%{keyword}%'
        params.extend([like, like, like, like])

    group_id = filters.get('groupId')
    if group_id not in (None, '', 'null'):
        sql += ' AND group_id = %s'
        params.append(int(group_id))

    env_type = str(filters.get('envType') or '').strip()
    if env_type:
        sql += ' AND env_type = %s'
        params.append(env_type)

    status = str(filters.get('status') or '').strip()
    if status:
        sql += ' AND status = %s'
        params.append(status)

    favorite = filters.get('favorite')
    if favorite in ('1', 'true', True, 1):
        sql += ' AND is_favorite = 1'

    tag_id = filters.get('tagId')
    if tag_id not in (None, '', 'null'):
        sql += ' AND id IN (SELECT host_id FROM linux_host_tag WHERE tag_id = %s)'
        params.append(int(tag_id))

    sql += ' ORDER BY is_favorite DESC, updated_at DESC, id DESC'

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall() or []
            result = []
            for row in rows:
                result.append(_serialize_host(row, _load_tags(cursor, row['id'])))
            return result
    finally:
        conn.close()


def get_host(host_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_host WHERE id = %s', (host_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return _serialize_host(row, _load_tags(cursor, host_id))
    finally:
        conn.close()


def get_host_credentials(host_id: int) -> dict[str, Any]:
    """内部使用：返回含明文凭证的连接信息。"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_host WHERE id = %s', (host_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError('主机不存在')
            return {
                'id': row['id'],
                'name': row['name'],
                'host': row['host'],
                'port': int(row['port'] or 22),
                'username': row['username'],
                'authType': row['auth_type'] or 'password',
                'password': decrypt_text(row.get('password_enc')),
                'privateKey': decrypt_text(row.get('private_key_enc')),
                'osName': row.get('os_name') or '',
            }
    finally:
        conn.close()


def is_windows_os(os_name: str | None) -> bool:
    return 'windows' in (os_name or '').strip().lower()


def _sync_tags(cursor, host_id: int, tag_ids: list[int] | None) -> None:
    cursor.execute('DELETE FROM linux_host_tag WHERE host_id = %s', (host_id,))
    if not tag_ids:
        return
    for tid in tag_ids:
        cursor.execute(
            'INSERT IGNORE INTO linux_host_tag (host_id, tag_id) VALUES (%s, %s)',
            (host_id, int(tid)),
        )


def create_host(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get('name') or '').strip()
    host = str(data.get('host') or '').strip()
    username = str(data.get('username') or '').strip()
    if not name or not host or not username:
        raise ValueError('名称、主机地址、用户名不能为空')

    port = int(data.get('port') or 22)
    auth_type = str(data.get('authType') or 'password').strip() or 'password'
    password = data.get('password')
    private_key = data.get('privateKey')
    if auth_type == 'password' and not password:
        raise ValueError('请填写登录密码')
    if auth_type == 'key' and not private_key:
        raise ValueError('请填写私钥')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_host (
                    name, host, port, username, auth_type, password_enc, private_key_enc,
                    group_id, os_name, env_type, owner, remark, is_favorite, status,
                    created_by, updated_by
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'unknown',%s,%s)
                """,
                (
                    name,
                    host,
                    port,
                    username,
                    auth_type,
                    encrypt_text(password) if password else None,
                    encrypt_text(private_key) if private_key else None,
                    data.get('groupId'),
                    str(data.get('osName') or '').strip() or None,
                    str(data.get('envType') or '').strip() or None,
                    str(data.get('owner') or '').strip() or None,
                    str(data.get('remark') or '').strip() or None,
                    1 if data.get('isFavorite') else 0,
                    _user(),
                    _user(),
                ),
            )
            new_id = cursor.lastrowid
            _sync_tags(cursor, new_id, data.get('tagIds') or [])
            cursor.execute('SELECT * FROM linux_host WHERE id = %s', (new_id,))
            row = cursor.fetchone()
            return _serialize_host(row, _load_tags(cursor, new_id))
    finally:
        conn.close()


def update_host(host_id: int, data: dict[str, Any]) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM linux_host WHERE id = %s', (host_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError('主机不存在')

            name = str(data.get('name') if data.get('name') is not None else row['name']).strip()
            host = str(data.get('host') if data.get('host') is not None else row['host']).strip()
            username = str(
                data.get('username') if data.get('username') is not None else row['username']
            ).strip()
            if not name or not host or not username:
                raise ValueError('名称、主机地址、用户名不能为空')

            port = int(data.get('port') if data.get('port') is not None else row['port'])
            auth_type = str(
                data.get('authType') if data.get('authType') is not None else row['auth_type']
            ).strip()

            password_enc = row.get('password_enc')
            private_key_enc = row.get('private_key_enc')
            if 'password' in data and data.get('password'):
                password_enc = encrypt_text(str(data['password']))
            if 'privateKey' in data and data.get('privateKey'):
                private_key_enc = encrypt_text(str(data['privateKey']))

            cursor.execute(
                """
                UPDATE linux_host SET
                    name=%s, host=%s, port=%s, username=%s, auth_type=%s,
                    password_enc=%s, private_key_enc=%s, group_id=%s,
                    os_name=%s, env_type=%s, owner=%s, remark=%s,
                    is_favorite=%s, updated_by=%s
                WHERE id=%s
                """,
                (
                    name,
                    host,
                    port,
                    username,
                    auth_type,
                    password_enc,
                    private_key_enc,
                    data.get('groupId', row.get('group_id')),
                    str(data.get('osName') if data.get('osName') is not None else (row.get('os_name') or '')).strip()
                    or None,
                    str(data.get('envType') if data.get('envType') is not None else (row.get('env_type') or '')).strip()
                    or None,
                    str(data.get('owner') if data.get('owner') is not None else (row.get('owner') or '')).strip()
                    or None,
                    str(data.get('remark') if data.get('remark') is not None else (row.get('remark') or '')).strip()
                    or None,
                    1
                    if (
                        data.get('isFavorite')
                        if data.get('isFavorite') is not None
                        else row.get('is_favorite')
                    )
                    else 0,
                    _user(),
                    host_id,
                ),
            )
            if 'tagIds' in data:
                _sync_tags(cursor, host_id, data.get('tagIds') or [])
            cursor.execute('SELECT * FROM linux_host WHERE id = %s', (host_id,))
            updated = cursor.fetchone()
            return _serialize_host(updated, _load_tags(cursor, host_id))
    finally:
        conn.close()


def delete_host(host_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM linux_host_tag WHERE host_id = %s', (host_id,))
            cursor.execute('DELETE FROM linux_host WHERE id = %s', (host_id,))
            if cursor.rowcount == 0:
                raise ValueError('主机不存在')
    finally:
        conn.close()


def batch_hosts(action: str, ids: list[int], payload: dict[str, Any] | None = None) -> int:
    if not ids:
        raise ValueError('请选择主机')
    payload = payload or {}
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if action == 'delete':
                cursor.execute(
                    f"DELETE FROM linux_host_tag WHERE host_id IN ({','.join(['%s'] * len(ids))})",
                    ids,
                )
                cursor.execute(
                    f"DELETE FROM linux_host WHERE id IN ({','.join(['%s'] * len(ids))})",
                    ids,
                )
                return cursor.rowcount
            if action == 'favorite':
                cursor.execute(
                    f"UPDATE linux_host SET is_favorite = 1 WHERE id IN ({','.join(['%s'] * len(ids))})",
                    ids,
                )
                return cursor.rowcount
            if action == 'unfavorite':
                cursor.execute(
                    f"UPDATE linux_host SET is_favorite = 0 WHERE id IN ({','.join(['%s'] * len(ids))})",
                    ids,
                )
                return cursor.rowcount
            if action == 'moveGroup':
                group_id = payload.get('groupId')
                cursor.execute(
                    f"UPDATE linux_host SET group_id = %s WHERE id IN ({','.join(['%s'] * len(ids))})",
                    [group_id, *ids],
                )
                return cursor.rowcount
            if action == 'setTags':
                tag_ids = payload.get('tagIds') or []
                for hid in ids:
                    _sync_tags(cursor, int(hid), tag_ids)
                return len(ids)
            raise ValueError('不支持的批量操作')
    finally:
        conn.close()


def mark_connected(host_id: int, status: str = 'online') -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE linux_host
                SET status = %s, last_connected_at = NOW()
                WHERE id = %s
                """,
                (status, host_id),
            )
    finally:
        conn.close()


def test_connection(host_id: int) -> dict[str, Any]:
    cred = get_host_credentials(host_id)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connect_kwargs: dict[str, Any] = {
            'hostname': cred['host'],
            'port': cred['port'],
            'username': cred['username'],
            'timeout': 12,
            'allow_agent': False,
            'look_for_keys': False,
        }
        if cred['authType'] == 'key' and cred.get('privateKey'):
            from io import StringIO

            try:
                connect_kwargs['pkey'] = paramiko.RSAKey.from_private_key(StringIO(cred['privateKey']))
            except Exception:
                connect_kwargs['pkey'] = paramiko.Ed25519Key.from_private_key(
                    StringIO(cred['privateKey'])
                )
        else:
            connect_kwargs['password'] = cred.get('password') or ''

        client.connect(**connect_kwargs)

        windows = is_windows_os(cred.get('osName'))
        probe_cmd = 'ver' if windows else 'uname -a'
        stdin, stdout, stderr = client.exec_command(probe_cmd, timeout=8)
        output = (stdout.read() or b'').decode('utf-8', errors='ignore').strip()
        err = (stderr.read() or b'').decode('utf-8', errors='ignore').strip()
        # Windows 某些环境下 ver 走 cmd，stdout 可能为空但连接已成功
        if not output and windows:
            output = err or 'Windows OpenSSH 已连通'
        mark_connected(host_id, 'online')
        return {
            'ok': True,
            'message': '连接成功',
            'uname': output,
            'osName': cred.get('osName') or '',
        }
    except Exception as exc:  # noqa: BLE001
        mark_connected(host_id, 'offline')
        raise ValueError(f'连接失败：{exc}') from exc
    finally:
        client.close()
