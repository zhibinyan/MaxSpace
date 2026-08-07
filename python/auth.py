import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from config import JWT_SECRET, JWT_EXPIRE_HOURS

MD5_HEX_RE = re.compile(r'^[a-f0-9]{32}$')


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def normalize_password_md5(raw_password: str) -> Optional[str]:
    value = raw_password.strip().lower()
    if MD5_HEX_RE.fullmatch(value):
        return value
    if value:
        return md5_hash(value)
    return None


def create_token(username: str) -> str:
    payload = {
        'sub': username,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
