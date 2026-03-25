import pytest

from app.hasher import pbkdf2_sha256


def test_hash_and_verify():
    assert (
        pbkdf2_sha256.verify(
            "mySuperS1rongPwd@",
            pbkdf2_sha256.hash("mySuperS1rongPwd@"),
        )
        is True
    )


def test_hash_no_input():
    with pytest.raises(ValueError, match="Password cannot be empty."):
        pbkdf2_sha256.hash(
            None,
        )


def test_verify_invalid_format():
    with pytest.raises(ValueError, match="Invalid hash format."):
        pbkdf2_sha256.verify(
            "mySuperS1rongPwd@",
            "lalala",
        )


def test_verify_invalid_iterations():
    with pytest.raises(ValueError, match="Invalid hash format."):
        pbkdf2_sha256.verify(
            "passwd",
            "pbkdf2_sha256$a1$salt$hash",
        )


def test_verify_invalid_salt():
    with pytest.raises(ValueError, match="Invalid hash format."):
        pbkdf2_sha256.verify(
            "passwd",
            "pbkdf2_sha256$10000$sal222t$hash",
        )


def test_verify_invalid_hash():
    with pytest.raises(ValueError, match="Invalid hash format."):
        pbkdf2_sha256.verify(
            "passwd",
            "pbkdf2_sha256$10000$ptALivOIMj/M4IZOmgzZew==$hash124",
        )


@pytest.mark.parametrize(
    ("passwd", "hash"),
    [
        (None, None),
        (None, ""),
        ("", None),
        ("", ""),
        ("a", ""),
        ("", "a"),
    ],
)
def test_verify_invalid_input(passwd: str, hash: str):
    with pytest.raises(ValueError, match="Password and hashed value cannot be empty."):
        pbkdf2_sha256.verify(
            passwd,
            hash,
        )

    with pytest.raises(ValueError, match="Password cannot be empty."):
        pbkdf2_sha256.hash(
            "",
        )
