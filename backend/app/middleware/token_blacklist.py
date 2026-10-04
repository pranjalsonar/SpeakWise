import threading
import time


class TokenBlacklist:
    """In-memory store of revoked token IDs (JWT `jti`).

    Each entry is kept only until the token's own expiry; after that the JWT
    is rejected by its `exp` claim anyway, so the entry is dropped.

    Limitations: entries live in this process only. They are lost on restart
    and not shared between multiple workers/servers. Swap for Redis
    (SET jti EX <seconds>) when running more than one process.
    """

    def __init__(self) -> None:
        self._entries: dict[str, float] = {}  # jti -> expiry (unix seconds)
        self._lock = threading.Lock()

    def add(self, jti: str, expires_at: float) -> None:
        with self._lock:
            self._purge_expired()
            self._entries[jti] = expires_at

    def contains(self, jti: str) -> bool:
        with self._lock:
            expires_at = self._entries.get(jti)

            if expires_at is None:
                return False

            if expires_at <= time.time():
                del self._entries[jti]
                return False

            return True

    def __len__(self) -> int:
        with self._lock:
            self._purge_expired()
            return len(self._entries)

    def _purge_expired(self) -> None:
        now = time.time()

        for jti in [jti for jti, exp in self._entries.items() if exp <= now]:
            del self._entries[jti]


token_blacklist = TokenBlacklist()
