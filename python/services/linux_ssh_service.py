"""Linux SSH WebSocket 会话桥接（含审计 / 录制 / 远端 tmux）。"""

from __future__ import annotations

import json
import re
import select
import threading
from typing import Any, Optional

import paramiko

from services import linux_session_service
from services.linux_host_service import get_host, get_host_credentials, is_windows_os, mark_connected

# 远端持久会话名前缀：刷新浏览器后重连可 attach 同一 tmux
TMUX_SESSION = 'maxspace'


def _sanitize_session_suffix(text: str) -> str:
    raw = re.sub(r'[^A-Za-z0-9_-]+', '-', (text or '').strip())[:24].strip('-')
    return raw or 'default'


def open_shell(
    host_id: int,
    cols: int = 120,
    rows: int = 36,
    *,
    app_username: Optional[str] = None,
) -> tuple[paramiko.SSHClient, Any, bool]:
    """打开远端 shell。Linux 优先进入 tmux；返回 (client, channel, used_tmux)。"""
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

    if windows:
        channel = client.invoke_shell(term='xterm-256color', width=cols, height=rows)
        channel.settimeout(0.0)
        mark_connected(host_id, 'online')
        return client, channel, False

    # 按平台登录用户隔离会话名；开启 mouse，滚轮由 tmux 滚历史而非变成 shell ↑↓
    remote_user = str(cred.get('username') or 'user')
    suffix = _sanitize_session_suffix(f'{remote_user}-{app_username or "anon"}')
    session_name = f'{TMUX_SESSION}-{suffix}'
    boot = (
        'if command -v tmux >/dev/null 2>&1; then '
        f'tmux new-session -d -s {session_name} 2>/dev/null || true; '
        f'tmux set -t {session_name} -g mouse on; '
        f'tmux set -t {session_name} -g history-limit 50000; '
        f'exec tmux attach-session -t {session_name}; '
        'else '
        'exec "${SHELL:-/bin/bash}" -l; '
        'fi'
    )

    transport = client.get_transport()
    if transport is None:
        raise RuntimeError('SSH transport 不可用')
    channel = transport.open_session()
    channel.get_pty(term='xterm-256color', width=cols, height=rows)
    channel.exec_command(boot)
    channel.settimeout(0.0)
    mark_connected(host_id, 'online')
    return client, channel, True


def bridge_websocket(ws, host_id: int, username: Optional[str] = None) -> None:
    """阻塞：将 WebSocket 与 SSH channel 双向桥接，直到断开。"""
    client = None
    channel = None
    stop = threading.Event()
    session_id = 0
    recording = False
    user = username or 'unknown'
    used_tmux = False

    try:
        host_meta = get_host(host_id) or {}
        session_id = linux_session_service.create_session(
            host_id,
            user,
            host_title=str(host_meta.get('name') or ''),
            host_addr=str(host_meta.get('host') or ''),
            host_user=str(host_meta.get('username') or ''),
            host_port=int(host_meta.get('port') or 22),
        )
        client, channel, used_tmux = open_shell(host_id, app_username=user)
        ws.send(
            json.dumps(
                {
                    'type': 'ready',
                    'hostId': host_id,
                    'sessionId': session_id,
                    'tmux': used_tmux,
                }
            )
        )

        def pump_ssh_to_ws() -> None:
            nonlocal recording
            while not stop.is_set():
                try:
                    if channel is None or channel.closed:
                        break
                    readable, _, _ = select.select([channel], [], [], 0.2)
                    if not readable:
                        continue
                    data = channel.recv(4096)
                    if not data:
                        break
                    if recording and session_id:
                        try:
                            linux_session_service.append_recording(session_id, data)
                        except Exception:
                            pass
                    ws.send(data)
                except Exception:
                    break
            stop.set()
            try:
                ws.close()
            except Exception:
                pass

        thread = threading.Thread(target=pump_ssh_to_ws, daemon=True)
        thread.start()

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
                msg_type = payload.get('type')
                if msg_type == 'resize':
                    cols = int(payload.get('cols') or 120)
                    rows = int(payload.get('rows') or 36)
                    channel.resize_pty(width=cols, height=rows)
                    continue
                if msg_type == 'ping':
                    ws.send(json.dumps({'type': 'pong'}))
                    continue
                if msg_type == 'command':
                    linux_session_service.log_command(
                        session_id,
                        host_id,
                        user,
                        str(payload.get('text') or ''),
                    )
                    continue
                if msg_type == 'record':
                    recording = bool(payload.get('on'))
                    ws.send(json.dumps({'type': 'record', 'on': recording, 'sessionId': session_id}))
                    continue
            channel.send(text.encode('utf-8'))
    except Exception as exc:  # noqa: BLE001
        try:
            ws.send(json.dumps({'type': 'error', 'message': str(exc)}))
        except Exception:
            pass
        # 会话异常不等于主机离线，仅结束会话记录
        if session_id:
            linux_session_service.end_session(session_id, 'error')
            session_id = 0
    finally:
        stop.set()
        if session_id:
            linux_session_service.end_session(session_id, 'closed')
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
        # 注意：关闭终端/刷新页面不应把主机标为 offline（机器仍可能在线）
