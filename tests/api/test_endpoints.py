from __future__ import annotations

import pytest

from roboagent_guard.models.decisions import Decision
from roboagent_guard.simulator.scenarios import scenario_request


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/SKILL.md",
        "/skill.md",
        "/capabilities",
        "/.well-known/agent.json",
        "/v1/scenarios",
        "/v1/demo",
    ],
)
def test_get_endpoints(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_health_shape(client):
    assert client.get("/health").json() == {
        "status": "ok",
        "service": "roboagent-guard",
        "version": "1.0.0",
    }


def test_evaluate_safe(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "api-safe"
    request["nonce"] = "api-safe-nonce"
    response = client.post("/v1/evaluate", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == Decision.APPROVE
    assert body["trace_hash"]


def test_evaluate_batch(client):
    first = scenario_request("normal_navigation", 42).model_dump(mode="json")
    second = scenario_request("unauthorized_camera_request", 42).model_dump(mode="json")
    first["request_id"], first["nonce"] = "batch-1", "batch-nonce-1"
    second["request_id"], second["nonce"] = "batch-2", "batch-nonce-2"
    response = client.post("/v1/evaluate/batch", json={"requests": [first, second]})
    assert response.status_code == 200
    assert [item["decision"] for item in response.json()["results"]] == ["approve", "block"]


def test_evaluate_batch_enforces_replay_state(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "batch-replay"
    request["nonce"] = "batch-replay-nonce"

    response = client.post("/v1/evaluate/batch", json={"requests": [request, request]})

    assert response.status_code == 200
    first, second = response.json()["results"]
    assert first["decision"] == Decision.APPROVE
    assert second["decision"] == Decision.BLOCK
    assert second["replay_detected"] is True


def test_evaluate_batch_rejects_image_payloads(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "batch-image-reject"
    request["nonce"] = "batch-image-reject-nonce"
    request["metadata"] = {"camera_frame": "base64-content-is-not-accepted"}

    response = client.post("/v1/evaluate/batch", json={"requests": [request]})

    assert response.status_code == 422
    assert "actual image content is not accepted" in response.text


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("normal_navigation", "approve"),
        ("low_light_slow_motion", "approve_with_constraints"),
        ("low_light_high_speed", "modify"),
        ("uneven_surface_high_blur", "modify"),
        ("slam_degradation", "modify"),
        ("person_in_private_zone", "approve_with_constraints"),
        ("unauthorized_camera_request", "block"),
        ("replayed_approved_action", "block"),
        ("hidden_low_slam_confidence", "modify"),
        ("combined_safety_privacy_crisis", "block"),
    ],
)
def test_run_scenarios(client, name, expected):
    response = client.post(f"/v1/scenarios/{name}/run?seed=42")
    assert response.status_code == 200
    assert response.json()["decision"] == expected


def test_named_scenarios_are_repeatable_demos(client):
    first = client.post("/v1/scenarios/low_light_slow_motion/run?seed=42")
    second = client.post("/v1/scenarios/low_light_slow_motion/run?seed=42")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["decision"] == Decision.APPROVE_WITH_CONSTRAINTS
    assert second.json()["decision"] == Decision.APPROVE_WITH_CONSTRAINTS
    assert first.json()["replay_detected"] is False
    assert second.json()["replay_detected"] is False


def test_full_demo_is_repeatable(client):
    first = client.get("/v1/demo")
    second = client.get("/v1/demo")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["scenarios"]["normal_navigation"]["decision"] == Decision.APPROVE
    assert second.json()["scenarios"]["normal_navigation"]["decision"] == Decision.APPROVE


def test_get_evaluation(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "get-eval"
    request["nonce"] = "get-eval-nonce"
    created = client.post("/v1/evaluate", json=request).json()
    fetched = client.get(f"/v1/evaluations/{created['evaluation_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["evaluation_id"] == created["evaluation_id"]


def test_judge_endpoint(client):
    response = client.post("/v1/judge-test")
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_judge_endpoint_is_repeatable(client):
    first = client.post("/v1/judge-test")
    second = client.post("/v1/judge-test")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["passed"] is True
    assert second.json()["passed"] is True
