"""Encrypted cookie persistence."""

from __future__ import annotations

import json
import os
from rednote_core.crypto.primitives.symmetric import aes_cbc_encrypt, aes_cbc_decrypt
from rednote_core.crypto.primitives.hash import sha256


def load_cookies(path: str, passphrase: str = "") -> dict:
    """Load and decrypt cookies from file."""
    if not os.path.exists(path):
        return {}

    with open(path, "rb") as f:
        encrypted_data = f.read()

    if not passphrase:
        try:
            return json.loads(encrypted_data.decode())
        except Exception:
            return {}

    key = sha256(passphrase.encode())
    iv = key[:16]

    try:
        raw_iv = encrypted_data[:16]
        raw_ciphertext = encrypted_data[16:]
        plaintext = aes_cbc_decrypt(key, raw_iv, raw_ciphertext)
        return json.loads(plaintext.decode())
    except Exception:
        return {}


def save_cookies(
    cookies: dict,
    path: str,
    passphrase: str = "",
) -> None:
    """Encrypt and save cookies to file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    if not passphrase:
        with open(path, "w") as f:
            json.dump(cookies, f, indent=2)
        return

    key = sha256(passphrase.encode())
    iv = key[:16]

    plaintext = json.dumps(cookies, indent=2).encode()
    ciphertext = aes_cbc_encrypt(key, iv, plaintext)

    with open(path, "wb") as f:
        f.write(iv + ciphertext)
