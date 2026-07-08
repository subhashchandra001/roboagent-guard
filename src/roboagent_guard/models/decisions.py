from enum import StrEnum


class Decision(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_CONSTRAINTS = "approve_with_constraints"
    MODIFY = "modify"
    BLOCK = "block"
    REQUEST_HUMAN_APPROVAL = "request_human_approval"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(StrEnum):
    NAVIGATE = "navigate"
    STOP = "stop"
    SLOW_DOWN = "slow_down"
    ROTATE = "rotate"
    RELOCALIZE = "relocalize"
    SAVE_MAP = "save_map"
    UPDATE_MAP = "update_map"
    SHARE_SENSOR_SUMMARY = "share_sensor_summary"
    SHARE_RAW_CAMERA = "share_raw_camera"
    DISABLE_STORAGE = "disable_storage"
    RETURN_TO_BASE = "return_to_base"


class Surface(StrEnum):
    SMOOTH = "smooth"
    UNEVEN = "uneven"
    SLIPPERY = "slippery"


class CallerRole(StrEnum):
    PLANNER = "planner"
    MAPPING_AGENT = "mapping_agent"
    PRIVACY_AGENT = "privacy_agent"
    SUPERVISOR = "supervisor"
    OBSERVER = "observer"
    ROBOT = "robot"
    MALICIOUS_AGENT = "malicious_agent"


DECISION_RANK: dict[Decision, int] = {
    Decision.APPROVE: 0,
    Decision.APPROVE_WITH_CONSTRAINTS: 1,
    Decision.REQUEST_HUMAN_APPROVAL: 2,
    Decision.MODIFY: 3,
    Decision.BLOCK: 4,
}


def risk_level(score: float) -> RiskLevel:
    if score >= 0.85:
        return RiskLevel.CRITICAL
    if score >= 0.65:
        return RiskLevel.HIGH
    if score >= 0.35:
        return RiskLevel.MODERATE
    return RiskLevel.LOW
