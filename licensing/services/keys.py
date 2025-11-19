# licensing/services/keys.py

import functools
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from django.conf import settings


class PublicKeyLoadError(Exception):
    """Raised when a public key cannot be loaded or is invalid."""
    pass


@functools.lru_cache(maxsize=1)
def _load_main_public_key() -> ed25519.Ed25519PublicKey:
    """
    Load the main Ed25519 public key from disk.

    This reads from settings.PUBLIC_KEY_PATH and caches the result.
    """
    key_path = Path(settings.PUBLIC_KEY_PATH)

    if not key_path.exists():
        raise PublicKeyLoadError(
            f"Public key file not found at {key_path}. "
            f"Check PUBLIC_KEY_PATH in settings / .env."
        )

    pem_data = key_path.read_bytes()

    try:
        public_key = serialization.load_pem_public_key(pem_data)
    except Exception as exc:
        raise PublicKeyLoadError(
            f"Failed to parse public key PEM at {key_path}: {exc}"
        ) from exc

    if not isinstance(public_key, ed25519.Ed25519PublicKey):
        raise PublicKeyLoadError(
            f"Loaded public key is not an Ed25519 key (got {type(public_key)!r})."
        )

    return public_key


def get_public_key_for_key_id(key_id: str) -> ed25519.Ed25519PublicKey:
    """
    Return the Ed25519 public key for a given key_id.

    """
    if key_id != "main-v1":
        raise PublicKeyLoadError(
            f"Unsupported key_id '{key_id}'. Only 'main-v1' is configured."
        )

    return _load_main_public_key()
