"""
Generate a Fernet key for encrypting per-account configs.

Usage:
  python scripts\generate_secret_key.py

Output: Base64 key you can set as MONDAY_SECRET_KEY in env.
Do NOT commit this key to source control.
"""

from cryptography.fernet import Fernet


def main():
    key = Fernet.generate_key()
    print(key.decode())


if __name__ == "__main__":
    main()
