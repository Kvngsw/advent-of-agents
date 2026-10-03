"""Cryptographic HMAC token generator and verifier for sandbox capability tokens."""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Tuple


class TokenSigner:
    """Handles HMAC-SHA256 capability token signing with TTL expiration."""

    def __init__(self, secret_key: str) -> None:
        if not secret_key or len(secret_key) < 16:
            raise ValueError("Secret key must be a non-empty string of at least 16 characters.")
        self._secret_key = secret_key.encode("utf-8")

    def create_capability_token(self, payload_hash: str, ttl_seconds: float = 30.0) -> str:
        """Generate a signed HMAC token containing expiration timestamp and payload digest.

        Args:
            payload_hash: SHA256 hex digest of the validated code or request.
            ttl_seconds: Validity lifetime in seconds (default: 30s).

        Returns:
            Hex string encoded signature token.
        """
        expires_at = time.time() + ttl_seconds
        token_data = {
            "digest": payload_hash,
            "exp": round(expires_at, 3),
        }
        raw_json = json.dumps(token_data, sort_keys=True).encode("utf-8")
        signature = hmac.new(self._secret_key, raw_json, hashlib.sha256).hexdigest()
        
        # Bundle token data and signature into a structured transport string
        token_body = json.dumps({"data": token_data, "sig": signature})
        return token_body

    def verify_capability_token(self, token_str: str, expected_payload_hash: str) -> Tuple[bool, Optional[str]]:
        """Verify signature validity, hash match, and TTL expiration.

        Args:
            token_str: Encoded capability token string.
            expected_payload_hash: SHA256 hex digest of the incoming request payload.

        Returns:
            Tuple of (is_valid: bool, error_reason: Optional[str]).
        """
        try:
            parsed = json.loads(token_str)
            token_data: Dict[str, Any] = parsed["data"]
            signature: str = parsed["sig"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return False, "INVALID_TOKEN_FORMAT"

        raw_json = json.dumps(token_data, sort_keys=True).encode("utf-8")
        expected_sig = hmac.new(self._secret_key, raw_json, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False, "INVALID_SIGNATURE"

        if time.time() > token_data.get("exp", 0):
            return False, "TOKEN_EXPIRED"

        if not hmac.compare_digest(token_data.get("digest", ""), expected_payload_hash):
            return False, "PAYLOAD_MISMATCH"

        return True, None


def hash_code_payload(code: str) -> str:
    """Compute SHA256 digest of source code string for capability binding."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
