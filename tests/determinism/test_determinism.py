from __future__ import annotations

from roboagent_guard.audit.hashing import stable_json
from roboagent_guard.config import Settings
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine, run_named_scenario
from roboagent_guard.simulator.scenarios import scenario_request


def run_once(name: str) -> str:
    engine = EvaluationEngine(Settings(), ReplayGuard(), ApprovalTokenStore())
    response = run_named_scenario(engine, name, scenario_request(name, 42))
    return stable_json(response.model_dump(mode="json"))


def test_combined_crisis_byte_identical():
    assert run_once("combined_safety_privacy_crisis") == run_once("combined_safety_privacy_crisis")


def test_normal_navigation_byte_identical():
    assert run_once("normal_navigation") == run_once("normal_navigation")
