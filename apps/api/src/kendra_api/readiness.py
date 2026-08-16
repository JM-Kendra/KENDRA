"""Secret-safe readiness contracts shared by infrastructure adapters."""

from dataclasses import dataclass
from typing import Literal, Protocol


ReadinessCode = Literal["reachable", "unreachable", "available", "unavailable"]


@dataclass(frozen=True, slots=True)
class ProbeResult:
    service: str
    ready: bool
    code: ReadinessCode


class ReadinessProbe(Protocol):
    name: str

    async def check(self) -> ProbeResult:
        """Return a sanitized readiness result without exception details."""
