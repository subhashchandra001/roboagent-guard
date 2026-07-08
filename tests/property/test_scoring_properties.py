from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from roboagent_guard.agents.physical_risk import PhysicalRiskAgent
from roboagent_guard.agents.slam_reliability import SlamReliabilityAgent
from roboagent_guard.models.decisions import Decision
from roboagent_guard.policies.scoring import clamp
from roboagent_guard.simulator.scenarios import scenario_request


@given(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
def test_clamp_bounds(value):
    assert 0.0 <= clamp(value) <= 1.0


@given(st.floats(min_value=0.0, max_value=1.5), st.floats(min_value=0.2, max_value=3.0))
def test_physical_score_bounded(speed, obstacle):
    req = scenario_request("normal_navigation", 42)
    req.action.linear_speed_mps = speed
    req.robot_state.nearest_obstacle_m = obstacle
    result = PhysicalRiskAgent().evaluate(req)
    assert 0.0 <= result.score <= 1.0


@given(st.floats(min_value=0.0, max_value=1.0), st.floats(min_value=0.0, max_value=1.0))
def test_slam_score_bounded(inlier, confidence):
    req = scenario_request("normal_navigation", 42)
    req.perception.slam_inlier_ratio = inlier
    req.perception.localization_confidence = confidence
    result = SlamReliabilityAgent().evaluate(req)
    assert 0.0 <= result.score <= 1.0


def test_obstacle_risk_monotonic():
    near = scenario_request("normal_navigation", 42)
    far = scenario_request("normal_navigation", 42)
    near.robot_state.nearest_obstacle_m = 0.4
    near.action.linear_speed_mps = 0.5
    far.robot_state.nearest_obstacle_m = 2.0
    far.action.linear_speed_mps = 0.5
    assert PhysicalRiskAgent().evaluate(near).score > PhysicalRiskAgent().evaluate(far).score
    assert PhysicalRiskAgent().evaluate(near).decision == Decision.MODIFY
