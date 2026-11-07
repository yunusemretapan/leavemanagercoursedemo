"""The six fictional demo users (spec 0002 R-1, R-3)."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from app.business.passwords import PRODUCTION_SCRYPT, ScryptParams, check_policy, hash_password
from app.data.database import Database
from app.data.users import UserRepository
from app.models.errors import ConfigurationError
from app.models.user import Role


@dataclass(frozen=True)
class DemoUser:
    username: str
    full_name: str
    role: Role
    manager_username: str | None


# Managers before their reports: each row's manager is already inserted.
DEMO_USERS: tuple[DemoUser, ...] = (
    DemoUser("ayse.yilmaz", "Ayşe Yılmaz", Role.MANAGER, None),
    DemoUser("mehmet.kaya", "Mehmet Kaya", Role.MANAGER, "ayse.yilmaz"),
    DemoUser("ali.demir", "Ali Demir", Role.EMPLOYEE, "ayse.yilmaz"),
    DemoUser("zeynep.sahin", "Zeynep Şahin", Role.EMPLOYEE, "ayse.yilmaz"),
    DemoUser("can.ozturk", "Can Öztürk", Role.EMPLOYEE, "mehmet.kaya"),
    DemoUser("elif.arslan", "Elif Arslan", Role.EMPLOYEE, "mehmet.kaya"),
)

# scrypt (N=2^17) takes ~1.3 s and ~128 MiB per hash; hashlib releases the GIL while hashing.
SEED_WORKERS = 3


def validate_demo_password(password: str | None) -> str:
    """The demo password, or ConfigurationError with the reasons (never the password itself)."""
    if not password:
        raise ConfigurationError(
            "DEMO_PASSWORD tanımlı değil. Ortam değişkeni veya .env dosyasıyla verin (README.md)."
        )
    reasons: list[str] = []
    for demo in DEMO_USERS:
        for violation in check_policy(password, demo.username):
            if violation not in reasons:
                reasons.append(violation)
    if reasons:
        raise ConfigurationError("DEMO_PASSWORD parola politikasına uymuyor: " + " ".join(reasons))
    return password


def seed_demo_users(db: Database, password: str, params: ScryptParams = PRODUCTION_SCRYPT) -> int:
    """Insert the demo users into an empty users table; return how many were inserted."""
    with db.connect() as conn:
        if UserRepository(conn).count() > 0:
            return 0
    with ThreadPoolExecutor(max_workers=SEED_WORKERS) as pool:
        hashes = list(pool.map(lambda _: hash_password(password, params), DEMO_USERS))
    ids: dict[str, int] = {}
    with db.connect() as conn:
        users = UserRepository(conn)
        for demo, password_hash in zip(DEMO_USERS, hashes, strict=True):
            manager_id = ids[demo.manager_username] if demo.manager_username else None
            ids[demo.username] = users.insert(
                demo.username, demo.full_name, demo.role, manager_id, password_hash
            )
    return len(DEMO_USERS)
