from dataclasses import dataclass
from typing import Protocol
import math

from .schema import require


class Hardware(Protocol):
    def stop(self) -> None: ...
    def estop_active(self) -> bool: ...
    def command(self, steering: float, duty: float) -> None: ...


class MockHardware:
    def __init__(self):
        self.commands = []
        self.stopped = True
        self.estop = False

    def command(self, steering: float, duty: float) -> None:
        self.commands.append((steering, duty))
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True

    def estop_active(self) -> bool:
        return self.estop


@dataclass(frozen=True)
class Clock:
    duration_s: float
    steering: float

    def command(self, elapsed_s: float) -> float:
        require(math.isfinite(self.duration_s) and self.duration_s > 0 and 35 <= self.steering <= 105, "Invalid timed-turn parameters")
        require(math.isfinite(elapsed_s) and elapsed_s >= 0, "Invalid elapsed time")
        return self.steering if elapsed_s < self.duration_s else 75.0


@dataclass(frozen=True)
class Compass:
    target_deg: float
    kp: float
    polarity: int
    tolerance_deg: float

    def command(self, measured_heading_deg: float) -> float:
        require(self.polarity in (-1, 1) and self.kp > 0 and self.tolerance_deg >= 0 and all(math.isfinite(v) for v in (self.target_deg, self.kp, self.tolerance_deg, measured_heading_deg)), "Invalid feedback parameters")
        error = (self.target_deg - measured_heading_deg + 180) % 360 - 180
        return 75.0 if abs(error) <= self.tolerance_deg else min(105.0, max(35.0, 75 + self.polarity * self.kp * error))
