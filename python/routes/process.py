from flask import Blueprint, request

from middleware.auth import login_required
from response import ApiCode, fail, ok, success
from services import process_service

process_bp = Blueprint('process', __name__, url_prefix='/api/processes')


@process_bp.get('')
@login_required
def list_processes():
    return ok(process_service.list_processes())


@process_bp.get('/<int:process_id>')
@login_required
def get_process(process_id: int):
    process = process_service.get_process_by_id(process_id)
    if not process:
        return fail('流程不存在', code=ApiCode.NOT_FOUND, http_status=404)
    return ok(process)


@process_bp.post('')
@login_required
def create_process():
    data = request.get_json(silent=True) or {}
    try:
        process = process_service.create_process(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        process,
        code=ApiCode.CREATE_SUCCESS,
        message='流程已创建',
        title='流程',
    )


@process_bp.put('/<int:process_id>')
@login_required
def update_process(process_id: int):
    data = request.get_json(silent=True) or {}
    try:
        process = process_service.update_process(process_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        process,
        code=ApiCode.UPDATE_SUCCESS,
        message='流程已保存',
        title='流程',
    )


@process_bp.delete('/<int:process_id>')
@login_required
def delete_process(process_id: int):
    try:
        process_service.delete_process(process_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        None,
        code=ApiCode.DELETE_SUCCESS,
        message='已删除',
        title='流程',
    )
