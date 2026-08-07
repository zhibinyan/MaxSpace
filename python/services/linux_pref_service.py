"""Linux 用户偏好（终端主题 / 分屏比例等）。"""

from __future__ import annotations

import json
from typing import Any, Optional

from flask import g

from db import get_connection


def _user() -> Optional[str]:
    return getattr(g, 'current_user', None)


def get_pref(key: str, username: Optional[str] = None) -> Any:
    user = username or _user()
    if not user:
        raise ValueError('未登录')
    key = (key or '').strip()
    if not key:
        raise ValueError('pref_key 不能为空')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pref_json FROM linux_user_pref
                WHERE username = %s AND pref_key = %s
                LIMIT 1
                """,
                (user, key),
            )
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None
    try:
        return json.loads(row['pref_json'])
    except (TypeError, json.JSONDecodeError):
        return None


def set_pref(key: str, value: Any, username: Optional[str] = None) -> Any:
    user = username or _user()
    if not user:
        raise ValueError('未登录')
    key = (key or '').strip()
    if not key:
        raise ValueError('pref_key 不能为空')

    payload = json.dumps(value, ensure_ascii=False)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO linux_user_pref (username, pref_key, pref_json)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE pref_json = VALUES(pref_json)
                """,
                (user, key, payload),
            )
        conn.commit()
    finally:
        conn.close()
    return value
