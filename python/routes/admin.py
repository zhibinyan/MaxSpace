from flask import Blueprint, request

from middleware.auth import login_required
from response import ApiCode, fail, ok, success
from services import admin_service

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admins')


@admin_bp.get('')
@login_required
def list_admins():
    return ok(admin_service.list_admins())


@admin_bp.post('')
@login_required
def create_admin():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', ''))
    try:
        password_md5 = admin_service.parse_password_md5(str(data.get('password', '')), required=True)
        admin = admin_service.create_admin(username, password_md5)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)

    return success(
        admin,
        code=ApiCode.CREATE_SUCCESS,
        message='管理员已创建',
        title='管理员',
    )


@admin_bp.put('/<int:admin_id>')
@login_required
def update_admin(admin_id: int):
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    try:
        password_md5 = None
        if password is not None and str(password).strip():
            password_md5 = admin_service.parse_password_md5(str(password), required=True)
        admin = admin_service.update_admin(
            admin_id,
            username=str(username).strip() if username is not None else None,
            password_md5=password_md5,
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)

    return success(
        admin,
        code=ApiCode.UPDATE_SUCCESS,
        message='管理员已更新',
        title='管理员',
    )


@admin_bp.delete('/<int:admin_id>')
@login_required
def delete_admin(admin_id: int):
    try:
        admin_service.delete_admin(admin_id)
    except ValueError as exc:
        status = ApiCode.FORBIDDEN if str(exc) == admin_service.SUPER_ADMIN_DELETE_MSG else ApiCode.BAD_REQUEST
        return fail(str(exc), code=status, http_status=status)

    return success(
        None,
        code=ApiCode.DELETE_SUCCESS,
        message='已删除',
        title='管理员',
    )
