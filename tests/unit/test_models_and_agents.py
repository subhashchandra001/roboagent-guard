from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from roboagent_guard.agents.authorization import AuthorizationAgent
from roboagent_guard.agents.physical_risk import PhysicalRiskAgent
from roboagent_guard.agents.privacy import PrivacyAgent
from roboagent_guard.agents.slam_reliability import SlamReliabilityAgent
from roboagent_guard.models.decisions import ActionType, CallerRole, Decision
from roboagent_guard.simulator.scenarios import scenario_request


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("robot_state", "nearest_obstacle_m"), -1),
        (("perception", "blur_score"), 2),
        (("perception", "slam_inlier_ratio"), math.nan),
        (("perception", "localization_confidence"), math.inf),
        (("action", "linear_speed_mps"), -0.1),
        (("privacy", "retention_seconds"), 90000),
        (("caller", "id"), "x" * 200),
        (("action", "type"), "fly"),
        (("robot_state", "battery_percent"), 101),
        (("perception", "sensor_age_ms"), -1),
    ],
)
def test_request_validation_rejects_invalid_values(path, value):
    data = scenario_request("normal_navigation", 42).model_dump(mode="json")
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        scenario_request("normal_navigation", 42).model_validate(data)


@pytest.mark.parametrize(
    ("scenario", "agent_cls", "expected"),
    [
        ("normal_navigation", AuthorizationAgent, Decision.APPROVE),
        ("combined_safety_privacy_crisis", AuthorizationAgent, Decision.BLOCK),
        ("normal_navigation", PhysicalRiskAgent, Decision.APPROVE),
        ("slam_degradation", SlamReliabilityAgent, Decision.MODIFY),
        ("unauthorized_camera_request", PrivacyAgent, Decision.BLOCK),
        ("person_in_private_zone", PrivacyAgent, Decision.APPROVE_WITH_CONSTRAINTS),
    ],
)
def test_component_agents(scenario, agent_cls, expected):
    result = agent_cls().evaluate(scenario_request(scenario, 42))
    assert result.decision == expected
    assert 0.0 <= result.score <= 1.0


def test_client_risk_score_is_ignored(engine):
    req = scenario_request("hidden_low_slam_confidence", 42)
    req.client_risk_score = 0.0
    req.safety_approved = True
    response = engine.evaluate(req, audit=False)
    assert response.decision == Decision.MODIFY
    assert "LOCALIZATION_CONFIDENCE_CRITICAL" in response.violation_codes


def test_blocked_action_does_not_change_twin_state(engine):
    response = engine.evaluate(scenario_request("combined_safety_privacy_crisis", 42), audit=False)
    assert response.decision == Decision.BLOCK
    assert response.digital_twin.action_applied is False
    assert response.digital_twin.previous_state == response.digital_twin.resulting_state


def test_modified_action_applies_replacement(engine):
    response = engine.evaluate(scenario_request("slam_degradation", 42), audit=False)
    assert response.decision == Decision.MODIFY
    assert response.recommended_action.type == "relocalize"
    assert response.digital_twin.resulting_state["localization_mode"] == "relocalized"


@pytest.mark.parametrize(
    ("action_type", "role", "caller_id", "authorized_actions", "field", "expected"),
    [
        (
            ActionType.ROTATE,
            CallerRole.PLANNER,
            "planner-agent-01",
            [ActionType.ROTATE],
            "heading_rad",
            0.5,
        ),
        (
            ActionType.UPDATE_MAP,
            CallerRole.MAPPING_AGENT,
            "mapping-agent-01",
            [ActionType.UPDATE_MAP],
            "map_update_count",
            1,
        ),
        (
            ActionType.SHARE_SENSOR_SUMMARY,
            CallerRole.PRIVACY_AGENT,
            "privacy-agent-01",
            [ActionType.SHARE_SENSOR_SUMMARY],
            "sensor_summary_shared",
            True,
        ),
    ],
)
def test_advertised_actions_have_twin_effect(
    engine, action_type, role, caller_id, authorized_actions, field, expected
):
    req = scenario_request("normal_navigation", 42)
    req.request_id = f"action-{action_type}"
    req.nonce = f"action-{action_type}-nonce"
    req.caller.id = caller_id
    req.caller.role = role
    req.caller.authorized_actions = authorized_actions
    req.action.type = action_type
    req.action.linear_speed_mps = 0.0
    req.action.angular_speed_rps = 0.5

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.APPROVE
    assert response.digital_twin.action_applied is True
    assert response.digital_twin.resulting_state[field] == expected
