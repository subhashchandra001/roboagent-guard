from __future__ import annotations

from typing import Any

from pydantic import Field

from roboagent_guard.models.common import ComponentResult, FiniteFloat, StrictBaseModel
from roboagent_guard.models.decisions import Decision, RiskLevel
from roboagent_guard.models.requests import Action


class DigitalTwinResult(StrictBaseModel):
    previous_state: dict[str, Any]
    resulting_state: dict[str, Any]
    action_applied: bool


class EvaluationResponse(StrictBaseModel):
    evaluation_id: str
    request_id: str
    decision: Decision
    risk_level: RiskLevel
    risk_score: FiniteFloat = Field(ge=0.0, le=1.0)
    slam_risk_score: FiniteFloat = Field(ge=0.0, le=1.0)
    privacy_risk_score: FiniteFloat = Field(ge=0.0, le=1.0)
    authorization_passed: bool
    freshness_passed: bool
    replay_detected: bool
    human_approval_required: bool
    recommended_action: Action
    constraints: list[str]
    reasons: list[str]
    violation_codes: list[str]
    component_results: dict[str, ComponentResult]
    digital_twin: DigitalTwinResult
    policy_version: str
    trace_hash: str


class BatchEvaluationResponse(StrictBaseModel):
    results: list[EvaluationResponse]


class ScenarioSummary(StrictBaseModel):
    name: str
    expected_decision: str
    description: str
