import base64
import hashlib
import hmac
import secrets


class PBKDF2Sha256PasswordHasher:
    def __init__(self, iterations=100000, salt_size=16):
        self.iterations = iterations
        self.salt_size = salt_size

    def hash(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty.")

        salt = secrets.token_bytes(self.salt_size)

        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        salt_encoded = base64.b64encode(salt).decode("utf-8")
        hash_encoded = base64.b64encode(hash_bytes).decode("utf-8")

        return f"pbkdf2_sha256${self.iterations}${salt_encoded}${hash_encoded}"

    @staticmethod
    def verify(password: str, hashed_value: str) -> bool:
        if not password or not hashed_value:
            raise ValueError("Password and hashed value cannot be empty.")

        try:
            _, iterations, salt_encoded, hash_encoded = hashed_value.split("$", 3)
            iterations = int(iterations)  # type: ignore
            salt = base64.b64decode(salt_encoded)
            expected_hash = base64.b64decode(hash_encoded)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid hash format.") from e

        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,  # type: ignore
        )

        return hmac.compare_digest(hash_bytes, expected_hash)


pbkdf2_sha256 = PBKDF2Sha256PasswordHasher()
