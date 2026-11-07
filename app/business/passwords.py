"""Password policy and storage (spec 0002 R-2, R-4; ADR 0001).

Policy follows NIST SP 800-63B: length and a blocklist, no composition rules.
Storage: scrypt with a per-user random salt; verification compares in constant time.
"""

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from functools import cache
from pathlib import Path

MIN_LENGTH = 12
MAX_LENGTH = 128
COMMON_PASSWORDS_FILE = Path(__file__).resolve().parent / "common_passwords.txt"
SALT_BYTES = 16
KEY_BYTES = 32


@dataclass(frozen=True)
class ScryptParams:
    """OWASP Password Storage Cheat Sheet scrypt baseline: N=2^17, r=8, p=1."""

    n: int = 2**17
    r: int = 8
    p: int = 1

    @property
    def maxmem(self) -> int:
        # scrypt needs ~128 * r * N bytes; leave headroom so OpenSSL never refuses.
        return 2 * 128 * self.r * self.n + 1024 * 1024


PRODUCTION_SCRYPT = ScryptParams()


@cache
def common_passwords() -> frozenset[str]:
    lines = COMMON_PASSWORDS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip().lower() for line in lines if line.strip())


def check_policy(password: str, username: str | None = None) -> list[str]:
    """Return the policy violations in Turkish (empty list = acceptable). Never echoes it."""
    violations: list[str] = []
    if len(password) < MIN_LENGTH:
        violations.append(f"Parola en az {MIN_LENGTH} karakter olmalı.")
    if len(password) > MAX_LENGTH:
        violations.append(f"Parola en fazla {MAX_LENGTH} karakter olabilir.")
    if username is not None and password.casefold() == username.strip().casefold():
        violations.append("Parola kullanıcı adıyla aynı olamaz.")
    if password.lower() in common_passwords():
        violations.append("Parola çok yaygın kullanılan parolalar listesinde.")
    return violations


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _derive(password: str, salt: bytes, params: ScryptParams) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=params.n,
        r=params.r,
        p=params.p,
        maxmem=params.maxmem,
        dklen=KEY_BYTES,
    )


def hash_password(password: str, params: ScryptParams = PRODUCTION_SCRYPT) -> str:
    """Stored form: scrypt$<n>$<r>$<p>$<salt b64>$<key b64>."""
    salt = secrets.token_bytes(SALT_BYTES)
    key = _derive(password, salt, params)
    return f"scrypt${params.n}${params.r}${params.p}${_b64(salt)}${_b64(key)}"


def verify_password(password: str, stored: str) -> bool:
    """Recompute with the stored parameters and compare in constant time."""
    scheme, n, r, p, salt_b64, key_b64 = stored.split("$")
    if scheme != "scrypt":
        return False
    params = ScryptParams(n=int(n), r=int(r), p=int(p))
    expected = base64.b64decode(key_b64)
    actual = _derive(password, base64.b64decode(salt_b64), params)
    return hmac.compare_digest(actual, expected)


def dummy_hash(params: ScryptParams = PRODUCTION_SCRYPT) -> str:
    """A well-formed hash no password matches: verifying against it costs the same as a real one,
    so an unknown username takes as long as a wrong password (spec 0002 R-6)."""
    salt = secrets.token_bytes(SALT_BYTES)
    key = secrets.token_bytes(KEY_BYTES)
    return f"scrypt${params.n}${params.r}${params.p}${_b64(salt)}${_b64(key)}"
