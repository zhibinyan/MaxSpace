from flask import Blueprint, Response, g, request, stream_with_context

from middleware.auth import login_required
from response import ApiCode, fail, ok, success
from services import (
    linux_ai_service,
    linux_host_service,
    linux_pref_service,
    linux_session_service,
    linux_sftp_service,
)

linux_bp = Blueprint('linux', __name__, url_prefix='/api/linux')


# ─── 分组 ─────────────────────────────────────────────


@linux_bp.get('/groups')
@login_required
def list_groups():
    return ok(linux_host_service.list_groups())


@linux_bp.post('/groups')
@login_required
def create_group():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.create_group(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='分组已创建', title='主机分组')


@linux_bp.put('/groups/<int:group_id>')
@login_required
def update_group(group_id: int):
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.update_group(group_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='分组已更新', title='主机分组')


@linux_bp.delete('/groups/<int:group_id>')
@login_required
def delete_group(group_id: int):
    try:
        linux_host_service.delete_group(group_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.DELETE_SUCCESS, message='分组已删除', title='主机分组')


# ─── 标签 ─────────────────────────────────────────────


@linux_bp.get('/tags')
@login_required
def list_tags():
    return ok(linux_host_service.list_tags())


@linux_bp.post('/tags')
@login_required
def create_tag():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.create_tag(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='标签已创建', title='标签')


@linux_bp.put('/tags/<int:tag_id>')
@login_required
def update_tag(tag_id: int):
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.update_tag(tag_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='标签已更新', title='标签')


@linux_bp.delete('/tags/<int:tag_id>')
@login_required
def delete_tag(tag_id: int):
    try:
        linux_host_service.delete_tag(tag_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.DELETE_SUCCESS, message='标签已删除', title='标签')


# ─── 主机 ─────────────────────────────────────────────


@linux_bp.get('/hosts')
@login_required
def list_hosts():
    filters = {
        'keyword': request.args.get('keyword'),
        'groupId': request.args.get('groupId'),
        'envType': request.args.get('envType'),
        'status': request.args.get('status'),
        'favorite': request.args.get('favorite'),
        'tagId': request.args.get('tagId'),
    }
    return ok(linux_host_service.list_hosts(filters))


@linux_bp.get('/hosts/<int:host_id>')
@login_required
def get_host(host_id: int):
    item = linux_host_service.get_host(host_id)
    if not item:
        return fail('主机不存在', code=ApiCode.NOT_FOUND, http_status=404)
    return ok(item)


@linux_bp.post('/hosts')
@login_required
def create_host():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.create_host(data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='主机已创建', title='主机管理')


@linux_bp.put('/hosts/<int:host_id>')
@login_required
def update_host(host_id: int):
    data = request.get_json(silent=True) or {}
    try:
        item = linux_host_service.update_host(host_id, data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='主机已更新', title='主机管理')


@linux_bp.delete('/hosts/<int:host_id>')
@login_required
def delete_host(host_id: int):
    try:
        linux_host_service.delete_host(host_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.DELETE_SUCCESS, message='主机已删除', title='主机管理')


@linux_bp.post('/hosts/<int:host_id>/test')
@login_required
def test_host(host_id: int):
    try:
        result = linux_host_service.test_connection(host_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(result, code=ApiCode.UPDATE_SUCCESS, message=result.get('message') or '连接成功', title='测试连接')


@linux_bp.post('/hosts/batch')
@login_required
def batch_hosts():
    data = request.get_json(silent=True) or {}
    action = str(data.get('action') or '').strip()
    ids = data.get('ids') or []
    try:
        count = linux_host_service.batch_hosts(action, [int(i) for i in ids], data)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success({'count': count}, code=ApiCode.UPDATE_SUCCESS, message='批量操作完成', title='主机管理')


# ─── SFTP ─────────────────────────────────────────────


@linux_bp.get('/sftp/list')
@login_required
def sftp_list():
    try:
        host_id = int(request.args.get('hostId') or 0)
        path = request.args.get('path') or '/'
        data = linux_sftp_service.list_dir(host_id, path)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'SFTP 失败：{exc}', code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.post('/sftp/mkdir')
@login_required
def sftp_mkdir():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.mkdir(int(data.get('hostId') or 0), str(data.get('path') or ''))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'创建失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.CREATE_SUCCESS, message='目录已创建', title='远程文件')


@linux_bp.post('/sftp/rename')
@login_required
def sftp_rename():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.rename(
            int(data.get('hostId') or 0),
            str(data.get('oldPath') or ''),
            str(data.get('newPath') or ''),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'重命名失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.UPDATE_SUCCESS, message='已重命名', title='远程文件')


@linux_bp.post('/sftp/delete')
@login_required
def sftp_delete():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.remove(int(data.get('hostId') or 0), str(data.get('path') or ''))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'删除失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.DELETE_SUCCESS, message='已删除', title='远程文件')


@linux_bp.post('/sftp/upload')
@login_required
def sftp_upload():
    try:
        host_id = int(request.form.get('hostId') or 0)
        path = request.form.get('path') or '/'
        upload = request.files.get('file')
        if upload is None:
            ct = request.content_type or ''
            raise ValueError(
                '请选择文件（未收到 file 字段；'
                f'Content-Type={ct or "空"}，请使用 multipart/form-data）'
            )
        item = linux_sftp_service.upload(host_id, path, upload)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'上传失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='上传成功', title='远程文件')


@linux_bp.get('/sftp/download')
@login_required
def sftp_download():
    try:
        host_id = int(request.args.get('hostId') or 0)
        path = request.args.get('path') or ''
        data, name = linux_sftp_service.download_bytes(host_id, path)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'下载失败：{exc}', code=ApiCode.BAD_REQUEST)
    return Response(
        data,
        mimetype='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{name}"'},
    )


@linux_bp.get('/sftp/read')
@login_required
def sftp_read():
    try:
        host_id = int(request.args.get('hostId') or 0)
        path = request.args.get('path') or ''
        data = linux_sftp_service.read_text(host_id, path)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'读取失败：{exc}', code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.put('/sftp/write')
@login_required
def sftp_write():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.write_text(
            int(data.get('hostId') or 0),
            str(data.get('path') or ''),
            str(data.get('content') if data.get('content') is not None else ''),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'保存失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.UPDATE_SUCCESS, message='已保存', title='远程文件')


# ─── 偏好 / 会话 / 审计 ───────────────────────────────


@linux_bp.get('/prefs/<path:key>')
@login_required
def get_pref(key: str):
    try:
        data = linux_pref_service.get_pref(key)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.put('/prefs/<path:key>')
@login_required
def put_pref(key: str):
    body = request.get_json(silent=True)
    # 允许直接传 JSON 值，或 { value: ... }
    if isinstance(body, dict) and 'value' in body and len(body) == 1:
        value = body['value']
    else:
        value = body
    try:
        data = linux_pref_service.set_pref(key, value)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(data, code=ApiCode.UPDATE_SUCCESS, message='偏好已保存', title='终端偏好')


@linux_bp.get('/sessions/recent')
@login_required
def sessions_recent():
    try:
        return ok(linux_session_service.list_user_recent())
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)


@linux_bp.get('/sessions/history')
@login_required
def sessions_history():
    try:
        return ok(linux_session_service.list_user_history())
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)


@linux_bp.post('/sessions')
@login_required
def sessions_register():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_session_service.register_open(
            int(data.get('hostId') or 0),
            host_title=str(data.get('title') or ''),
            host_addr=str(data.get('host') or ''),
            host_user=str(data.get('username') or ''),
            host_port=int(data.get('port') or 22),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='已登记会话', title='SSH')


@linux_bp.get('/sessions/<int:session_id>/recording')
@login_required
def session_recording(session_id: int):
    try:
        data = linux_session_service.get_recording(session_id)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.get('/audit/sessions')
@login_required
def audit_sessions():
    host_id = request.args.get('hostId')
    try:
        data = linux_session_service.list_audit_sessions(
            host_id=int(host_id) if host_id else None,
            username=request.args.get('username') or None,
            date_from=request.args.get('from') or None,
            date_to=request.args.get('to') or None,
            limit=int(request.args.get('limit') or 100),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.get('/audit/commands')
@login_required
def audit_commands():
    host_id = request.args.get('hostId')
    session_id = request.args.get('sessionId')
    try:
        data = linux_session_service.list_audit_commands(
            session_id=int(session_id) if session_id else None,
            host_id=int(host_id) if host_id else None,
            username=request.args.get('username') or None,
            date_from=request.args.get('from') or None,
            date_to=request.args.get('to') or None,
            keyword=request.args.get('keyword') or None,
            limit=int(request.args.get('limit') or 200),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(data)


# ─── SFTP 增强 ────────────────────────────────────────


@linux_bp.put('/sftp/chmod')
@login_required
def sftp_chmod():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.chmod(
            int(data.get('hostId') or 0),
            str(data.get('path') or ''),
            str(data.get('mode') or ''),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'chmod 失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.UPDATE_SUCCESS, message='权限已更新', title='远程文件')


@linux_bp.put('/sftp/chown')
@login_required
def sftp_chown():
    data = request.get_json(silent=True) or {}
    try:
        linux_sftp_service.chown(
            int(data.get('hostId') or 0),
            str(data.get('path') or ''),
            int(data.get('uid')),
            int(data.get('gid')),
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'chown 失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(None, code=ApiCode.UPDATE_SUCCESS, message='所有者已更新', title='远程文件')


@linux_bp.post('/sftp/upload/init')
@login_required
def sftp_upload_init():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_sftp_service.upload_init(
            int(data.get('hostId') or 0),
            str(data.get('path') or '/'),
            str(data.get('fileName') or ''),
            int(data.get('size') or 0),
            getattr(g, 'current_user', None) or '',
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'初始化上传失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.CREATE_SUCCESS, message='上传已初始化', title='远程文件')


@linux_bp.post('/sftp/upload/chunk')
@login_required
def sftp_upload_chunk():
    try:
        token = request.form.get('token') or ''
        offset = int(request.form.get('offset') or 0)
        blob = request.files.get('chunk')
        item = linux_sftp_service.upload_chunk(token, offset, blob)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'分片上传失败：{exc}', code=ApiCode.BAD_REQUEST)
    return ok(item)


@linux_bp.post('/sftp/upload/complete')
@login_required
def sftp_upload_complete():
    data = request.get_json(silent=True) or {}
    try:
        item = linux_sftp_service.upload_complete(str(data.get('token') or ''))
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'完成上传失败：{exc}', code=ApiCode.BAD_REQUEST)
    return success(item, code=ApiCode.UPDATE_SUCCESS, message='上传完成', title='远程文件')


@linux_bp.get('/sftp/upload/<token>')
@login_required
def sftp_upload_status(token: str):
    try:
        item = linux_sftp_service.upload_status(token)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    return ok(item)


@linux_bp.post('/sftp/download-zip')
@login_required
def sftp_download_zip():
    data = request.get_json(silent=True) or {}
    try:
        host_id = int(data.get('hostId') or 0)
        paths = data.get('paths') or []
        if not isinstance(paths, list) or not paths:
            raise ValueError('请选择要下载的路径')
        gen, filename = linux_sftp_service.download_zip_stream(host_id, [str(p) for p in paths])
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'打包下载失败：{exc}', code=ApiCode.BAD_REQUEST)
    return Response(
        stream_with_context(gen),
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@linux_bp.get('/sftp/search')
@login_required
def sftp_search():
    try:
        host_id = int(request.args.get('hostId') or 0)
        path = request.args.get('path') or '/'
        keyword = request.args.get('keyword') or ''
        recursive = (request.args.get('recursive') or '1') not in {'0', 'false', 'False'}
        max_depth = int(request.args.get('maxDepth') or 5)
        data = linux_sftp_service.search(host_id, path, keyword, recursive=recursive, max_depth=max_depth)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'搜索失败：{exc}', code=ApiCode.BAD_REQUEST)
    return ok(data)


@linux_bp.post('/ai/command')
@login_required
def ai_command():
    """自然语言生成 shell 命令（SSE 流式，完成后落库）。"""
    data = request.get_json(silent=True) or {}
    prompt = str(data.get('prompt') or '').strip()
    if not prompt:
        return fail('请输入需求描述', code=ApiCode.BAD_REQUEST)
    username = getattr(g, 'current_user', None) or ''
    try:
        gen = linux_ai_service.stream_command(prompt, username=username)
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'AI 请求失败：{exc}', code=ApiCode.BAD_REQUEST)

    return Response(
        stream_with_context(gen),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


@linux_bp.get('/ai/history')
@login_required
def ai_history():
    try:
        limit = int(request.args.get('limit') or 50)
        items = linux_ai_service.list_chats(
            getattr(g, 'current_user', None) or '',
            limit=limit,
        )
    except ValueError as exc:
        return fail(str(exc), code=ApiCode.BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return fail(f'加载 AI 记录失败：{exc}', code=ApiCode.BAD_REQUEST)
    return ok(items)
