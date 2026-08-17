from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class ScryptParameters:
    version: int = 1
    n: int = 16384
    r: int = 8
    p: int = 1
    dklen: int = 32
    salt_bytes: int = 16

    def to_dict(self) -> dict[str, int]:
        return {"n": self.n, "r": self.r, "p": self.p, "dklen": self.dklen, "salt_bytes": self.salt_bytes}


class CredentialKdf:
    algorithm = "scrypt"

    def __init__(self, params: ScryptParameters | None = None) -> None:
        self.params = params or ScryptParameters()

    def hash_password(self, password: str) -> tuple[bytes, bytes, dict[str, int]]:
        self.validate_password(password)
        salt = secrets.token_bytes(self.params.salt_bytes)
        digest = self._derive(password, salt, self.params.to_dict())
        return digest, salt, self.params.to_dict()

    def verify(self, password: str, *, expected_hash: bytes, salt: bytes, params: dict[str, int]) -> bool:
        try:
            candidate = self._derive(password, salt, params)
        except (TypeError, ValueError, MemoryError):
            return False
        return hmac.compare_digest(candidate, expected_hash)

    def needs_rehash(self, *, algorithm: str, version: int, params: dict[str, int]) -> bool:
        return algorithm != self.algorithm or version != self.params.version or params != self.params.to_dict()

    @staticmethod
    def validate_password(password: str) -> None:
        if not isinstance(password, str):
            raise ValueError("password must be text")
        if len(password) < 12:
            raise ValueError("password must contain at least 12 characters")
        if len(password) > 128:
            raise ValueError("password exceeds the 128-character local limit")
        if not password.strip():
            raise ValueError("password cannot be blank")

    @staticmethod
    def _derive(password: str, salt: bytes, params: dict[str, int]) -> bytes:
        n = int(params["n"])
        r = int(params["r"])
        p = int(params["p"])
        dklen = int(params["dklen"])
        if n < 2**14 or n & (n - 1):
            raise ValueError("invalid scrypt n")
        if r < 8 or p < 1 or dklen < 32:
            raise ValueError("invalid scrypt parameters")
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=dklen)
