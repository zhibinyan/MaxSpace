"""主机凭证加解密（Fernet）。"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config import JWT_SECRET


def _fernet() -> Fernet:
    digest = hashlib.sha256(JWT_SECRET.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_text(plain: str | None) -> str | None:
    if plain is None or plain == '':
        return None
    return _fernet().encrypt(plain.encode('utf-8')).decode('utf-8')


def decrypt_text(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return None
