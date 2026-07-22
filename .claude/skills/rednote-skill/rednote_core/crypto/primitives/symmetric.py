"""AES symmetric encryption primitives.

Uses pycryptodomex for AES-CBC and AES-ECB with PKCS7 padding.
"""

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """Encrypt plaintext using AES-CBC with PKCS7 padding.

    Args:
        key: AES key (16, 24, or 32 bytes)
        iv: Initialization vector (16 bytes)
        plaintext: Data to encrypt

    Returns:
        Encrypted ciphertext bytes
    """
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return cipher.encrypt(pad(plaintext, AES.block_size))


def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """Decrypt ciphertext using AES-CBC with PKCS7 padding.

    Args:
        key: AES key (16, 24, or 32 bytes)
        iv: Initialization vector (16 bytes)
        ciphertext: Data to decrypt

    Returns:
        Decrypted plaintext bytes
    """
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


def aes_ecb_encrypt(key: bytes, plaintext: bytes) -> bytes:
    """Encrypt plaintext using AES-ECB with PKCS7 padding.

    Args:
        key: AES key (16, 24, or 32 bytes)
        plaintext: Data to encrypt

    Returns:
        Encrypted ciphertext bytes
    """
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(pad(plaintext, AES.block_size))


def aes_ecb_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    """Decrypt ciphertext using AES-ECB with PKCS7 padding.

    Args:
        key: AES key (16, 24, or 32 bytes)
        ciphertext: Data to decrypt

    Returns:
        Decrypted plaintext bytes
    """
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)
