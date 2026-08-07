"""SSH 侧栏 AI：自然语言 → Shell 命令（经 TokenHub 流式转发）+ 问答落库。"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Iterator

from config import AI_API_KEY, AI_API_URL, AI_MODEL
from db import get_connection

SYSTEM_PROMPT = (
    '你是 Linux / Shell 命令助手。用户用自然语言描述需求时，'
    '你只输出一条可直接在 bash 中执行的命令。\n'
    '规则：\n'
    '1. 只输出命令本身，不要解释、不要 markdown、不要代码块围栏\n'
    '2. 不要输出多余空行或前后缀说明\n'
    '3. 若需求含糊，输出最合理的一条命令'
)


def normalize_cmd(raw: str) -> str:
    text = (raw or '').strip()
    text = re.sub(r'^```(?:bash|sh|shell)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    text = re.sub(r'^命令[：:]\s*', '', text)
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def save_chat(username: str, prompt: str, answer: str) -> dict[str, Any]:
    user = (username or '').strip()
    q = (prompt or '').strip()
    a = normalize_cmd(answer) or (answer or '').strip()
    if not user or not q or not a:
        raise ValueError('问答内容不完整')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_ai_chat (username, prompt, answer)
                VALUES (%s, %s, %s)
                """,
                (user, q[:4000], a[:4000]),
            )
            chat_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return {
        'id': int(chat_id),
        'prompt': q,
        'answer': a,
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def list_chats(username: str, limit: int = 50) -> list[dict[str, Any]]:
    user = (username or '').strip()
    if not user:
        raise ValueError('未登录')
    lim = min(max(int(limit or 50), 1), 200)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, prompt, answer, created_at
                FROM linux_ai_chat
                WHERE username = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (user, lim),
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()

    def fmt(v: Any) -> str:
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d %H:%M:%S')
        return str(v or '')

    return [
        {
            'id': r['id'],
            'prompt': r['prompt'],
            'answer': r['answer'],
            'createdAt': fmt(r.get('created_at')),
        }
        for r in rows
    ]


def _extract_content_delta(line: bytes) -> str:
    """只取最终命令字段 content（忽略 reasoning_content 思考过程）。"""
    try:
        text = line.decode('utf-8', errors='ignore').strip()
    except Exception:
        return ''
    if not text.startswith('data:'):
        return ''
    data = text[5:].strip()
    if not data or data == '[DONE]':
        return ''
    try:
        payload = json.loads(data)
        delta = (payload.get('choices') or [{}])[0].get('delta') or {}
        content = delta.get('content')
        return str(content) if content else ''
    except (TypeError, ValueError, IndexError, AttributeError):
        return ''


def stream_command(prompt: str, username: str = '') -> Iterator[bytes]:
    """按行转发上游 SSE；落库只用 delta.content（不含 reasoning_content）。"""
    text = (prompt or '').strip()
    if not text:
        raise ValueError('请输入需求描述')
    if not AI_API_KEY:
        raise ValueError('未配置 AI_API_KEY，请在服务端环境变量中设置')

    body = json.dumps(
        {
            'model': AI_MODEL,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': text},
            ],
            'stream': True,
        },
        ensure_ascii=False,
    ).encode('utf-8')

    req = urllib.request.Request(
        AI_API_URL,
        data=body,
        method='POST',
        headers={
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
    )

    answer_parts: list[str] = []

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            while True:
                line = resp.readline()
                if not line:
                    break
                yield line
                delta = _extract_content_delta(line)
                if delta:
                    answer_parts.append(delta)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore')[:300]
        raise ValueError(f'AI 接口错误 {exc.code}：{detail or exc.reason}') from exc
    except urllib.error.URLError as exc:
        raise ValueError(f'AI 接口不可达：{exc.reason}') from exc
    finally:
        full = ''.join(answer_parts).strip()
        if username and full:
            try:
                save_chat(username, text, full)
            except Exception:
                pass
