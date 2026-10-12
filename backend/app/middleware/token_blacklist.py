import threading
import time


class TokenBlacklist:
    """In-memory store of revoked token IDs (JWT `jti`).

    Each entry is kept only until the token's own expiry (at most
    JWT_EXPIRE_HOURS after login); after that the JWT is rejected by its `exp`
    claim anyway, so the entry is dropped. Expired entries are removed lazily on
    access and by the periodic sweep started in main.py (purge_expired).

    The whole cache is never wiped at once: that would un-revoke tokens that
    were logged out recently but haven't expired yet.

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

    def purge_expired(self) -> int:
        """Remove entries whose token has expired. Returns how many were removed."""
        with self._lock:
            return self._purge_expired()

    def __len__(self) -> int:
        with self._lock:
            self._purge_expired()
            return len(self._entries)

    def _purge_expired(self) -> int:
        now = time.time()
        expired = [jti for jti, exp in self._entries.items() if exp <= now]

        for jti in expired:
            del self._entries[jti]

        return len(expired)


token_blacklist = TokenBlacklist()
