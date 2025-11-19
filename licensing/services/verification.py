# licensing/services/verification.py

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

from cryptography.exceptions import InvalidSignature

from .keys import get_public_key_for_key_id, PublicKeyLoadError


@dataclass
class SignatureVerificationResult:
    ok: bool
    error: str | None = None


def _canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    """
    Serialize a dict to canonical JSON bytes for signing/verification.

    Must match the server-side signing logic exactly:
    - Sorted keys for deterministic field order
    - No extraneous whitespace
    - UTF-8 encoding
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"), 
        ensure_ascii=False,
    ).encode("utf-8")


def _b64url_decode_no_padding(value: str) -> bytes:
    """
    Decode a base64 URL-safe string that may be missing padding.

    The license server encodes using urlsafe_b64encode and strips '=' padding.
    Here we add padding back if needed before decoding.
    """
    # Add padding to make length a multiple of 4
    padding_needed = (4 - (len(value) % 4)) % 4
    value_padded = value + ("=" * padding_needed)
    try:
        return base64.urlsafe_b64decode(value_padded.encode("ascii"))
    except Exception as exc:
        raise ValueError(f"Invalid base64url signature encoding: {exc}") from exc


def verify_license_signature(
    *,
    payload: Dict[str, Any],
    signature_b64: str,
    alg: str,
    key_id: str,
) -> SignatureVerificationResult:
    """
    Verify the Ed25519 signature for a given payload + meta info.

    Inputs:
        payload:    dict that was signed on the server
        signature_b64: base64-url-encoded signature (no padding in original)
        alg:        algorithm name from meta (e.g., 'Ed25519')
        key_id:     key identifier from meta (e.g., 'main-v1')

    Output:
        SignatureVerificationResult(ok=True) on success, or ok=False with error message.
    """
    if alg != "Ed25519":
        return SignatureVerificationResult(
            ok=False,
            error=f"Unsupported algorithm '{alg}'. Only Ed25519 is supported.",
        )

    # Decode signature
    try:
        signature_bytes = _b64url_decode_no_padding(signature_b64)
    except ValueError as exc:
        return SignatureVerificationResult(ok=False, error=str(exc))

    # Canonicalize payload JSON
    try:
        payload_bytes = _canonical_json_bytes(payload)
    except Exception as exc:
        return SignatureVerificationResult(
            ok=False,
            error=f"Failed to canonicalize payload for verification: {exc}",
        )

    # Load appropriate public key
    try:
        public_key = get_public_key_for_key_id(key_id)
    except PublicKeyLoadError as exc:
        return SignatureVerificationResult(ok=False, error=str(exc))

    # Verify signature
    try:
        public_key.verify(signature_bytes, payload_bytes)
    except InvalidSignature:
        return SignatureVerificationResult(ok=False, error="Invalid signature.")
    except Exception as exc:
        return SignatureVerificationResult(
            ok=False,
            error=f"Unexpected error during signature verification: {exc}",
        )

    return SignatureVerificationResult(ok=True, error=None)
