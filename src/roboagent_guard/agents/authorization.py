from __future__ import annotations

from roboagent_guard.models.common import ComponentResult, Violation
from roboagent_guard.models.decisions import Decision, RiskLevel
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.role_policy import (
    MAP_SAVE_ROLES,
    RAW_CAMERA_ROLES,
    STORAGE_ROLES,
    allowed_actions_for,
)


class AuthorizationAgent:
    name = "authorization"

    def evaluate(self, request: EvaluationRequest) -> ComponentResult:
        violations: list[Violation] = []
        role = request.caller.role
        action = request.action
        allowed_by_server = allowed_actions_for(role)

        if action.type not in allowed_by_server:
            violations.append(
                Violation(
                    code=codes.UNAUTHORIZED_ACTION,
                    message="Caller role is not authorized for the requested action.",
                    observed=action.type,
                    threshold=sorted(allowed_by_server),
                )
            )
        if action.type not in request.caller.authorized_actions and role.name != "SUPERVISOR":
            violations.append(
                Violation(
                    code=codes.UNAUTHORIZED_ACTION,
                    message="Caller self-asserted authorization omits the requested action.",
                    observed=action.type,
                    threshold=request.caller.authorized_actions,
                )
            )
        if action.share_raw_camera and role not in RAW_CAMERA_ROLES:
            violations.append(
                Violation(
                    code=codes.UNAUTHORIZED_RAW_CAMERA,
                    message="Caller role may not request raw camera sharing.",
                    observed=role,
                    threshold=sorted(RAW_CAMERA_ROLES),
                )
            )
        if action.save_map and role not in MAP_SAVE_ROLES:
            violations.append(
                Violation(
                    code=codes.UNAUTHORIZED_MAP_SAVE,
                    message="Caller role may not save maps.",
                    observed=role,
                    threshold=sorted(MAP_SAVE_ROLES),
                )
            )
        if action.store_sensor_data and role not in STORAGE_ROLES:
            violations.append(
                Violation(
                    code=codes.UNAUTHORIZED_STORAGE,
                    message="Caller role may not store sensor data.",
                    observed=role,
                    threshold=sorted(STORAGE_ROLES),
                )
            )

        score = 1.0 if violations else 0.0
        return ComponentResult(
            name=self.name,
            score=score,
            level=RiskLevel.CRITICAL if violations else RiskLevel.LOW,
            decision=Decision.BLOCK if violations else Decision.APPROVE,
            violations=violations,
            recommended_controls=["block"] if violations else [],
            evidence={"role": role, "action": action.type},
            reasons=["Authorization failed."] if violations else ["Caller is authorized."],
        )
