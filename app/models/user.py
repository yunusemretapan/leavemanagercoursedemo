from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"


ROLE_LABELS_TR = {Role.EMPLOYEE: "Çalışan", Role.MANAGER: "Yönetici"}


@dataclass(frozen=True)
class User:
    id: int
    username: str
    full_name: str
    role: Role
    manager_id: int | None
