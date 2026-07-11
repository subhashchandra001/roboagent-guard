from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from roboagent_guard.models.decisions import Decision
from roboagent_guard.simulator.scenarios import scenario_request


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/healthz",
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
    assert client.get("/healthz").json() == client.get("/health").json()


def test_discovery_exposes_autonomy_model(client):
    capabilities = client.get("/capabilities").json()
    agent_card = client.get("/.well-known/agent.json").json()

    assert capabilities["autonomy_model"]["default"] == "agent_autonomous"
    assert capabilities["autonomy_model"]["human_intervention"] == "exception_only"
    assert agent_card["autonomy_model"] == capabilities["autonomy_model"]
    assert capabilities["demo_endpoints"]["judge_skill_test"] == "POST /v1/agent-skill-test"
    assert agent_card["demo_endpoints"]["composed_mission_planner"]["path"] == (
        "/v1/compose/mission-plan"
    )


def test_root_head(client):
    assert client.head("/").status_code == 200


def test_dashboard_has_decision_and_risk_visual_states(client):
    html = client.get("/").text

    assert 'id="decisionBox"' in html
    assert ".decision.block" in html
    assert ".decision.critical" in html
    assert ".pill.critical" in html
    assert "function setDecisionVisual" in html
    assert "function selectScenario" in html
    assert "setErrorState" in html
    assert "document.execCommand(\"copy\")" in html


def test_evaluate_safe(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "api-safe"
    request["nonce"] = "api-safe-nonce"
    response = client.post("/v1/evaluate", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == Decision.APPROVE
    assert body["trace_hash"]


def test_evaluate_accepts_current_snapshot_time(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "api-current-time"
    request["nonce"] = "api-current-time-nonce"
    request["timestamp"] = datetime.now(UTC).isoformat()

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 200
    assert response.json()["decision"] == Decision.APPROVE
    assert response.json()["freshness_passed"] is True


def test_evaluate_rejects_stale_timestamp_when_evaluation_time_is_injected(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "api-stale-eval-time"
    request["nonce"] = "api-stale-eval-time-nonce"
    timestamp = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
    request["timestamp"] = timestamp.isoformat()
    request["evaluation_time"] = (timestamp + timedelta(minutes=10)).isoformat()

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 200
    assert response.json()["decision"] == Decision.REQUEST_HUMAN_APPROVAL
    assert response.json()["freshness_passed"] is False
    assert "STALE_TIMESTAMP" in response.json()["violation_codes"]


def test_evaluate_rejects_malformed_json(client):
    response = client.post(
        "/v1/evaluate", content="{bad json", headers={"content-type": "application/json"}
    )

    assert response.status_code == 422


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


def test_receipt_round_trip_and_verification(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "receipt-eval"
    request["nonce"] = "receipt-eval-nonce"
    created = client.post("/v1/evaluate", json=request).json()

    receipt_response = client.get(f"/v1/receipts/{created['evaluation_id']}")
    receipt = receipt_response.json()
    verified = client.post("/v1/receipts/verify", json=receipt)

    assert receipt_response.status_code == 200
    assert receipt["evaluation_id"] == created["evaluation_id"]
    assert receipt["trace_hash"] == created["trace_hash"]
    assert receipt["receipt_hash"]
    assert verified.status_code == 200
    assert verified.json()["valid"] is True


def test_tampered_receipt_fails_verification(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "tampered-receipt"
    request["nonce"] = "tampered-receipt-nonce"
    created = client.post("/v1/evaluate", json=request).json()
    receipt = client.get(f"/v1/receipts/{created['evaluation_id']}").json()
    receipt["decision"] = "block"

    verified = client.post("/v1/receipts/verify", json=receipt)

    assert verified.status_code == 200
    assert verified.json()["valid"] is False
    assert verified.json()["reason"] == "receipt_hash does not match receipt payload"


def test_missing_receipt_returns_404(client):
    response = client.get("/v1/receipts/not-found")

    assert response.status_code == 404


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


def test_agent_skill_test_proves_skill_only_flow(client):
    response = client.post("/v1/agent-skill-test")

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["test"] == "agent_uses_only_skill_md"
    assert [step["step"] for step in body["steps"]] == [
        "read_skill_md",
        "read_capabilities",
        "evaluate_representative_actions",
        "confirm_exception_only_human_review",
    ]
    evaluations = body["steps"][2]["evidence"]
    assert [item["actual_decision"] for item in evaluations] == [
        Decision.APPROVE,
        Decision.APPROVE_WITH_CONSTRAINTS,
        Decision.MODIFY,
        Decision.BLOCK,
    ]


def test_composed_mission_plan_uses_guard_without_routine_human_intervention(client):
    response = client.post("/v1/compose/mission-plan")

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["composes"]["endpoint"] == "POST /v1/evaluate"
    assert body["mission_summary"] == {
        "steps": 5,
        "blocked_steps": 2,
        "modified_steps": 1,
        "constrained_steps": 1,
    }
    assert {step["autonomous_outcome"] for step in body["plan"]} == {
        "execute_original_action",
        "execute_original_action_with_constraints",
        "execute_recommended_action_only",
        "execute_nothing",
    }
