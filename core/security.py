from __future__ import annotations

import hashlib
import os
import re

MAX_STRATEGY_LENGTH = 8000
INJECTION_PATTERNS = [
    r"ignore\s+previous",
    r"system\s+prompt",
    r"developer\s+message",
    r"jailbreak",
    r"exfiltrate",
]


def validate_strategy_input(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Strategy input cannot be empty")
    if len(text) > MAX_STRATEGY_LENGTH:
        raise ValueError("Strategy input too long")
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Potential prompt injection detected")
    return text.strip()


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    salt = os.urandom(16)
    iterations = 120_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations_str, salt_hex, digest_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hashlib.compare_digest(test, expected)
    except Exception:
        return False
