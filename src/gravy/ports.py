"""Bounded, in-process review-port reservations."""

from __future__ import annotations

from threading import Lock


class PortPool:
    def __init__(self, first_port: int, last_port: int) -> None:
        if first_port <= 0 or last_port < first_port or last_port > 65535:
            raise ValueError("invalid bounded port range")
        self._ports = range(first_port, last_port + 1)
        self._reserved: set[int] = set()
        self._lock = Lock()

    @property
    def reserved(self) -> frozenset[int]:
        with self._lock:
            return frozenset(self._reserved)

    def reserve(self) -> int | None:
        with self._lock:
            for port in self._ports:
                if port not in self._reserved:
                    self._reserved.add(port)
                    return port
        return None

    def release(self, port: int) -> None:
        with self._lock:
            self._reserved.discard(port)
