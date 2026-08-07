from flask import Blueprint, request

from middleware.auth import login_required
from response import ApiCode, fail, ok, success
from services import markdown_service

markdown_bp = Blueprint('markdown', __name__, url_prefix='/api/markdowns')


@markdown_bp.get('')
@login_required
def list_markdowns():
    return ok(markdown_service.list_markdowns())


@markdown_bp.get('/<int:markdown_id>')
@login_required
def get_markdown(markdown_id: int):
    item = markdown_service.get_markdown_by_id(markdown_id)
    if not item:
        return fail('备忘录不存在', code=ApiCode.NOT_FOUND, http_status=404)
    return ok(item)


@markdown_bp.post('')
@login_required
def create_markdown():
    data = request.get_json(silent=True) or {}
    try:
        item = markdown_service.create_markdown(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        item,
        code=ApiCode.CREATE_SUCCESS,
        message='备忘录已创建',
        title='备忘录',
    )


@markdown_bp.put('/<int:markdown_id>')
@login_required
def update_markdown(markdown_id: int):
    data = request.get_json(silent=True) or {}
    try:
        item = markdown_service.update_markdown(markdown_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        item,
        code=ApiCode.UPDATE_SUCCESS,
        message='备忘录已保存',
        title='备忘录',
    )


@markdown_bp.delete('/<int:markdown_id>')
@login_required
def delete_markdown(markdown_id: int):
    try:
        markdown_service.delete_markdown(markdown_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        None,
        code=ApiCode.DELETE_SUCCESS,
        message='已删除',
        title='备忘录',
    )
