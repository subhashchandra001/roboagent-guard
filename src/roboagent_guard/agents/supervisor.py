from __future__ import annotations

from dataclasses import dataclass

from roboagent_guard.models.common import ComponentResult
from roboagent_guard.models.decisions import (
    DECISION_RANK,
    ActionType,
    Decision,
    RiskLevel,
    risk_level,
)
from roboagent_guard.models.requests import Action, EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.scoring import clamp
from roboagent_guard.policies.thresholds import MAX_RETENTION_SECONDS


@dataclass
class SupervisorDecision:
    decision: Decision
    risk_level: RiskLevel
    risk_score: float
    recommended_action: Action
    constraints: list[str]
    reasons: list[str]
    violation_codes: list[str]
    human_approval_required: bool


class SupervisorAgent:
    name = "supervisor"

    def decide(
        self,
        request: EvaluationRequest,
        component_results: dict[str, ComponentResult],
        freshness_passed: bool,
        replay_detected: bool,
        token_violations: list[str],
    ) -> SupervisorDecision:
        violation_codes = [
            violation.code
            for result in component_results.values()
            for violation in result.violations
        ] + token_violations
        constraints = sorted(
            {
                control
                for result in component_results.values()
                for control in result.recommended_controls
            }
        )
        reasons = [reason for result in component_results.values() for reason in result.reasons]

        decisions = [Decision(result.decision) for result in component_results.values()]
        decision = max(decisions, key=lambda item: DECISION_RANK[item])
        if replay_detected:
            decision = Decision.BLOCK
            violation_codes.append(codes.REPLAY_REQUEST)
            reasons.append("Replay guard detected duplicate or blocked evidence.")
        if token_violations:
            decision = Decision.BLOCK
            reasons.append("Approval token validation failed.")
        if not freshness_passed and decision != Decision.BLOCK:
            decision = Decision.REQUEST_HUMAN_APPROVAL
            reasons.append("Fresh perception evidence is required before execution.")

        if any(code in self._hard_block_codes() for code in violation_codes):
            decision = Decision.BLOCK
        elif (
            any(code in self._slam_modify_codes() for code in violation_codes)
            and decision != Decision.BLOCK
        ):
            decision = Decision.MODIFY

        risk_score = clamp(max(result.score for result in component_results.values()))
        if decision == Decision.BLOCK:
            risk_score = max(risk_score, 0.9)
        elif decision == Decision.MODIFY:
            risk_score = max(risk_score, 0.65)
        elif decision == Decision.APPROVE_WITH_CONSTRAINTS:
            risk_score = max(risk_score, 0.35)

        return SupervisorDecision(
            decision=decision,
            risk_level=RiskLevel.CRITICAL if decision == Decision.BLOCK else risk_level(risk_score),
            risk_score=clamp(risk_score),
            recommended_action=self._recommended_action(request, decision, constraints),
            constraints=constraints,
            reasons=self._unique(reasons),
            violation_codes=self._unique(violation_codes),
            human_approval_required=decision == Decision.REQUEST_HUMAN_APPROVAL
            or "request_human_approval" in constraints,
        )

    @staticmethod
    def _hard_block_codes() -> set[str]:
        return {
            codes.UNAUTHORIZED_ACTION,
            codes.UNAUTHORIZED_RAW_CAMERA,
            codes.UNAUTHORIZED_MAP_SAVE,
            codes.UNAUTHORIZED_STORAGE,
            codes.FORGED_APPROVAL_TOKEN,
            codes.REUSED_APPROVAL_TOKEN,
            codes.OBSTACLE_COLLISION_IMMINENT,
            codes.LOW_BATTERY_NAVIGATION,
            codes.RAW_CAMERA_UNAUTHORIZED_RECIPIENT,
            codes.FACE_DATA_WITHOUT_FILTER,
            codes.PRIVATE_ZONE_RAW_STORAGE,
            codes.REPLAY_REQUEST,
            codes.REPLAY_NONCE,
            codes.REPLAY_BLOCKED_ACTION,
        }

    @staticmethod
    def _slam_modify_codes() -> set[str]:
        return {
            codes.SLAM_INLIER_RATIO_CRITICAL,
            codes.LOCALIZATION_CONFIDENCE_CRITICAL,
            codes.LOW_LIGHT_BLUR_HIGH_SPEED,
            codes.OBSTACLE_TOO_CLOSE_FOR_SPEED,
        }

    @staticmethod
    def _recommended_action(
        request: EvaluationRequest, decision: Decision, controls: list[str]
    ) -> Action:
        original = request.action
        if decision == Decision.BLOCK:
            return Action(
                type=ActionType.STOP,
                linear_speed_mps=0.0,
                angular_speed_rps=0.0,
                save_map=False,
                share_raw_camera=False,
                store_sensor_data=False,
                recipient_id=None,
            )
        if "relocalize" in controls and ("stop" in controls or decision == Decision.MODIFY):
            return Action(
                type=ActionType.RELOCALIZE,
                linear_speed_mps=0.0,
                angular_speed_rps=0.0,
                save_map=False,
                share_raw_camera=False,
                store_sensor_data=False,
                recipient_id=None,
            )
        if decision == Decision.MODIFY or "slow_down" in controls:
            return Action(
                type=ActionType.SLOW_DOWN,
                linear_speed_mps=min(original.linear_speed_mps, 0.15),
                angular_speed_rps=0.0,
                target=original.target,
                save_map=False if "disable_map_save" in controls else original.save_map,
                share_raw_camera=False,
                store_sensor_data=False,
                recipient_id=None,
            )
        if "reduce_retention" in controls:
            _ = MAX_RETENTION_SECONDS
        return original.model_copy(deep=True)

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
