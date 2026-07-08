from __future__ import annotations

from roboagent_guard.models.common import ComponentResult, Violation
from roboagent_guard.models.decisions import Decision, RiskLevel, Surface, risk_level
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.scoring import clamp, ratio
from roboagent_guard.policies.thresholds import (
    MAX_CRAWL_SPEED_MPS,
    MAX_UNEVEN_SPEED_MPS,
    MIN_BATTERY_NAV_PERCENT,
    MIN_OBSTACLE_BLOCK_M,
    MIN_OBSTACLE_CRAWL_M,
)


class PhysicalRiskAgent:
    name = "physical_risk"

    def evaluate(self, request: EvaluationRequest) -> ComponentResult:
        state = request.robot_state
        action = request.action
        violations: list[Violation] = []
        controls: list[str] = []

        if state.nearest_obstacle_m < MIN_OBSTACLE_BLOCK_M:
            violations.append(
                Violation(
                    code=codes.OBSTACLE_COLLISION_IMMINENT,
                    message="Obstacle clearance is below collision threshold.",
                    observed=state.nearest_obstacle_m,
                    threshold=MIN_OBSTACLE_BLOCK_M,
                )
            )
            controls += ["stop"]
        if (
            state.nearest_obstacle_m < MIN_OBSTACLE_CRAWL_M
            and action.linear_speed_mps > MAX_CRAWL_SPEED_MPS
        ):
            violations.append(
                Violation(
                    code=codes.OBSTACLE_TOO_CLOSE_FOR_SPEED,
                    message="Obstacle is too close for requested speed.",
                    observed=action.linear_speed_mps,
                    threshold=MAX_CRAWL_SPEED_MPS,
                )
            )
            controls += ["slow_down", "stop"]
        if state.surface == Surface.UNEVEN and action.linear_speed_mps > MAX_UNEVEN_SPEED_MPS:
            controls.append("slow_down")
        if state.battery_percent < MIN_BATTERY_NAV_PERCENT and action.type == "navigate":
            violations.append(
                Violation(
                    code=codes.LOW_BATTERY_NAVIGATION,
                    message="Battery is too low for navigation.",
                    observed=state.battery_percent,
                    threshold=MIN_BATTERY_NAV_PERCENT,
                )
            )
            controls += ["stop", "return_to_base"]

        obstacle_risk = clamp(1.0 - min(state.nearest_obstacle_m, 2.0) / 2.0)
        speed_risk = ratio(action.linear_speed_mps, 1.0)
        disturbance = max(abs(state.pitch_disturbance_deg), abs(state.roll_disturbance_deg))
        surface_risk = clamp(
            (0.25 if state.surface != Surface.SMOOTH else 0.0) + ratio(disturbance, 20.0) * 0.75
        )
        battery_risk = clamp(1.0 - state.battery_percent / 30.0)
        angular_risk = ratio(abs(action.angular_speed_rps), 1.5)
        score = clamp(
            0.30 * obstacle_risk
            + 0.25 * speed_risk
            + 0.20 * surface_risk
            + 0.15 * battery_risk
            + 0.10 * angular_risk
        )
        level = risk_level(score)

        if any(
            v.code in {codes.OBSTACLE_COLLISION_IMMINENT, codes.LOW_BATTERY_NAVIGATION}
            for v in violations
        ):
            decision = Decision.BLOCK
            level = RiskLevel.CRITICAL
        elif violations or score >= 0.65:
            decision = Decision.MODIFY
            controls = controls or ["slow_down"]
        elif score >= 0.35 or (state.surface == Surface.UNEVEN and action.linear_speed_mps > 0):
            decision = Decision.APPROVE_WITH_CONSTRAINTS
            controls = controls or ["limit_speed", "monitor_obstacle_clearance"]
        else:
            decision = Decision.APPROVE

        return ComponentResult(
            name=self.name,
            score=score,
            level=level,
            decision=decision,
            violations=violations,
            recommended_controls=sorted(set(controls)),
            evidence={
                "nearest_obstacle_m": state.nearest_obstacle_m,
                "linear_speed_mps": action.linear_speed_mps,
                "surface": state.surface,
                "battery_percent": state.battery_percent,
            },
            reasons=self._reasons(decision),
        )

    @staticmethod
    def _reasons(decision: Decision) -> list[str]:
        return {
            Decision.APPROVE: ["Obstacle clearance and motion risk are acceptable."],
            Decision.APPROVE_WITH_CONSTRAINTS: [
                "Physical risk is moderate; constraints are required."
            ],
            Decision.MODIFY: ["Physical risk is high enough to require a safer action."],
            Decision.BLOCK: ["A hard physical safety constraint was triggered."],
            Decision.REQUEST_HUMAN_APPROVAL: ["Physical risk requires human approval."],
        }[decision]
