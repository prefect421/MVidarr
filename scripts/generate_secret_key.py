#!/usr/bin/env python3
"""
Generate a secure secret key for MVidarr Enhanced
"""

import secrets
import string

def generate_secret_key(length=64):
    """Generate a secure random secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    key = generate_secret_key()
    print("Generated secret key:")
    print(key)
    print("")
    print("Add this to your .env file:")
    print(f"SECRET_KEY={key}")