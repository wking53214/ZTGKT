import pytest

from ztgkt import ARCHIVE_DEFAULT_KEY, PayloadSigner


def test_signature_is_stable_and_verifies():
    signer = PayloadSigner(b"unit-test-key")
    sig = signer.sign("content")
    assert signer.sign("content") == sig
    assert signer.verify("content", sig) is True


def test_altered_content_fails_verification():
    signer = PayloadSigner(b"unit-test-key")
    assert signer.verify("content.", signer.sign("content")) is False


def test_different_keys_produce_different_signatures():
    assert PayloadSigner(b"key-a").sign("x") != PayloadSigner(b"key-b").sign("x")


def test_archive_default_key_warns():
    with pytest.warns(UserWarning, match="ARCHIVE_DEFAULT_KEY"):
        signer = PayloadSigner()
    assert signer.sign("x") == PayloadSigner(ARCHIVE_DEFAULT_KEY).sign("x")


def test_empty_key_is_rejected():
    with pytest.raises(ValueError):
        PayloadSigner(b"")


def test_sha384_digest_length():
    assert len(PayloadSigner(b"k").sign("x")) == 96
