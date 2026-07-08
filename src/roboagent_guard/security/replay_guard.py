from __future__ import annotations

from dataclasses import dataclass, field

from roboagent_guard.audit.hashing import sha256_digest
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes


@dataclass
class ReplayResult:
    passed: bool
    replay_detected: bool
    violations: list[str] = field(default_factory=list)


class ReplayGuard:
    def __init__(self) -> None:
        self.request_ids: set[str] = set()
        self.nonces: set[str] = set()
        self.blocked_action_digests: set[str] = set()

    def check(self, request: EvaluationRequest) -> ReplayResult:
        violations: list[str] = []
        if request.request_id in self.request_ids:
            violations.append(codes.REPLAY_REQUEST)
        if request.nonce in self.nonces:
            violations.append(codes.REPLAY_NONCE)
        if self.action_digest(request) in self.blocked_action_digests:
            violations.append(codes.REPLAY_BLOCKED_ACTION)
        return ReplayResult(
            passed=not violations,
            replay_detected=bool(violations),
            violations=violations,
        )

    def record(self, request: EvaluationRequest, blocked: bool) -> None:
        self.request_ids.add(request.request_id)
        self.nonces.add(request.nonce)
        if blocked:
            self.blocked_action_digests.add(self.action_digest(request))

    @staticmethod
    def action_digest(request: EvaluationRequest) -> str:
        return sha256_digest(
            {
                "caller": request.caller.model_dump(mode="json"),
                "action": request.action.model_dump(mode="json"),
                "robot_state": request.robot_state.model_dump(mode="json"),
                "perception": request.perception.model_dump(mode="json"),
                "privacy": request.privacy.model_dump(mode="json"),
            }
        )
