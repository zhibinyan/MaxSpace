from typing import Any, Dict, List, Optional

from auth import normalize_password_md5
from db import get_connection

SUPER_ADMIN_DELETE_MSG = '超级管理员不可删除'


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'username': row['username'],
        'isSuper': bool(row['is_super']),
        'createdAt': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
        'updatedAt': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
    }


def list_admins() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, is_super, created_at, updated_at
                FROM admin
                ORDER BY is_super DESC, id ASC
                """
            )
            rows = cursor.fetchall()
    finally:
        conn.close()
    return [_serialize_row(row) for row in rows]


def get_admin_by_id(admin_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, is_super, created_at, updated_at
                FROM admin WHERE id = %s LIMIT 1
                """,
                (admin_id,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    return _serialize_row(row) if row else None


def create_admin(username: str, password_md5: str) -> Dict[str, Any]:
    username = username.strip()
    if not username:
        raise ValueError('用户名不能为空')
    if not password_md5:
        raise ValueError('密码不能为空')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM admin WHERE username = %s LIMIT 1', (username,))
            if cursor.fetchone():
                raise ValueError('用户名已存在')

            cursor.execute(
                'INSERT INTO admin (username, password, is_super) VALUES (%s, %s, 0)',
                (username, password_md5),
            )
            admin_id = cursor.lastrowid
    finally:
        conn.close()

    admin = get_admin_by_id(admin_id)
    if not admin:
        raise RuntimeError('创建管理员失败')
    return admin


def update_admin(
    admin_id: int,
    username: Optional[str] = None,
    password_md5: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, username, is_super FROM admin WHERE id = %s LIMIT 1',
                (admin_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError('管理员不存在')

            next_username = row['username']
            if username is not None:
                next_username = username.strip()
                if not next_username:
                    raise ValueError('用户名不能为空')
                if next_username != row['username']:
                    cursor.execute(
                        'SELECT id FROM admin WHERE username = %s AND id <> %s LIMIT 1',
                        (next_username, admin_id),
                    )
                    if cursor.fetchone():
                        raise ValueError('用户名已存在')

            fields = ['username = %s']
            values: List[Any] = [next_username]

            if password_md5:
                fields.append('password = %s')
                values.append(password_md5)

            values.append(admin_id)
            cursor.execute(
                f"UPDATE admin SET {', '.join(fields)} WHERE id = %s",
                values,
            )
    finally:
        conn.close()

    admin = get_admin_by_id(admin_id)
    if not admin:
        raise RuntimeError('更新管理员失败')
    return admin


def delete_admin(admin_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, is_super FROM admin WHERE id = %s LIMIT 1',
                (admin_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError('管理员不存在')
            if row['is_super']:
                raise ValueError(SUPER_ADMIN_DELETE_MSG)

            cursor.execute('DELETE FROM admin WHERE id = %s', (admin_id,))
    finally:
        conn.close()


def parse_password_md5(raw_password: str, required: bool = True) -> Optional[str]:
    password_md5 = normalize_password_md5(raw_password)
    if required and not password_md5:
        raise ValueError('密码不能为空')
    return password_md5
