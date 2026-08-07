"""SSH 会话、命令审计、录制读写。"""

from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Any, Optional

from flask import g

from db import get_connection

RECORDING_MAX_BYTES = 5 * 1024 * 1024


def _user() -> Optional[str]:
    return getattr(g, 'current_user', None)


def _fmt_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def _row_session(row: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': row['id'],
        'hostId': row['host_id'],
        'username': row['username'],
        'hostTitle': row.get('host_title') or '',
        'host': row.get('host_addr') or '',
        'hostUser': row.get('host_user') or '',
        'port': row.get('host_port') or 22,
        'status': row['status'],
        'hasRecording': bool(row.get('has_recording')),
        'recordingBytes': int(row.get('recording_bytes') or 0),
        'layoutSnapshot': row.get('layout_snapshot'),
        'startedAt': _fmt_dt(row.get('started_at')),
        'endedAt': _fmt_dt(row.get('ended_at')),
    }


def create_session(
    host_id: int,
    username: str,
    *,
    host_title: str = '',
    host_addr: str = '',
    host_user: str = '',
    host_port: int = 22,
) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_ssh_session (
                    host_id, username, host_title, host_addr, host_user, host_port,
                    status, started_at
                ) VALUES (%s, %s, %s, %s, %s, %s, 'online', NOW())
                """,
                (host_id, username, host_title, host_addr, host_user, host_port),
            )
            session_id = int(cursor.lastrowid)
        conn.commit()
        return session_id
    finally:
        conn.close()


def end_session(session_id: int, status: str = 'closed') -> None:
    if not session_id:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE linux_ssh_session
                SET status = %s, ended_at = NOW()
                WHERE id = %s
                """,
                (status, session_id),
            )
        conn.commit()
    finally:
        conn.close()


def _is_usable_shell_cmd(command: str) -> bool:
    """过滤终端协议泄漏 / 误贴输出，避免写入审计命令表。"""
    text = (command or '').strip()
    if not text:
        return False
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', text):
        return False
    # CSI / DA（带 [）：[A、[>0;276;0c、[?1;2c
    if re.match(r'^\[[?>!=]?[\d;]*[A-Za-z~@`]', text):
        return False
    if text.startswith('[<') or text.startswith('[M'):
        return False
    # DA 丢 ESC/[：>0;276;0c...
    if re.match(r'^>[0-9;]+[A-Za-z]', text):
        return False
    # 鼠标报告（有无 [）：[<64;33;36M 或 <65;48;17M
    if re.search(r'\[?<\d+;\d+;\d+[Mm]', text):
        return False
    # bracketed paste 残留：200~ ... 201~
    if '200~' in text or '201~' in text:
        return False
    # SS3 方向键残留：OA/OB/OC/OD（单独或作前缀）
    if re.match(r'^(?:O[A-D])+', text):
        return False
    # docker ps 等输出误贴进命令
    if re.match(r'^[0-9a-f]{12}\s+\S+', text):
        return False
    if not re.search(r'[A-Za-z0-9_./~$*-]', text):
        return False
    return True


def log_command(session_id: int, host_id: int, username: str, command: str) -> None:
    text = (command or '').strip()
    if not text or not session_id:
        return
    if not _is_usable_shell_cmd(text):
        return
    if len(text) > 4000:
        text = text[:4000]
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_ssh_cmd_log (session_id, host_id, username, command)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, host_id, username, text),
            )
        conn.commit()
    finally:
        conn.close()


def append_recording(session_id: int, data: bytes) -> bool:
    """追加录制块。超过上限返回 False。"""
    if not session_id or not data:
        return True
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT recording_bytes FROM linux_ssh_session WHERE id = %s LIMIT 1',
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False
            used = int(row['recording_bytes'] or 0)
            if used >= RECORDING_MAX_BYTES:
                return False
            chunk = data
            if used + len(chunk) > RECORDING_MAX_BYTES:
                chunk = chunk[: max(0, RECORDING_MAX_BYTES - used)]
            if not chunk:
                return False
            cursor.execute(
                'SELECT COALESCE(MAX(seq), 0) AS mx FROM linux_ssh_recording WHERE session_id = %s',
                (session_id,),
            )
            seq = int((cursor.fetchone() or {}).get('mx') or 0) + 1
            cursor.execute(
                """
                INSERT INTO linux_ssh_recording (session_id, seq, payload)
                VALUES (%s, %s, %s)
                """,
                (session_id, seq, chunk),
            )
            cursor.execute(
                """
                UPDATE linux_ssh_session
                SET has_recording = 1, recording_bytes = recording_bytes + %s
                WHERE id = %s
                """,
                (len(chunk), session_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def list_user_recent(username: Optional[str] = None, limit: int = 30) -> list[dict[str, Any]]:
    user = username or _user()
    if not user:
        raise ValueError('未登录')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.*
                FROM linux_ssh_session s
                INNER JOIN (
                    SELECT host_id, MAX(id) AS max_id
                    FROM linux_ssh_session
                    WHERE username = %s
                    GROUP BY host_id
                ) t ON s.id = t.max_id
                ORDER BY s.started_at DESC
                LIMIT %s
                """,
                (user, limit),
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()
    return [
        {
            'hostId': r['host_id'],
            'title': r.get('host_title') or '',
            'host': r.get('host_addr') or '',
            'username': r.get('host_user') or '',
            'port': r.get('host_port') or 22,
            'lastAt': _fmt_dt(r.get('started_at')) or '',
            'sessionId': r['id'],
        }
        for r in rows
    ]


def list_user_history(username: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    user = username or _user()
    if not user:
        raise ValueError('未登录')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM linux_ssh_session
                WHERE username = %s
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (user, limit),
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()
    return [
        {
            'hostId': r['host_id'],
            'title': r.get('host_title') or '',
            'host': r.get('host_addr') or '',
            'username': r.get('host_user') or '',
            'port': r.get('host_port') or 22,
            'lastAt': _fmt_dt(r.get('started_at')) or '',
            'sessionId': r['id'],
            'status': r['status'],
            'hasRecording': bool(r.get('has_recording')),
        }
        for r in rows
    ]


def list_audit_sessions(
    *,
    host_id: Optional[int] = None,
    username: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ['1=1']
    args: list[Any] = []
    if host_id:
        clauses.append('host_id = %s')
        args.append(host_id)
    if username:
        clauses.append('username = %s')
        args.append(username)
    if date_from:
        clauses.append('started_at >= %s')
        args.append(date_from)
    if date_to:
        clauses.append('started_at <= %s')
        args.append(date_to + ' 23:59:59' if len(date_to) <= 10 else date_to)
    args.append(min(max(limit, 1), 500))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM linux_ssh_session
                WHERE {' AND '.join(clauses)}
                ORDER BY started_at DESC
                LIMIT %s
                """,
                tuple(args),
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()
    return [_row_session(r) for r in rows]


def list_audit_commands(
    *,
    session_id: Optional[int] = None,
    host_id: Optional[int] = None,
    username: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    clauses = ['1=1']
    args: list[Any] = []
    if session_id:
        clauses.append('session_id = %s')
        args.append(session_id)
    if host_id:
        clauses.append('host_id = %s')
        args.append(host_id)
    if username:
        clauses.append('username = %s')
        args.append(username)
    if date_from:
        clauses.append('created_at >= %s')
        args.append(date_from)
    if date_to:
        clauses.append('created_at <= %s')
        args.append(date_to + ' 23:59:59' if len(date_to) <= 10 else date_to)
    if keyword:
        clauses.append('command LIKE %s')
        args.append(f'%{keyword}%')
    args.append(min(max(limit, 1), 1000))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM linux_ssh_cmd_log
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC
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
            'sessionId': r['session_id'],
            'hostId': r['host_id'],
            'username': r['username'],
            'command': r['command'],
            'createdAt': _fmt_dt(r.get('created_at')),
        }
        for r in rows
    ]


def register_open(
    host_id: int,
    username: Optional[str] = None,
    *,
    host_title: str = '',
    host_addr: str = '',
    host_user: str = '',
    host_port: int = 22,
) -> dict[str, Any]:
    """前端打开主机时登记一条历史（WS 连接会再建在线会话）。"""
    user = username or _user()
    if not user:
        raise ValueError('未登录')
    sid = create_session(
        host_id,
        user,
        host_title=host_title,
        host_addr=host_addr,
        host_user=host_user,
        host_port=host_port,
    )
    end_session(sid, 'opened')
    return {
        'sessionId': sid,
        'hostId': host_id,
        'title': host_title,
        'host': host_addr,
        'username': host_user,
        'port': host_port,
    }


def get_recording(session_id: int) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM linux_ssh_session WHERE id = %s LIMIT 1',
                (session_id,),
            )
            sess = cursor.fetchone()
            if not sess:
                raise ValueError('会话不存在')
            cursor.execute(
                """
                SELECT seq, payload FROM linux_ssh_recording
                WHERE session_id = %s
                ORDER BY seq ASC
                """,
                (session_id,),
            )
            chunks = cursor.fetchall() or []
    finally:
        conn.close()

    pieces = []
    for c in chunks:
        raw = c['payload']
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if isinstance(raw, str):
            raw = raw.encode('latin1')
        pieces.append(base64.b64encode(raw).decode('ascii'))

    return {
        'session': _row_session(sess),
        'chunks': pieces,
        'encoding': 'base64',
    }
