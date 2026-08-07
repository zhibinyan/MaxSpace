import json
from typing import Any, Dict, List, Optional

from db import get_connection


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    process_data = None
    raw = row.get('process_data')
    if raw:
        try:
            process_data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            process_data = None

    return {
        'id': row['id'],
        'title': row['title'],
        'description': row['description'] or '',
        'processData': process_data,
        'createdAt': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
        'updatedAt': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
    }


def _encode_process_data(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def list_processes() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, description, process_data, created_at, updated_at
                FROM process
                ORDER BY updated_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()
    finally:
        conn.close()
    return [_serialize_row(row) for row in rows]


def get_process_by_id(process_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, description, process_data, created_at, updated_at
                FROM process
                WHERE id = %s
                LIMIT 1
                """,
                (process_id,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    return _serialize_row(row) if row else None


def _validate_payload(title: str) -> None:
    if not title.strip():
        raise ValueError('标题不能为空')


def create_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get('title', '')).strip()
    description = str(payload.get('description') or '').strip()
    _validate_payload(title)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO process (title, description, process_data)
                VALUES (%s, %s, %s)
                """,
                (
                    title,
                    description or None,
                    _encode_process_data(payload.get('processData')),
                ),
            )
            process_id = cursor.lastrowid
    finally:
        conn.close()

    process = get_process_by_id(process_id)
    if not process:
        raise RuntimeError('创建流程失败')
    return process


def update_process(process_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    current = get_process_by_id(process_id)
    if not current:
        raise ValueError('流程不存在')

    title = str(payload.get('title', current['title'])).strip()
    description = str(payload.get('description', current['description'])).strip()
    _validate_payload(title)

    process_data = payload.get('processData', current['processData'])

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE process
                SET title = %s, description = %s, process_data = %s
                WHERE id = %s
                """,
                (
                    title,
                    description or None,
                    _encode_process_data(process_data),
                    process_id,
                ),
            )
    finally:
        conn.close()

    process = get_process_by_id(process_id)
    if not process:
        raise RuntimeError('更新流程失败')
    return process


def delete_process(process_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM process WHERE id = %s LIMIT 1', (process_id,))
            if not cursor.fetchone():
                raise ValueError('流程不存在')
            cursor.execute('DELETE FROM process WHERE id = %s', (process_id,))
    finally:
        conn.close()
