"""Unit tests for AST governance policy analyzer and capability token signer."""

import time
import pytest
from src.governance.ast_policy import (
    ASTGovernancePolicy,
    SecurityPolicyViolation,
    enforce_code_safety,
    validate_code_safety,
)
from src.governance/token_signer import TokenSigner, hash_code_payload


def test_safe_python_code() -> None:
    """Verify standard benign computational code passes AST policy validation."""
    safe_code = """
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

result = calculate_fibonacci(10)
print(f"Fibonacci: {result}")
"""
    is_safe, violations = validate_code_safety(safe_code)
    assert is_safe is True
    assert len(violations) == 0


@pytest.mark.parametrize(
    "forbidden_code, expected_term",
    [
        ("import os\nos.system('ls')", "Forbidden module import: 'os'"),
        ("import sys\nsys.exit(0)", "Forbidden module import: 'sys'"),
        ("import subprocess\nsubprocess.Popen(['whoami'])", "Forbidden module import: 'subprocess'"),
        ("import socket\ns = socket.socket()", "Forbidden module import: 'socket'"),
        ("from shutil import rmtree", "Forbidden module import from: 'shutil'"),
        ("eval('1 + 1')", "Forbidden builtin function identifier access: 'eval'"),
        ("exec('import os')", "Forbidden builtin function identifier access: 'exec'"),
        ("x = __builtins__", "Forbidden direct access to '__builtins__'"),
        ("getattr(object, 'attr')", "Forbidden builtin function identifier access: 'getattr'"),
        ("cls = type.__subclasses__()", "Forbidden attribute access: '__subclasses__'"),
    ],
)
def test_blocked_primitives_and_exploits(forbidden_code: str, expected_term: str) -> None:
    """Verify blacklisted imports and dynamic evaluation primitives trigger safety violations."""
    is_safe, violations = validate_code_safety(forbidden_code)
    assert is_safe is False
    assert any(expected_term in v for v in violations)

    with pytest.raises(SecurityPolicyViolation) as exc_info:
        enforce_code_safety(forbidden_code)
    assert "AST Security Check Failed" in str(exc_info.value)


def test_syntax_error_handling() -> None:
    """Verify invalid syntax yields a controlled violation rather than uncaught error."""
    invalid_code = "def invalid_syntax(:"
    is_safe, violations = validate_code_safety(invalid_code)
    assert is_safe is False
    assert any("SyntaxError" in v for v in violations)


def test_token_signer_valid_workflow() -> None:
    """Verify token generation, signature validation, and payload binding."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)

    code = "x = 42\nprint(x)"
    payload_hash = hash_code_payload(code)

    token = signer.create_capability_token(payload_hash=payload_hash, ttl_seconds=5.0)
    assert isinstance(token, str)

    is_valid, error = signer.verify_capability_token(token, expected_payload_hash=payload_hash)
    assert is_valid is True
    assert error is None


def test_token_signer_expired_token() -> None:
    """Verify token validation fails when token TTL expires."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)

    code = "x = 42"
    payload_hash = hash_code_payload(code)

    token = signer.create_capability_token(payload_hash=payload_hash, ttl_seconds=0.1)
    time.sleep(0.2)

    is_valid, error = signer.verify_capability_token(token, expected_payload_hash=payload_hash)
    assert is_valid is False
    assert error == "TOKEN_EXPIRED"


def test_token_signer_payload_mismatch() -> None:
    """Verify token validation fails when payload digest does not match token digest."""
    secret = "super-secret-governance-key-12345"
    signer = TokenSigner(secret_key=secret)

    code_a = "x = 42"
    code_b = "x = 99"
    hash_a = hash_code_payload(code_a)
    hash_b = hash_code_payload(code_b)

    token = signer.create_capability_token(payload_hash=hash_a, ttl_seconds=10.0)

    is_valid, error = signer.verify_capability_token(token, expected_payload_hash=hash_b)
    assert is_valid is False
    assert error == "PAYLOAD_MISMATCH"
