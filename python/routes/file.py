from flask import Blueprint, request, send_file

from middleware.auth import login_required
from response import ApiCode, fail, ok, success
from services import file_service

file_bp = Blueprint('file', __name__, url_prefix='/api/files')


def _parse_parent_id(raw):
    if raw is None or raw == '' or raw == 'null':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError('parentId 无效') from exc


@file_bp.get('')
@login_required
def list_files():
    try:
        parent_id = _parse_parent_id(request.args.get('parentId'))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)

    items = file_service.list_files(
        parent_id,
        keyword=request.args.get('keyword', ''),
        category=request.args.get('category', ''),
        ext=request.args.get('ext', ''),
        created_by=request.args.get('createdBy', ''),
    )
    breadcrumbs = file_service.get_breadcrumbs(parent_id)
    return ok({'list': items, 'breadcrumbs': breadcrumbs, 'parentId': parent_id})


@file_bp.get('/<int:file_id>')
@login_required
def get_file(file_id: int):
    item = file_service.get_file(file_id)
    if not item:
        return fail('文件不存在', code=ApiCode.NOT_FOUND, http_status=404)
    return ok(item)


@file_bp.post('/folder')
@login_required
def create_folder():
    data = request.get_json(silent=True) or {}
    try:
        parent_id = _parse_parent_id(data.get('parentId'))
        item = file_service.create_folder(parent_id, str(data.get('name', '')))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='文件夹已创建', title='文件管理')


@file_bp.post('/upload')
@login_required
def upload_file():
    try:
        parent_id = _parse_parent_id(request.form.get('parentId'))
        upload = request.files.get('file')
        relative_path = str(request.form.get('relativePath') or '').strip()
        item = file_service.upload_file(parent_id, upload, relative_path=relative_path)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='上传成功', title='文件管理')


@file_bp.put('/<int:file_id>/rename')
@login_required
def rename_file(file_id: int):
    data = request.get_json(silent=True) or {}
    try:
        item = file_service.rename_file(file_id, str(data.get('name', '')))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='已重命名', title='文件管理')


@file_bp.put('/<int:file_id>/move')
@login_required
def move_file(file_id: int):
    data = request.get_json(silent=True) or {}
    try:
        target = _parse_parent_id(data.get('parentId'))
        item = file_service.move_file(file_id, target)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='已移动', title='文件管理')


@file_bp.post('/delete')
@login_required
def delete_files():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    try:
        count = file_service.delete_files([int(i) for i in ids])
    except (TypeError, ValueError) as exc:
        return fail(str(exc) if str(exc) else '参数错误', code=ApiCode.BAD_REQUEST)
    return success(
        {'count': count},
        code=ApiCode.DELETE_SUCCESS,
        message=f'已删除 {count} 项',
        title='文件管理',
    )


@file_bp.get('/<int:file_id>/download')
@login_required
def download_file(file_id: int):
    try:
        path, name, mime = file_service.get_download_path(file_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return send_file(path, mimetype=mime, as_attachment=True, download_name=name)


@file_bp.get('/<int:file_id>/raw')
@login_required
def raw_file(file_id: int):
    """预览用：图片/音视频/PDF 内联输出。"""
    try:
        path, name, mime = file_service.get_download_path(file_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return send_file(path, mimetype=mime, as_attachment=False, download_name=name)


@file_bp.get('/<int:file_id>/text')
@login_required
def text_preview(file_id: int):
    try:
        data = file_service.read_text_preview(file_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(data)
