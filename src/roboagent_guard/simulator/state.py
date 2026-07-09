from __future__ import annotations

from pydantic import Field

from roboagent_guard.models.common import FiniteFloat, StrictBaseModel
from roboagent_guard.models.decisions import Surface
from roboagent_guard.models.requests import EvaluationRequest


class TwinState(StrictBaseModel):
    x: FiniteFloat = 0.0
    y: FiniteFloat = 0.0
    heading_rad: FiniteFloat = 0.0
    linear_speed_mps: FiniteFloat = 0.0
    angular_speed_rps: FiniteFloat = 0.0
    battery_percent: FiniteFloat = Field(ge=0.0, le=100.0)
    mapping_enabled: bool = False
    raw_storage_enabled: bool = False
    map_update_count: int = 0
    sensor_summary_shared: bool = False
    raw_camera_shared: bool = False
    last_recipient_id: str | None = None
    localization_mode: str = "tracking"
    person_detected: bool = False
    private_zone: bool = False
    surface: Surface = Surface.SMOOTH
    illumination_lux: FiniteFloat = 100.0
    slam_inlier_ratio: FiniteFloat = Field(ge=0.0, le=1.0)
    localization_confidence: FiniteFloat = Field(ge=0.0, le=1.0)


def state_from_request(request: EvaluationRequest) -> TwinState:
    return TwinState(
        battery_percent=request.robot_state.battery_percent,
        person_detected=request.privacy.person_detected,
        private_zone=request.privacy.private_zone,
        surface=request.robot_state.surface,
        illumination_lux=request.perception.illumination_lux,
        slam_inlier_ratio=request.perception.slam_inlier_ratio,
        localization_confidence=request.perception.localization_confidence,
    )
