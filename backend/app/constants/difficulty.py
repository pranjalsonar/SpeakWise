from enum import IntEnum


class Difficulty(IntEnum):
    """Topic difficulty, stored as topics.difficulty (1-3)."""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3

    @property
    def label(self) -> str:
        return self.name.capitalize()

    @classmethod
    def from_label(cls, label: str) -> "Difficulty":
        return cls[label.strip().upper()]
