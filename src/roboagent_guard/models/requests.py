from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from roboagent_guard.models.common import FiniteFloat, StrictBaseModel, Target
from roboagent_guard.models.decisions import ActionType, CallerRole, Surface
from roboagent_guard.security.input_safety import reject_image_payloads


class Caller(StrictBaseModel):
    id: str = Field(min_length=1, max_length=120)
    role: CallerRole
    authorized_actions: list[ActionType] = Field(default_factory=list, max_length=20)


class Action(StrictBaseModel):
    type: ActionType
    linear_speed_mps: FiniteFloat = Field(default=0.0, ge=0.0, le=2.0)
    angular_speed_rps: FiniteFloat = Field(default=0.0, ge=-3.14, le=3.14)
    target: Target | None = None
    save_map: bool = False
    share_raw_camera: bool = False
    store_sensor_data: bool = False
    recipient_id: str | None = Field(default=None, max_length=120)


class RobotState(StrictBaseModel):
    battery_percent: FiniteFloat = Field(ge=0.0, le=100.0)
    emergency_stop_available: bool
    nearest_obstacle_m: FiniteFloat = Field(ge=0.0, le=1000.0)
    surface: Surface
    pitch_disturbance_deg: FiniteFloat = Field(ge=-90.0, le=90.0)
    roll_disturbance_deg: FiniteFloat = Field(ge=-90.0, le=90.0)


class Perception(StrictBaseModel):
    illumination_lux: FiniteFloat = Field(ge=0.0, le=200000.0)
    blur_score: FiniteFloat = Field(ge=0.0, le=1.0)
    slam_inlier_ratio: FiniteFloat = Field(ge=0.0, le=1.0)
    localization_confidence: FiniteFloat = Field(ge=0.0, le=1.0)
    map_entropy: FiniteFloat = Field(ge=0.0, le=1.0)
    sensor_age_ms: int = Field(ge=0, le=600000)


class PrivacyContext(StrictBaseModel):
    person_detected: bool
    private_zone: bool
    face_data_present: bool
    privacy_filter_applied: bool
    recipient_authorized: bool
    retention_seconds: int = Field(ge=0, le=86400)


class Approval(StrictBaseModel):
    token: str | None = Field(default=None, max_length=160)


class EvaluationRequest(StrictBaseModel):
    request_id: str = Field(min_length=1, max_length=120)
    nonce: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    evaluation_time: datetime | None = None
    caller: Caller
    action: Action
    robot_state: RobotState
    perception: Perception
    privacy: PrivacyContext
    approval: Approval = Field(default_factory=Approval)
    simulation_seed: int = Field(default=42, ge=0, le=2_147_483_647)
    client_risk_score: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    safety_approved: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=20)

    @model_validator(mode="before")
    @classmethod
    def reject_embedded_image_payloads(cls, value: Any) -> Any:
        reject_image_payloads(value)
        return value

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone")
        return value

    @field_validator("evaluation_time")
    @classmethod
    def evaluation_time_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("evaluation_time must include timezone")
        return value


class BatchEvaluationRequest(StrictBaseModel):
    requests: list[EvaluationRequest] = Field(min_length=1, max_length=25)
