import sys

import pymysql
from flask import Flask, request
from flask_cors import CORS

from auth import create_token, normalize_password_md5
from config import API_PORT
from db import get_connection
from response import ApiCode, fail, ok, success
from flask_sock import Sock

from middleware.auth import verify_token
from routes.admin import admin_bp
from routes.menu import menu_bp
from routes.markdown import markdown_bp
from routes.process import process_bp
from routes.file import file_bp
from routes.linux import linux_bp
from services import linux_docker_service, linux_ssh_service


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    sock = Sock(app)
    app.register_blueprint(admin_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(markdown_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(linux_bp)

    @sock.route('/ws/linux/ssh/<int:host_id>')
    def linux_ssh_ws(ws, host_id: int):
        token = (request.args.get('token') or '').strip()
        username = verify_token(token)
        if not username:
            try:
                ws.send('{"type":"error","message":"未登录或登录已过期"}')
            except Exception:
                pass
            ws.close()
            return
        linux_ssh_service.bridge_websocket(ws, host_id, username)

    @sock.route('/ws/linux/docker/<int:host_id>/exec')
    def linux_docker_exec_ws(ws, host_id: int):
        token = (request.args.get('token') or '').strip()
        container = (request.args.get('container') or '').strip()
        username = verify_token(token)
        if not username:
            try:
                ws.send('{"type":"error","message":"未登录或登录已过期"}')
            except Exception:
                pass
            ws.close()
            return
        linux_docker_service.bridge_exec_websocket(ws, host_id, container, username)

    @app.post('/api/login')
    def login():
        data = request.get_json(silent=True) or {}
        username = str(data.get('username', '')).strip()
        password_md5 = normalize_password_md5(str(data.get('password', '')))

        if not username or not password_md5:
            return fail('用户名和密码不能为空', code=ApiCode.BAD_REQUEST, title='登录')

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT username, password, is_super FROM admin WHERE username = %s LIMIT 1',
                    (username,),
                )
                row = cursor.fetchone()
        finally:
            conn.close()

        if not row or row['password'] != password_md5:
            return fail(
                '用户名或密码错误',
                code=ApiCode.UNAUTHORIZED,
                http_status=401,
                title=username,
            )

        token = create_token(row['username'])
        return success(
            {
                'token': token,
                'username': row['username'],
                'isSuper': bool(row['is_super']),
            },
            code=ApiCode.LOGIN_SUCCESS,
            message='登录成功！',
            title=row['username'],
            notify_position='top-right',
        )

    @app.get('/api/health')
    def health():
        return ok(message='ok')

    return app


def check_database_connection() -> None:
    try:
        conn = get_connection()
        try:
            conn.ping(reconnect=False)
        finally:
            conn.close()
    except pymysql.Error as exc:
        print(f'数据库连接失败: {exc}')
        print('请启动 MySQL: mysql.server start')
        sys.exit(1)


def run_server():
    check_database_connection()
    create_app().run(
        host='0.0.0.0',
        port=API_PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == '__main__':
    run_server()
