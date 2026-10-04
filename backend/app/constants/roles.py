from enum import IntEnum


class RoleId(IntEnum):
    """Fixed role IDs seeded by the roles migration (55c0f98d2b01)."""

    ADMIN = 1
    USER = 2
