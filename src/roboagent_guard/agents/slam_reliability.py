from __future__ import annotations

from roboagent_guard.models.common import ComponentResult, Violation
from roboagent_guard.models.decisions import Decision, RiskLevel, Surface, risk_level
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.scoring import clamp, inverse_ratio, ratio
from roboagent_guard.policies.thresholds import (
    HIGH_BLUR_SCORE,
    HIGH_SPEED_MPS,
    LOW_LIGHT_LUX,
    MAX_CRITICAL_SENSOR_AGE_MS,
    MAX_SENSOR_AGE_MS,
    MIN_LOCALIZATION_CONFIDENCE,
    MIN_SLAM_INLIER_RATIO,
)


class SlamReliabilityAgent:
    name = "slam_reliability"

    def evaluate(self, request: EvaluationRequest) -> ComponentResult:
        p = request.perception
        state = request.robot_state
        action = request.action
        violations: list[Violation] = []
        controls: list[str] = []

        if p.slam_inlier_ratio < MIN_SLAM_INLIER_RATIO:
            violations.append(
                Violation(
                    code=codes.SLAM_INLIER_RATIO_CRITICAL,
                    message="SLAM inlier ratio is below critical threshold.",
                    observed=p.slam_inlier_ratio,
                    threshold=MIN_SLAM_INLIER_RATIO,
                )
            )
            controls += ["stop", "relocalize"]
        if p.localization_confidence < MIN_LOCALIZATION_CONFIDENCE:
            violations.append(
                Violation(
                    code=codes.LOCALIZATION_CONFIDENCE_CRITICAL,
                    message="Localization confidence is below critical threshold.",
                    observed=p.localization_confidence,
                    threshold=MIN_LOCALIZATION_CONFIDENCE,
                )
            )
            controls += ["stop", "relocalize"]
        if p.sensor_age_ms > MAX_CRITICAL_SENSOR_AGE_MS:
            violations.append(
                Violation(
                    code=codes.STALE_SENSOR_CRITICAL,
                    message="Sensor evidence is critically stale.",
                    observed=p.sensor_age_ms,
                    threshold=MAX_CRITICAL_SENSOR_AGE_MS,
                )
            )
            controls += ["fresh_state", "stop"]
        if (
            p.illumination_lux < LOW_LIGHT_LUX
            and p.blur_score > HIGH_BLUR_SCORE
            and action.linear_speed_mps > HIGH_SPEED_MPS
        ):
            violations.append(
                Violation(
                    code=codes.LOW_LIGHT_BLUR_HIGH_SPEED,
                    message="Low light, high blur, and high speed make localization unsafe.",
                    observed={
                        "illumination_lux": p.illumination_lux,
                        "blur_score": p.blur_score,
                        "linear_speed_mps": action.linear_speed_mps,
                    },
                    threshold={
                        "illumination_lux": LOW_LIGHT_LUX,
                        "blur_score": HIGH_BLUR_SCORE,
                        "linear_speed_mps": HIGH_SPEED_MPS,
                    },
                )
            )
            controls += ["slow_down", "relocalize"]

        score = clamp(
            0.25 * inverse_ratio(p.slam_inlier_ratio, 0.9)
            + 0.25 * inverse_ratio(p.localization_confidence, 0.95)
            + 0.15 * p.blur_score
            + 0.15 * inverse_ratio(p.illumination_lux, 150.0)
            + 0.10 * p.map_entropy
            + 0.10 * ratio(p.sensor_age_ms, MAX_SENSOR_AGE_MS)
        )
        if p.illumination_lux < LOW_LIGHT_LUX and action.linear_speed_mps > 0.25:
            score = clamp(score + 0.10)
            controls.append("reduce_speed_in_low_light")
        if state.surface == Surface.UNEVEN and p.blur_score > 0.5:
            score = clamp(score + 0.10)
            controls.append("stabilize_motion")
        if p.slam_inlier_ratio < 0.5 and p.map_entropy > 0.6:
            score = clamp(score + 0.10)
            controls.append("relocalize")

        level = risk_level(score)
        if any(
            v.code in {codes.SLAM_INLIER_RATIO_CRITICAL, codes.LOCALIZATION_CONFIDENCE_CRITICAL}
            for v in violations
        ):
            decision = Decision.MODIFY
            level = RiskLevel.CRITICAL
        elif any(v.code == codes.STALE_SENSOR_CRITICAL for v in violations):
            decision = Decision.REQUEST_HUMAN_APPROVAL
            level = RiskLevel.HIGH
        elif violations or score >= 0.65:
            decision = Decision.MODIFY
            controls = controls or ["slow_down", "relocalize"]
        elif score >= 0.35:
            decision = Decision.APPROVE_WITH_CONSTRAINTS
            controls = controls or ["limit_speed", "monitor_slam"]
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
                "illumination_lux": p.illumination_lux,
                "blur_score": p.blur_score,
                "slam_inlier_ratio": p.slam_inlier_ratio,
                "localization_confidence": p.localization_confidence,
                "map_entropy": p.map_entropy,
                "sensor_age_ms": p.sensor_age_ms,
            },
            reasons=self._reasons(decision),
        )

    @staticmethod
    def _reasons(decision: Decision) -> list[str]:
        return {
            Decision.APPROVE: ["SLAM reliability is high."],
            Decision.APPROVE_WITH_CONSTRAINTS: ["SLAM reliability is usable with constraints."],
            Decision.MODIFY: ["SLAM reliability requires a safer replacement action."],
            Decision.BLOCK: ["SLAM evidence is unsafe."],
            Decision.REQUEST_HUMAN_APPROVAL: ["Fresh perception evidence is required."],
        }[decision]
