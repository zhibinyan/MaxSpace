import os
from pathlib import Path


def _load_dotenv() -> None:
    """轻量加载 python/.env（不覆盖已有环境变量）。"""
    env_path = Path(__file__).resolve().parent / '.env'
    if not env_path.is_file():
        return
    try:
        for raw in env_path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


_load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '12345678')
DB_NAME = os.getenv('DB_NAME', 'maxadmin')

JWT_SECRET = os.getenv('JWT_SECRET', 'maxadmin-dev-secret-change-in-production')
JWT_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRE_HOURS', '24'))

API_PORT = int(os.getenv('PORT', '5050'))
FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '8888'))

# 文件本地存储根目录（相对 python/ 或绝对路径）
_UPLOAD_ENV = os.getenv('FILE_UPLOAD_DIR', '').strip()
FILE_UPLOAD_DIR = Path(_UPLOAD_ENV) if _UPLOAD_ENV else Path(__file__).resolve().parent / 'uploads'
FILE_MAX_BYTES = int(os.getenv('FILE_MAX_BYTES', str(200 * 1024 * 1024)))

# TokenHub / DeepSeek（勿把密钥写进前端；用环境变量 AI_API_KEY）
AI_API_URL = os.getenv(
    'AI_API_URL',
    'https://tokenhub.tencentmaas.com/v1/chat/completions',
).strip()
AI_API_KEY = os.getenv('AI_API_KEY', '').strip()
AI_MODEL = os.getenv('AI_MODEL', 'deepseek-v4-flash-202605').strip()
