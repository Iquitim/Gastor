"""
Security Utilities
==================

Funções para criptografia e segurança de dados sensíveis.
Utiliza Fernet (criptografia simétrica) para proteger chaves de API.
"""

from cryptography.fernet import Fernet
import os
import base64

# O segredo deve ser uma string url-safe base64-encoded de 32 bytes
# Se não configurado, gera uma temporária (mas dados serão perdidos ao reiniciar)
_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not _ENCRYPTION_KEY:
    print("⚠️  AVISO: ENCRYPTION_KEY não configurada! Gerando chave temporária.")
    _ENCRYPTION_KEY = Fernet.generate_key().decode()


def get_cipher_suite():
    return Fernet(_ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """
    Criptografa uma string sensível.
    
    Args:
        value: O valor original (ex: API Secret)
        
    Returns:
        String criptografada (hash)
    """
    if not value:
        return ""
    
    cipher_suite = get_cipher_suite()
    encrypted_bytes = cipher_suite.encrypt(value.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_value(token: str) -> str:
    """
    Descriptografa uma string.
    
    Args:
        token: O valor criptografado
        
    Returns:
        String original
        
    Raises:
        cryptography.fernet.InvalidToken: Se a chave estiver errada ou token inválido
    """
    if not token:
        return ""
        
    cipher_suite = get_cipher_suite()
    decrypted_bytes = cipher_suite.decrypt(token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
