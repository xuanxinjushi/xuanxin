"""Encrypt gallery assets for password-protected static pages."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"xuanxin1"
PBKDF2_ITERATIONS = 120_000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypted_asset_path(path: Path | str) -> Path:
    """Return output path for an encrypted asset."""
    path = Path(path)
    return path.with_name(path.name + ".enc")


def encrypt_bytes(data: bytes, password: str) -> bytes:
    """Encrypt bytes with AES-GCM; salt and nonce are embedded in the blob."""
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    return MAGIC + salt + nonce + ciphertext


def decrypt_bytes(payload: bytes, password: str) -> bytes:
    """Decrypt bytes produced by :func:`encrypt_bytes`."""
    if len(payload) < len(MAGIC) + 16 + 12 + 16 or payload[: len(MAGIC)] != MAGIC:
        raise ValueError("invalid encrypted payload")
    salt = payload[len(MAGIC) : len(MAGIC) + 16]
    nonce = payload[len(MAGIC) + 16 : len(MAGIC) + 28]
    ciphertext = payload[len(MAGIC) + 28 :]
    key = _derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def encrypt_file(src: Path, dst: Path, password: str) -> Path:
    """Write an encrypted copy of a file."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    payload = encrypt_bytes(src.read_bytes(), password)
    dst.write_bytes(payload)
    return dst
