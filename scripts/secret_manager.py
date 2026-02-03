"""
Secret manager abstraction supporting local encrypted files and AWS Secrets Manager.

Usage:
 - Set MONDAY_SECRET_BACKEND to 'aws' to use AWS Secrets Manager (requires boto3 and AWS credentials).
 - Otherwise falls back to local filesystem (encrypted if MONDAY_SECRET_KEY present).
"""

import os
import json
from pathlib import Path
from typing import Optional

SECRET_BACKEND = os.getenv("MONDAY_SECRET_BACKEND", "local")

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None


class LocalSecretManager:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key

    def load(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and raw.get("_encrypted"):
            if not self.secret_key:
                raise RuntimeError("encrypted config but MONDAY_SECRET_KEY not set")
            if Fernet is None:
                raise RuntimeError("cryptography required")
            fernet = Fernet(self.secret_key.encode())
            dec = fernet.decrypt(raw["payload"].encode("utf-8"))
            return json.loads(dec.decode("utf-8"))
        return raw

    def save(self, path: Path, cfg: dict, encrypt: bool = False):
        path.parent.mkdir(parents=True, exist_ok=True)
        if encrypt:
            if not self.secret_key:
                raise RuntimeError("MONDAY_SECRET_KEY not set")
            if Fernet is None:
                raise RuntimeError("cryptography required")
            fernet = Fernet(self.secret_key.encode())
            token = fernet.encrypt(json.dumps(cfg).encode("utf-8")).decode("utf-8")
            wrapper = {"_encrypted": True, "payload": token}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(wrapper, f, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)


class AWSSecretManager:
    def __init__(self):
        try:
            import boto3

            self.client = boto3.client("secretsmanager")
        except Exception as e:
            raise RuntimeError(f"boto3 required for AWS backend: {e}")

    def _secret_name(self, path: Path):
        # secret name derived from filename
        return f"construction-ai-suite/{path.stem}"

    def load(self, path: Path):
        name = self._secret_name(path)
        try:
            resp = self.client.get_secret_value(SecretId=name)
            secret = resp.get("SecretString")
            return json.loads(secret)
        except Exception as e:
            raise RuntimeError(f"failed to load secret {name}: {e}")

    def save(self, path: Path, cfg: dict, encrypt: bool = False):
        # encryption handled by AWS
        name = self._secret_name(path)
        try:
            self.client.put_secret_value(SecretId=name, SecretString=json.dumps(cfg))
        except Exception:
            # try create
            self.client.create_secret(Name=name, SecretString=json.dumps(cfg))


def get_manager():
    if SECRET_BACKEND == "aws":
        return AWSSecretManager()
    secret = os.getenv("MONDAY_SECRET_KEY")
    return LocalSecretManager(secret_key=secret)
