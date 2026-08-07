from flask import Blueprint, g, request

from middleware.auth import login_required, super_admin_required
from response import ApiCode, fail, ok, success
from services import menu_service

menu_bp = Blueprint('menu', __name__, url_prefix='/api/menus')


@menu_bp.get('/tree')
@login_required
def list_menu_tree():
    return ok(menu_service.list_menu_tree())


@menu_bp.get('')
@login_required
def list_menus():
    return ok(menu_service.list_menus_flat())


@menu_bp.post('')
@login_required
def create_menu():
    data = request.get_json(silent=True) or {}
    try:
        menu = menu_service.create_menu(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        menu,
        code=ApiCode.CREATE_SUCCESS,
        message='菜单已创建',
        title='菜单',
    )


@menu_bp.put('/<int:menu_id>')
@login_required
def update_menu(menu_id: int):
    data = request.get_json(silent=True) or {}
    try:
        menu = menu_service.update_menu(menu_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        menu,
        code=ApiCode.UPDATE_SUCCESS,
        message='菜单已更新',
        title='菜单',
    )


@menu_bp.delete('/<int:menu_id>')
@super_admin_required
def delete_menu(menu_id: int):
    try:
        menu_service.delete_menu(menu_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(
        None,
        code=ApiCode.DELETE_SUCCESS,
        message='已删除',
        title='菜单',
    )


@menu_bp.get('/me')
@login_required
def current_admin():
    return ok({
        'username': g.current_user,
        'isSuper': menu_service.is_super_admin(g.current_user),
    })
