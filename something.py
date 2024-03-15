from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidSignature
import os


def encrypt(plaintext, key):
    # Generate a random initialization vector (IV)
    iv = os.urandom(12)

    # Create AES-GCM cipher with provided key and IV
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Encrypt the plaintext and get the authentication tag
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    # print(tag)

    return (iv, ciphertext, tag)


def decrypt(iv, ciphertext, tag, key):
    # Create AES-GCM cipher with provided key and IV
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the ciphertext and verify the authentication tag
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext

if __name__ == "__main__":
    # Example usage:
    plaintext = b"Secret message"
    key = os.urandom(32)  # Generate a random 256-bit key

    # Encrypt the plaintext
    iv, ciphertext, tag = encrypt(plaintext, key)
    print("Encrypted ciphertext:", ciphertext.hex())
    print("IV:", iv.hex())
    print("Tag:", tag.hex())

    # Decrypt the ciphertext
    decrypted_plaintext = decrypt(iv, ciphertext, tag, key)
    print("Decrypted plaintext:", decrypted_plaintext.decode('utf-8'))