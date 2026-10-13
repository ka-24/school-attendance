# security.py
import os
from cryptography.fernet import Fernet

# It pulls the key from the cloud server's environment variables.
# Replace the fallback string below with the key you just generated for local testing.
SECRET_KEY = os.getenv("ENCRYPTION_KEY", b'rGQ6UW55v0H9Ewg59C_nLeliIF_LgugnMG4YxNLhz8A=') 

cipher_suite = Fernet(SECRET_KEY)

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode()).decode()