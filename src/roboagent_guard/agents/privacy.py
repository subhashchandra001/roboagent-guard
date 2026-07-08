from __future__ import annotations

from roboagent_guard.models.common import ComponentResult, Violation
from roboagent_guard.models.decisions import Decision, RiskLevel, risk_level
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.policies import hard_constraints as codes
from roboagent_guard.policies.scoring import clamp
from roboagent_guard.policies.thresholds import MAX_RETENTION_SECONDS


class PrivacyAgent:
    name = "privacy"

    def evaluate(self, request: EvaluationRequest) -> ComponentResult:
        action = request.action
        privacy = request.privacy
        violations: list[Violation] = []
        controls: list[str] = []

        if action.share_raw_camera and not privacy.recipient_authorized:
            violations.append(
                Violation(
                    code=codes.RAW_CAMERA_UNAUTHORIZED_RECIPIENT,
                    message="Raw camera sharing requires an authorized recipient.",
                    observed=privacy.recipient_authorized,
                    threshold=True,
                )
            )
            controls += ["prohibit_sharing", "authorized_recipient_only"]
        if privacy.private_zone and privacy.person_detected and action.save_map:
            violations.append(
                Violation(
                    code=codes.PRIVATE_ZONE_MAP_SAVE,
                    message="Map saving is unsafe around people in a private zone.",
                    observed=True,
                    threshold=False,
                )
            )
            controls += ["disable_map_save"]
        if (
            privacy.face_data_present
            and not privacy.privacy_filter_applied
            and action.share_raw_camera
        ):
            violations.append(
                Violation(
                    code=codes.FACE_DATA_WITHOUT_FILTER,
                    message="Face data cannot be shared without a privacy filter.",
                    observed=False,
                    threshold=True,
                )
            )
            controls += ["redact_faces", "privacy_filtered"]
        if privacy.retention_seconds > MAX_RETENTION_SECONDS:
            violations.append(
                Violation(
                    code=codes.RETENTION_TOO_LONG,
                    message="Requested retention exceeds policy maximum.",
                    observed=privacy.retention_seconds,
                    threshold=MAX_RETENTION_SECONDS,
                )
            )
            controls += ["reduce_retention"]
        if privacy.private_zone and action.store_sensor_data:
            violations.append(
                Violation(
                    code=codes.PRIVATE_ZONE_RAW_STORAGE,
                    message="Raw sensor storage is blocked in private zones.",
                    observed=True,
                    threshold=False,
                )
            )
            controls += ["disable_raw_storage"]

        score = clamp(
            (0.25 if privacy.person_detected else 0.0)
            + (0.20 if privacy.private_zone else 0.0)
            + (0.20 if privacy.face_data_present else 0.0)
            + (0.20 if action.share_raw_camera else 0.0)
            + (0.10 if action.store_sensor_data else 0.0)
            + (0.05 if action.save_map else 0.0)
        )
        level = risk_level(score)

        hard_block_codes = {
            codes.RAW_CAMERA_UNAUTHORIZED_RECIPIENT,
            codes.FACE_DATA_WITHOUT_FILTER,
            codes.PRIVATE_ZONE_RAW_STORAGE,
        }
        if any(v.code in hard_block_codes for v in violations):
            decision = Decision.BLOCK
            level = RiskLevel.CRITICAL
            score = max(score, 0.9)
        elif violations:
            decision = Decision.MODIFY
            score = max(score, 0.55)
        elif privacy.person_detected or privacy.private_zone:
            decision = Decision.APPROVE_WITH_CONSTRAINTS
            controls = ["privacy_filtered", "no_raw_storage"]
            score = max(score, 0.35)
            level = risk_level(score)
        else:
            decision = Decision.APPROVE

        return ComponentResult(
            name=self.name,
            score=clamp(score),
            level=level,
            decision=decision,
            violations=violations,
            recommended_controls=sorted(set(controls)),
            evidence={
                "person_detected": privacy.person_detected,
                "private_zone": privacy.private_zone,
                "face_data_present": privacy.face_data_present,
                "share_raw_camera": action.share_raw_camera,
                "save_map": action.save_map,
                "store_sensor_data": action.store_sensor_data,
                "retention_seconds": privacy.retention_seconds,
            },
            reasons=self._reasons(decision),
        )

    @staticmethod
    def _reasons(decision: Decision) -> list[str]:
        return {
            Decision.APPROVE: ["No privacy-sensitive collection was requested."],
            Decision.APPROVE_WITH_CONSTRAINTS: ["Privacy context requires conservative handling."],
            Decision.MODIFY: ["Privacy controls must be added before execution."],
            Decision.BLOCK: ["A hard privacy constraint was triggered."],
            Decision.REQUEST_HUMAN_APPROVAL: ["Privacy review is required."],
        }[decision]
