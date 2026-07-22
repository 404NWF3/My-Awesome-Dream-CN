"""RSA asymmetric encryption primitives."""

from Cryptodome.Cipher import PKCS1_OAEP, PKCS1_v1_5
from Cryptodome.PublicKey import RSA


def rsa_encrypt_oaep(public_key_pem: str, plaintext: bytes) -> bytes:
    """Encrypt plaintext using RSA-OAEP.

    Args:
        public_key_pem: RSA public key in PEM format
        plaintext: Data to encrypt

    Returns:
        Encrypted ciphertext bytes
    """
    key = RSA.import_key(public_key_pem)
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(plaintext)


def rsa_encrypt_pkcs1v15(public_key_pem: str, plaintext: bytes) -> bytes:
    """Encrypt plaintext using RSA PKCS1 v1.5.

    Args:
        public_key_pem: RSA public key in PEM format
        plaintext: Data to encrypt

    Returns:
        Encrypted ciphertext bytes
    """
    key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(key)
    return cipher.encrypt(plaintext)
