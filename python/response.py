"""统一 API 响应与业务状态码。"""

from __future__ import annotations

from typing import Any, Optional

from flask import jsonify


class ApiCode:
    """业务状态码：0 表示成功且不弹窗；1xxx 成功并弹窗；4xx/5xx 失败并弹窗。"""

    OK = 0

    LOGIN_SUCCESS = 1001
    CREATE_SUCCESS = 1002
    UPDATE_SUCCESS = 1003
    DELETE_SUCCESS = 1004

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500


def _body(
    code: int,
    message: str,
    data: Any = None,
    *,
    title: Optional[str] = None,
    notify: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {'code': code, 'message': message}
    if data is not None:
        payload['data'] = data
    if title:
        payload['title'] = title
    if notify:
        payload['notify'] = notify
    return payload


def ok(data: Any = None, message: str = 'ok') -> tuple[Any, int]:
    """查询成功，不弹窗。"""
    return jsonify(_body(ApiCode.OK, message, data)), 200


def success(
    data: Any = None,
    *,
    code: int = ApiCode.CREATE_SUCCESS,
    message: str,
    title: Optional[str] = None,
    notify_type: str = 'success',
    notify_position: str = 'top-right',
) -> tuple[Any, int]:
    """写操作成功，前端弹成功通知。"""
    notify = {'type': notify_type, 'position': notify_position}
    return jsonify(_body(code, message, data, title=title, notify=notify)), 200


def fail(
    message: str,
    *,
    code: int = ApiCode.BAD_REQUEST,
    http_status: Optional[int] = None,
    title: Optional[str] = None,
    notify_type: str = 'error',
    notify_position: str = 'top-center',
) -> tuple[Any, int]:
    """操作失败，前端弹错误通知。"""
    status = http_status if http_status is not None else code
    notify = {'type': notify_type, 'position': notify_position}
    if code == ApiCode.BAD_REQUEST:
        notify['type'] = 'warning'
    return jsonify(_body(code, message, title=title, notify=notify)), status
