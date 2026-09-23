"""Unit tests for cryptographic case-code generation and hashing."""

import re
from app.utils.case_code import (
    CROCKFORD_SAFE_ALPHABET,
    generate_case_code,
    hash_case_code,
    normalize_case_code,
)


def test_generate_case_code_format():
    """Verify generated case codes match the expected prefix and block pattern."""
    code = generate_case_code()
    # Pattern: WD-XXXX-XXXX-XXXX-XXXX (where X is from Crockford alphabet)
    pattern = r"^WD-[2-9A-HJ-KM-NP-Z]{4}-[2-9A-HJ-KM-NP-Z]{4}-[2-9A-HJ-KM-NP-Z]{4}-[2-9A-HJ-KM-NP-Z]{4}$"
    assert re.match(pattern, code) is not None, f"Code '{code}' failed pattern matching"


def test_generate_case_code_entropy_uniqueness():
    """Verify that 1,000 generated case codes are completely unique."""
    generated = {generate_case_code() for _ in range(1000)}
    assert len(generated) == 1000


def test_case_code_excludes_ambiguous_characters():
    """Ensure ambiguous characters (0, O, 1, I, L) are never generated."""
    for _ in range(100):
        code = generate_case_code()
        assert "0" not in code
        assert "O" not in code
        assert "1" not in code
        assert "I" not in code
        assert "L" not in code


def test_hash_case_code_deterministic():
    """Ensure hashing is deterministic and produces standard 64-char hex HMAC-SHA256 digest."""
    code = "WD-ABCD-EFGH-JKMN-PQRS"
    hash1 = hash_case_code(code)
    hash2 = hash_case_code(code)
    assert hash1 == hash2
    assert len(hash1) == 64
    assert re.match(r"^[0-9a-f]{64}$", hash1) is not None


def test_hash_case_code_case_insensitivity():
    """Ensure case codes normalize so lowercase input produces the same hash."""
    upper = "WD-ABCD-EFGH-JKMN-PQRS"
    lower = "wd-abcd-efgh-jkmn-pqrs"
    spaced = "  WD-ABCD-EFGH-JKMN-PQRS  "

    assert hash_case_code(upper) == hash_case_code(lower)
    assert hash_case_code(upper) == hash_case_code(spaced)
