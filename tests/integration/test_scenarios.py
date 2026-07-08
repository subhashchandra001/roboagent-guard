from __future__ import annotations

import pytest

from roboagent_guard.models.decisions import Decision
from roboagent_guard.simulator.runner import run_named_scenario
from roboagent_guard.simulator.scenarios import list_scenarios, scenario_request


@pytest.mark.parametrize("item", list_scenarios(), ids=lambda item: item["name"])
def test_all_scenarios_expected(engine, item):
    response = run_named_scenario(engine, item["name"], scenario_request(item["name"], 42))
    assert response.decision == item["expected_decision"]


@pytest.mark.parametrize(
    "scenario",
    [
        "low_light_high_speed",
        "uneven_surface_high_blur",
        "slam_degradation",
        "hidden_low_slam_confidence",
    ],
)
def test_modify_scenarios_have_safe_replacement(engine, scenario):
    response = engine.evaluate(scenario_request(scenario, 42), audit=False)
    assert response.decision == Decision.MODIFY
    assert response.recommended_action.type in {"slow_down", "relocalize"}
    assert response.recommended_action.share_raw_camera is False


def test_private_zone_recording_variant_blocks(engine):
    req = scenario_request("person_in_private_zone", 42)
    req.request_id = "private-recording"
    req.nonce = "private-recording-nonce"
    req.action.store_sensor_data = True
    response = engine.evaluate(req, audit=False)
    assert response.decision == Decision.BLOCK
    assert "PRIVATE_ZONE_RAW_STORAGE" in response.violation_codes
