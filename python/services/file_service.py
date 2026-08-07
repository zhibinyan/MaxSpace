from __future__ import annotations

import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from flask import g
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import FILE_MAX_BYTES, FILE_UPLOAD_DIR
from db import get_connection

INSTALL_EXTS = {
    'exe', 'msi', 'apk', 'ipa', 'dmg', 'pkg', 'deb', 'rpm', 'iso',
}
IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'}
VIDEO_EXTS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
AUDIO_EXTS = {'mp3', 'wav', 'aac', 'flac'}
DOC_EXTS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'markdown'}
CODE_EXTS = {
    'vue', 'js', 'jsx', 'ts', 'tsx', 'java', 'py', 'go', 'php', 'c', 'cpp', 'h',
    'html', 'css', 'scss', 'json', 'xml', 'yaml', 'yml', 'sql', 'sh', 'rs', 'kt',
}
ARCHIVE_EXTS = {'zip', 'rar', '7z', 'tar', 'gz', 'tgz'}
OFFICE_EXTS = {'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}


def ensure_upload_root() -> Path:
    root = Path(FILE_UPLOAD_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def guess_category(ext: str, is_folder: bool) -> str:
    if is_folder:
        return 'folder'
    e = (ext or '').lower().lstrip('.')
    if e in IMAGE_EXTS:
        return 'image'
    if e in VIDEO_EXTS:
        return 'video'
    if e in AUDIO_EXTS:
        return 'audio'
    if e == 'pdf':
        return 'pdf'
    if e in {'md', 'markdown'}:
        return 'markdown'
    if e in OFFICE_EXTS:
        return 'office'
    if e in CODE_EXTS:
        return 'code'
    if e in ARCHIVE_EXTS:
        return 'archive'
    if e in INSTALL_EXTS:
        return 'install'
    if e in DOC_EXTS:
        return 'document'
    return 'other'


def preview_kind(ext: str, is_folder: bool) -> str:
    if is_folder:
        return 'folder'
    e = (ext or '').lower().lstrip('.')
    if e in INSTALL_EXTS:
        return 'install'
    if e in IMAGE_EXTS:
        return 'image'
    if e in VIDEO_EXTS:
        return 'video'
    if e in AUDIO_EXTS:
        return 'audio'
    if e == 'pdf':
        return 'pdf'
    if e in CODE_EXTS or e in {'txt', 'md', 'markdown', 'json', 'xml', 'yaml', 'yml', 'sql', 'log'}:
        return 'text'
    if e in OFFICE_EXTS:
        return 'office'
    return 'download'


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    ext = row.get('ext') or ''
    is_folder = bool(row['is_folder'])
    return {
        'id': row['id'],
        'parentId': row['parent_id'],
        'name': row['name'],
        'isFolder': is_folder,
        'ext': ext,
        'mimeType': row.get('mime_type'),
        'sizeBytes': int(row.get('size_bytes') or 0),
        'category': row.get('category') or guess_category(ext, is_folder),
        'createdBy': row.get('created_by'),
        'updatedBy': row.get('updated_by'),
        'createdAt': row['created_at'].isoformat(sep=' ', timespec='seconds')
        if isinstance(row.get('created_at'), datetime)
        else row.get('created_at'),
        'updatedAt': row['updated_at'].isoformat(sep=' ', timespec='seconds')
        if isinstance(row.get('updated_at'), datetime)
        else row.get('updated_at'),
        'previewKind': preview_kind(ext, is_folder),
        'canPreview': preview_kind(ext, is_folder) not in {'install', 'download', 'office', 'folder'},
    }


def _current_user() -> str:
    return getattr(g, 'current_user', None) or 'system'


def _get_by_id(cursor, file_id: int) -> Optional[dict[str, Any]]:
    cursor.execute('SELECT * FROM file_entry WHERE id = %s LIMIT 1', (file_id,))
    return cursor.fetchone()


def _assert_unique_name(cursor, parent_id: Optional[int], name: str, exclude_id: Optional[int] = None) -> None:
    if parent_id is None:
        sql = 'SELECT id FROM file_entry WHERE parent_id IS NULL AND name = %s'
        params: list[Any] = [name]
    else:
        sql = 'SELECT id FROM file_entry WHERE parent_id = %s AND name = %s'
        params = [parent_id, name]
    if exclude_id is not None:
        sql += ' AND id <> %s'
        params.append(exclude_id)
    sql += ' LIMIT 1'
    cursor.execute(sql, params)
    if cursor.fetchone():
        raise ValueError(f'同级目录下已存在「{name}」')


def _resolve_storage_path(storage_key: Optional[str]) -> Path:
    if not storage_key:
        raise ValueError('文件存储路径无效')
    root = ensure_upload_root().resolve()
    path = (root / storage_key).resolve()
    if not str(path).startswith(str(root)):
        raise ValueError('非法文件路径')
    return path


def get_file(file_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            row = _get_by_id(cursor, file_id)
            return _serialize_row(row) if row else None
    finally:
        conn.close()


def list_files(
    parent_id: Optional[int] = None,
    *,
    keyword: str = '',
    category: str = '',
    ext: str = '',
    created_by: str = '',
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            clauses: list[str] = []
            params: list[Any] = []

            searching = bool(keyword.strip() or category.strip() or ext.strip() or created_by.strip())
            if searching:
                if keyword.strip():
                    clauses.append('name LIKE %s')
                    params.append(f'%{keyword.strip()}%')
                if category.strip():
                    clauses.append('category = %s')
                    params.append(category.strip())
                if ext.strip():
                    clauses.append('ext = %s')
                    params.append(ext.strip().lstrip('.').lower())
                if created_by.strip():
                    clauses.append('created_by LIKE %s')
                    params.append(f'%{created_by.strip()}%')
            else:
                if parent_id is None:
                    clauses.append('parent_id IS NULL')
                else:
                    clauses.append('parent_id = %s')
                    params.append(parent_id)

            where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
            cursor.execute(
                f"""
                SELECT * FROM file_entry
                {where}
                ORDER BY is_folder DESC, name ASC
                """,
                params,
            )
            rows = cursor.fetchall() or []
            return [_serialize_row(r) for r in rows]
    finally:
        conn.close()


def get_breadcrumbs(folder_id: Optional[int]) -> list[dict[str, Any]]:
    if folder_id is None:
        return [{'id': None, 'name': '根目录'}]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            chain: list[dict[str, Any]] = []
            current = folder_id
            guard = 0
            while current is not None and guard < 64:
                row = _get_by_id(cursor, current)
                if not row or not row['is_folder']:
                    break
                chain.append({'id': row['id'], 'name': row['name']})
                current = row['parent_id']
                guard += 1
            chain.reverse()
            return [{'id': None, 'name': '根目录'}, *chain]
    finally:
        conn.close()


def create_folder(parent_id: Optional[int], name: str) -> dict[str, Any]:
    name = (name or '').strip()
    if not name:
        raise ValueError('文件夹名称不能为空')
    if '/' in name or '\\' in name:
        raise ValueError('文件夹名称不能包含路径分隔符')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if parent_id is not None:
                parent = _get_by_id(cursor, parent_id)
                if not parent or not parent['is_folder']:
                    raise ValueError('父目录不存在')
            _assert_unique_name(cursor, parent_id, name)
            user = _current_user()
            cursor.execute(
                """
                INSERT INTO file_entry (
                    parent_id, name, is_folder, ext, mime_type, size_bytes,
                    category, storage_key, created_by, updated_by
                ) VALUES (%s, %s, 1, NULL, NULL, 0, 'folder', NULL, %s, %s)
                """,
                (parent_id, name, user, user),
            )
            new_id = cursor.lastrowid
            row = _get_by_id(cursor, new_id)
            return _serialize_row(row)
    finally:
        conn.close()


def _find_child_folder(cursor, parent_id: Optional[int], name: str) -> Optional[dict[str, Any]]:
    if parent_id is None:
        cursor.execute(
            """
            SELECT * FROM file_entry
            WHERE parent_id IS NULL AND is_folder = 1 AND name = %s
            LIMIT 1
            """,
            (name,),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM file_entry
            WHERE parent_id = %s AND is_folder = 1 AND name = %s
            LIMIT 1
            """,
            (parent_id, name),
        )
    return cursor.fetchone()


def _ensure_folder(cursor, parent_id: Optional[int], name: str) -> dict[str, Any]:
    """同级已有同名文件夹则复用，否则创建。若同名是文件则报错。"""
    name = name.strip()
    if not name or name in {'.', '..'}:
        raise ValueError('非法文件夹名称')

    if parent_id is not None:
        parent = _get_by_id(cursor, parent_id)
        if not parent or not parent['is_folder']:
            raise ValueError('父目录不存在')

    existing = _find_child_folder(cursor, parent_id, name)
    if existing:
        return existing

    # 同名文件占用
    if parent_id is None:
        cursor.execute(
            'SELECT id, is_folder FROM file_entry WHERE parent_id IS NULL AND name = %s LIMIT 1',
            (name,),
        )
    else:
        cursor.execute(
            'SELECT id, is_folder FROM file_entry WHERE parent_id = %s AND name = %s LIMIT 1',
            (parent_id, name),
        )
    conflict = cursor.fetchone()
    if conflict:
        raise ValueError(f'同级已存在文件「{name}」，无法创建同名文件夹')

    user = _current_user()
    cursor.execute(
        """
        INSERT INTO file_entry (
            parent_id, name, is_folder, ext, mime_type, size_bytes,
            category, storage_key, created_by, updated_by
        ) VALUES (%s, %s, 1, NULL, NULL, 0, 'folder', NULL, %s, %s)
        """,
        (parent_id, name, user, user),
    )
    return _get_by_id(cursor, cursor.lastrowid)


def ensure_relative_folders(parent_id: Optional[int], relative_path: str) -> int | None:
    """
    根据相对路径创建中间目录，返回文件应落入的 parent_id。
    例如 relative_path=a/b/c.txt → 确保 a、b 存在，返回 b 的 id。
    """
    path = (relative_path or '').replace('\\', '/').strip('/')
    if not path:
        return parent_id

    parts = [p for p in path.split('/') if p and p not in {'.', '..'}]
    if not parts:
        return parent_id

    # 最后一段是文件名
    folder_parts = parts[:-1]
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            current = parent_id
            for name in folder_parts:
                folder = _ensure_folder(cursor, current, name)
                current = folder['id']
            return current
    finally:
        conn.close()


def upload_file(
    parent_id: Optional[int],
    upload: FileStorage,
    *,
    relative_path: str = '',
) -> dict[str, Any]:
    if upload is None or not upload.filename:
        raise ValueError('请选择要上传的文件')

    rel = (relative_path or '').replace('\\', '/').strip('/')
    # 浏览器文件夹上传时 filename 可能只是文件名，相对路径在 relativePath
    if rel:
        target_parent = ensure_relative_folders(parent_id, rel)
        raw_name = Path(rel).name
    else:
        target_parent = parent_id
        raw_name = Path(upload.filename).name

    safe = secure_filename(raw_name) or f'file_{uuid.uuid4().hex}'
    display_name = raw_name.strip() or safe
    ext = Path(display_name).suffix.lstrip('.').lower()
    mime = upload.mimetype or mimetypes.guess_type(display_name)[0] or 'application/octet-stream'

    upload.stream.seek(0, os.SEEK_END)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size > FILE_MAX_BYTES:
        raise ValueError(f'文件过大，最大允许 {FILE_MAX_BYTES // (1024 * 1024)} MB')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if target_parent is not None:
                parent = _get_by_id(cursor, target_parent)
                if not parent or not parent['is_folder']:
                    raise ValueError('父目录不存在')

            # 重名自动加后缀
            final_name = display_name
            stem = Path(display_name).stem
            suffix = Path(display_name).suffix
            n = 1
            while True:
                try:
                    _assert_unique_name(cursor, target_parent, final_name)
                    break
                except ValueError:
                    final_name = f'{stem}({n}){suffix}'
                    n += 1
                    if n > 999:
                        raise ValueError('无法生成可用文件名') from None

            storage_key = f'{uuid.uuid4().hex}_{safe}'
            dest = ensure_upload_root() / storage_key
            upload.save(dest)

            user = _current_user()
            category = guess_category(ext, False)
            cursor.execute(
                """
                INSERT INTO file_entry (
                    parent_id, name, is_folder, ext, mime_type, size_bytes,
                    category, storage_key, created_by, updated_by
                ) VALUES (%s, %s, 0, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    target_parent,
                    final_name,
                    ext or None,
                    mime,
                    size,
                    category,
                    storage_key,
                    user,
                    user,
                ),
            )
            row = _get_by_id(cursor, cursor.lastrowid)
            return _serialize_row(row)
    finally:
        conn.close()


def rename_file(file_id: int, name: str) -> dict[str, Any]:
    name = (name or '').strip()
    if not name:
        raise ValueError('名称不能为空')
    if '/' in name or '\\' in name:
        raise ValueError('名称不能包含路径分隔符')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            row = _get_by_id(cursor, file_id)
            if not row:
                raise ValueError('文件不存在')
            _assert_unique_name(cursor, row['parent_id'], name, exclude_id=file_id)

            ext = row['ext']
            category = row['category']
            if not row['is_folder']:
                ext = Path(name).suffix.lstrip('.').lower() or None
                category = guess_category(ext or '', False)

            cursor.execute(
                """
                UPDATE file_entry
                SET name = %s, ext = %s, category = %s, updated_by = %s
                WHERE id = %s
                """,
                (name, ext, category, _current_user(), file_id),
            )
            return _serialize_row(_get_by_id(cursor, file_id))
    finally:
        conn.close()


def move_file(file_id: int, target_parent_id: Optional[int]) -> dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            row = _get_by_id(cursor, file_id)
            if not row:
                raise ValueError('文件不存在')

            if target_parent_id is not None:
                if target_parent_id == file_id:
                    raise ValueError('不能移动到自身')
                parent = _get_by_id(cursor, target_parent_id)
                if not parent or not parent['is_folder']:
                    raise ValueError('目标目录不存在')
                # 防止把文件夹移到自己的子树
                if row['is_folder']:
                    cur = target_parent_id
                    while cur is not None:
                        if cur == file_id:
                            raise ValueError('不能移动到自己的子目录')
                        p = _get_by_id(cursor, cur)
                        cur = p['parent_id'] if p else None

            _assert_unique_name(cursor, target_parent_id, row['name'], exclude_id=file_id)
            cursor.execute(
                'UPDATE file_entry SET parent_id = %s, updated_by = %s WHERE id = %s',
                (target_parent_id, _current_user(), file_id),
            )
            return _serialize_row(_get_by_id(cursor, file_id))
    finally:
        conn.close()


def _delete_recursive(cursor, file_id: int) -> None:
    row = _get_by_id(cursor, file_id)
    if not row:
        return
    if row['is_folder']:
        cursor.execute('SELECT id FROM file_entry WHERE parent_id = %s', (file_id,))
        children = cursor.fetchall() or []
        for child in children:
            _delete_recursive(cursor, child['id'])
    else:
        key = row.get('storage_key')
        if key:
            path = ensure_upload_root() / key
            if path.exists():
                path.unlink(missing_ok=True)
    cursor.execute('DELETE FROM file_entry WHERE id = %s', (file_id,))


def delete_files(ids: list[int]) -> int:
    if not ids:
        raise ValueError('请选择要删除的文件')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            count = 0
            for fid in ids:
                if _get_by_id(cursor, int(fid)):
                    _delete_recursive(cursor, int(fid))
                    count += 1
            return count
    finally:
        conn.close()


def get_download_path(file_id: int) -> tuple[Path, str, str]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            row = _get_by_id(cursor, file_id)
            if not row:
                raise ValueError('文件不存在')
            if row['is_folder']:
                raise ValueError('文件夹请使用压缩下载')
            path = _resolve_storage_path(row.get('storage_key'))
            if not path.exists():
                raise ValueError('物理文件丢失')
            mime = row.get('mime_type') or 'application/octet-stream'
            return path, row['name'], mime
    finally:
        conn.close()


def read_text_preview(file_id: int, max_bytes: int = 512_000) -> dict[str, Any]:
    path, name, _mime = get_download_path(file_id)
    data = path.read_bytes()[:max_bytes]
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('gbk', errors='replace')
    return {'name': name, 'content': text, 'truncated': len(data) >= max_bytes}


def open_path_for_stream(file_id: int) -> tuple[Path, str, str]:
    return get_download_path(file_id)
