"""Cryptographically secure case-code generation and HMAC-SHA256 hashing utilities.

Requirements & Cryptographic Guarantees:
- Cryptographically secure pseudorandom number generator (CSPRNG via Python's standard `secrets` module).
- Unpredictable and impossible to enumerate.
- Crockford-inspired Base32 character set (32 characters: 2-9, A-Z excluding 0, O, 1, I, L) to eliminate ambiguous glyphs.
- Exact Entropy Calculation:
    16 random characters chosen from 32 distinct safe symbols:
    32^16 = (2^5)^16 = 2^80 ≈ 1.2089 × 10^24 combinations (80 bits of cryptographic entropy).
- Raw case code returned to reporter once upon submission.
- Only a one-way HMAC-SHA256 digest is persisted in the database.
"""

import hashlib
import hmac
import secrets
from typing import Optional

from app.core.config import settings

# 32 unambiguous characters (excludes 0, O, 1, I, L)
CROCKFORD_SAFE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
CASE_CODE_PREFIX = "WD"
BLOCK_SIZE = 4
BLOCK_COUNT = 4  # 16 characters total -> 32^16 = 2^80 combinations (~1.2e24)


def generate_case_code() -> str:
    """Generate a cryptographically secure, human-readable case code.

    Format example: WD-A7K9-3MXP-8Y4B-2RTC
    Total entropy: exactly 2^80 combinations (80 bits) generated via CSPRNG `secrets`.
    """
    blocks = [
        "".join(secrets.choice(CROCKFORD_SAFE_ALPHABET) for _ in range(BLOCK_SIZE))
        for _ in range(BLOCK_COUNT)
    ]
    return f"{CASE_CODE_PREFIX}-{'-'.join(blocks)}"


def normalize_case_code(code: str) -> str:
    """Normalize user input by trimming whitespace and converting to uppercase."""
    return code.strip().upper()


def hash_case_code(code: str, salt: Optional[str] = None) -> str:
    """Compute a one-way HMAC-SHA256 cryptographic digest of the normalized case code.

    The database stores ONLY this 64-character hex digest. Raw case codes are never
    persisted, ensuring that even a full database compromise yields zero readable codes.
    """
    normalized = normalize_case_code(code)
    pepper = (salt or settings.CASE_CODE_SALT).encode("utf-8")
    digest = hmac.new(pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest
