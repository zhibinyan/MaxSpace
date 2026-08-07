from functools import wraps
from typing import Callable, Optional

import jwt
from flask import g, request

from config import JWT_SECRET
from response import ApiCode, fail


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload.get('sub')
    except jwt.PyJWTError:
        return None


def get_bearer_token() -> str:
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    # 媒体预览（img/video/audio）无法带 Header，允许 ?token=
    q = request.args.get('token', '').strip()
    return q


def login_required(view: Callable):
    @wraps(view)
    def wrapper(*args, **kwargs):
        username = verify_token(get_bearer_token())
        if not username:
            return fail('未登录或登录已过期', code=ApiCode.UNAUTHORIZED, http_status=401)
        g.current_user = username
        return view(*args, **kwargs)

    return wrapper


def super_admin_required(view: Callable):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        from services.menu_service import is_super_admin

        if not is_super_admin(g.current_user):
            return fail('仅超级管理员可删除菜单', code=ApiCode.FORBIDDEN, http_status=403)
        return view(*args, **kwargs)

    return wrapper
