"""HMAC-SHA384 attestation over accepted content.

The signature is what makes the gate auditable downstream: a consumer can
confirm that the exact bytes it received are the bytes ZTGKT accepted, and
that they came from a holder of the signing key.

Security note carried over from the archive. The original embedded a literal
key in the pipeline class::

    self._signing_key = b"GENERIC_PIPELINE_HMAC_SECRET_KEY_SHA384_815"

A hardcoded key in source is not a secret. This module keeps that value only
as :data:`ARCHIVE_DEFAULT_KEY`, for byte-compatible replay of archived
signatures when passed explicitly. It is never used as a default: with no
key, the signer generates a random one for this instance and warns, so its
signatures verify only within the process. Supply a real key in any
deployment that consumes the signature as evidence.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import warnings

__all__ = ["ARCHIVE_DEFAULT_KEY", "PayloadSigner"]


ARCHIVE_DEFAULT_KEY: bytes = b"GENERIC_PIPELINE_HMAC_SECRET_KEY_SHA384_815"


class PayloadSigner:
    """Computes and verifies HMAC-SHA384 signatures over UTF-8 content."""

    def __init__(self, signing_key: bytes | str | None = None, digestmod=hashlib.sha384) -> None:
        if signing_key is None:
            warnings.warn(
                "PayloadSigner has no signing_key; using a random per-instance "
                "key, so signatures cannot be verified outside this process. "
                "Pass signing_key= in any deployment.",
                stacklevel=2,
            )
            signing_key = secrets.token_bytes(48)
        if isinstance(signing_key, str):
            signing_key = signing_key.encode("utf-8")
        if not signing_key:
            raise ValueError("signing_key must be non-empty.")
        self._signing_key = signing_key
        self._digestmod = digestmod

    def sign(self, text: str) -> str:
        return hmac.new(self._signing_key, text.encode("utf-8"), self._digestmod).hexdigest()

    def verify(self, text: str, signature: str) -> bool:
        """Constant-time comparison, so a mismatch leaks no timing information."""
        return hmac.compare_digest(self.sign(text), signature)
