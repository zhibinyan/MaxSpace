from typing import Any, Dict, List, Optional

from db import get_connection

SUPER_ADMIN_ONLY_MSG = '仅超级管理员可删除菜单'


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'parentId': row['parent_id'],
        'path': row['path'],
        'name': row['name'],
        'title': row['title'],
        'icon': row['icon'],
        'component': row['component'],
        'redirect': row['redirect'],
        'keepAlive': bool(row['keep_alive']),
        'dock': bool(row['dock']),
        'sortOrder': row['sort_order'],
        'createdAt': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
        'updatedAt': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
    }


def _fetch_all_rows() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, parent_id, path, name, title, icon, component, redirect,
                       keep_alive, dock, sort_order, created_at, updated_at
                FROM menu
                ORDER BY sort_order ASC, id ASC
                """
            )
            return cursor.fetchall()
    finally:
        conn.close()


def _build_tree(rows: List[Dict[str, Any]], parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
    tree: List[Dict[str, Any]] = []
    for row in rows:
        if row['parent_id'] == parent_id:
            item = _serialize_row(row)
            children = _build_tree(rows, row['id'])
            if children:
                item['children'] = children
            tree.append(item)
    return tree


def list_menu_tree() -> List[Dict[str, Any]]:
    return _build_tree(_fetch_all_rows())


def list_menus_flat() -> List[Dict[str, Any]]:
    return [_serialize_row(row) for row in _fetch_all_rows()]


def get_menu_by_id(menu_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, parent_id, path, name, title, icon, component, redirect,
                       keep_alive, dock, sort_order, created_at, updated_at
                FROM menu WHERE id = %s LIMIT 1
                """,
                (menu_id,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    return _serialize_row(row) if row else None


def _validate_menu_payload(
    path: str,
    title: str,
    parent_id: Optional[int],
    menu_id: Optional[int] = None,
) -> None:
    path = path.strip()
    title = title.strip()
    if not path:
        raise ValueError('路径不能为空')
    if not title:
        raise ValueError('标题不能为空')
    if parent_id is not None:
        parent = get_menu_by_id(parent_id)
        if not parent:
            raise ValueError('父级菜单不存在')
        if menu_id is not None and parent_id == menu_id:
            raise ValueError('不能将自己设为父级菜单')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM menu
                WHERE path = %s AND IFNULL(parent_id, 0) = IFNULL(%s, 0) AND id <> %s
                LIMIT 1
                """,
                (path, parent_id, menu_id or 0),
            )
            if cursor.fetchone():
                raise ValueError('同级路径已存在')
    finally:
        conn.close()


def create_menu(payload: Dict[str, Any]) -> Dict[str, Any]:
    parent_id = payload.get('parentId')
    path = str(payload.get('path', '')).strip()
    title = str(payload.get('title', '')).strip()
    _validate_menu_payload(path, title, parent_id)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO menu
                    (parent_id, path, name, title, icon, component, redirect, keep_alive, dock, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    parent_id,
                    path,
                    payload.get('name') or None,
                    title,
                    str(payload.get('icon') or 'Menu'),
                    payload.get('component') or None,
                    payload.get('redirect') or None,
                    1 if payload.get('keepAlive') else 0,
                    1 if payload.get('dock') else 0,
                    int(payload.get('sortOrder') or 0),
                ),
            )
            menu_id = cursor.lastrowid
    finally:
        conn.close()

    menu = get_menu_by_id(menu_id)
    if not menu:
        raise RuntimeError('创建菜单失败')
    return menu


def update_menu(menu_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    current = get_menu_by_id(menu_id)
    if not current:
        raise ValueError('菜单不存在')

    parent_id = payload.get('parentId', current['parentId'])
    path = str(payload.get('path', current['path'])).strip()
    title = str(payload.get('title', current['title'])).strip()
    _validate_menu_payload(path, title, parent_id, menu_id)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE menu SET
                    parent_id = %s,
                    path = %s,
                    name = %s,
                    title = %s,
                    icon = %s,
                    component = %s,
                    redirect = %s,
                    keep_alive = %s,
                    dock = %s,
                    sort_order = %s
                WHERE id = %s
                """,
                (
                    parent_id,
                    path,
                    payload.get('name', current['name']),
                    title,
                    str(payload.get('icon', current['icon'])),
                    payload.get('component', current['component']),
                    payload.get('redirect', current['redirect']),
                    1 if payload.get('keepAlive', current['keepAlive']) else 0,
                    1 if payload.get('dock', current['dock']) else 0,
                    int(payload.get('sortOrder', current['sortOrder'])),
                    menu_id,
                ),
            )
    finally:
        conn.close()

    menu = get_menu_by_id(menu_id)
    if not menu:
        raise RuntimeError('更新菜单失败')
    return menu


def delete_menu(menu_id: int) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM menu WHERE id = %s LIMIT 1', (menu_id,))
            if not cursor.fetchone():
                raise ValueError('菜单不存在')

            cursor.execute('SELECT id FROM menu WHERE parent_id = %s LIMIT 1', (menu_id,))
            if cursor.fetchone():
                raise ValueError('请先删除子菜单')

            cursor.execute('DELETE FROM menu WHERE id = %s', (menu_id,))
    finally:
        conn.close()


def is_super_admin(username: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT is_super FROM admin WHERE username = %s LIMIT 1',
                (username,),
            )
            row = cursor.fetchone()
    finally:
        conn.close()
    return bool(row and row['is_super'])
