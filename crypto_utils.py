from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os

def get_key():
    key = os.getenv('AES_KEY')
    return key.encode('utf-8').ljust(32)[:32]

def encrypt_data(plain_text):
    key = get_key()
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(
        pad(plain_text.encode('utf-8'), AES.block_size)
    )
    result = base64.b64encode(iv + encrypted).decode('utf-8')
    return result

def decrypt_data(encrypted_text):
    key = get_key()
    raw = base64.b64decode(encrypted_text)
    iv = raw[:16]
    encrypted = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(
        cipher.decrypt(encrypted),
        AES.block_size
    ).decode('utf-8')
    return decrypted
    