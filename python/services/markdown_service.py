from typing import Any, Dict, List, Optional

from db import get_connection


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'title': row['title'],
        'content': row['content'] or '',
        'createdAt': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
        'updatedAt': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
    }


def list_markdowns() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM markdown
                ORDER BY updated_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()
    finally:
        conn.close()
    return [_serialize_row(row) for row in rows]


def get_markdown_by_id(markdown_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM markdown
                WHERE id = %s
                LIMIT 1
                """,
                (markdown_id,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    return _serialize_row(row) if row else None


def _validate_payload(title: str) -> None:
    if not title.strip():
        raise ValueError('标题不能为空')


def create_markdown(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get('title', '')).strip()
    content = str(payload.get('content') or '')
    _validate_payload(title)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO markdown (title, content)
                VALUES (%s, %s)
                """,
                (title, content or None),
            )
            markdown_id = cursor.lastrowid
    finally:
        conn.close()

    item = get_markdown_by_id(markdown_id)
    if not item:
        raise RuntimeError('创建备忘录失败')
    return item


def update_markdown(markdown_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    current = get_markdown_by_id(markdown_id)
    if not current:
        raise ValueError('备忘录不存在')

    title = str(payload.get('title', current['title'])).strip()
    content = str(payload.get('content', current['content']))
    _validate_payload(title)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE markdown
                SET title = %s, content = %s
                WHERE id = %s
                """,
                (title, content or None, markdown_id),
            )
    finally:
        conn.close()

    item = get_markdown_by_id(markdown_id)
    if not item:
        raise RuntimeError('更新备忘录失败')
    return item


def delete_markdown(markdown_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM markdown WHERE id = %s LIMIT 1', (markdown_id,))
            if not cursor.fetchone():
                raise ValueError('备忘录不存在')
            cursor.execute('DELETE FROM markdown WHERE id = %s', (markdown_id,))
    finally:
        conn.close()
