from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.thresholds import FRESHNESS_WINDOW_SECONDS, MAX_CRITICAL_SENSOR_AGE_MS


@dataclass
class FreshnessResult:
    passed: bool
    human_approval_required: bool
    violations: list[str] = field(default_factory=list)


class FreshnessGuard:
    def __init__(self, now: datetime | None = None) -> None:
        self.now = now

    def check(self, request: EvaluationRequest) -> FreshnessResult:
        now = self.now or datetime.now(UTC)
        age_seconds = abs((now - request.timestamp.astimezone(UTC)).total_seconds())
        violations: list[str] = []
        human = False
        if age_seconds > FRESHNESS_WINDOW_SECONDS:
            violations.append(codes.STALE_TIMESTAMP)
            human = True
        if request.perception.sensor_age_ms > MAX_CRITICAL_SENSOR_AGE_MS:
            violations.append(codes.STALE_SENSOR_CRITICAL)
            human = True
        return FreshnessResult(
            passed=not violations, human_approval_required=human, violations=violations
        )
