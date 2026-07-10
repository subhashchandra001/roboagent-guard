from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from roboagent_guard.models.decisions import CallerRole, Decision
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.simulator.scenarios import scenario_request


def test_duplicate_request_id_blocks(engine):
    req = scenario_request("normal_navigation", 42)
    assert engine.evaluate(req, audit=False).decision == Decision.APPROVE
    replay = engine.evaluate(req, audit=False)
    assert replay.decision == Decision.BLOCK
    assert replay.replay_detected is True


def test_reused_nonce_blocks(engine):
    first = scenario_request("normal_navigation", 42)
    second = scenario_request("normal_navigation", 42)
    second.request_id = "new-request-same-nonce"
    assert engine.evaluate(first, audit=False).decision == Decision.APPROVE
    assert engine.evaluate(second, audit=False).decision == Decision.BLOCK


@pytest.mark.parametrize(
    ("scenario", "code"),
    [
        ("combined_safety_privacy_crisis", "UNAUTHORIZED_ACTION"),
        ("unauthorized_camera_request", "UNAUTHORIZED_RAW_CAMERA"),
        ("unauthorized_camera_request", "RAW_CAMERA_UNAUTHORIZED_RECIPIENT"),
        ("hidden_low_slam_confidence", "SLAM_INLIER_RATIO_CRITICAL"),
        ("slam_degradation", "LOCALIZATION_CONFIDENCE_CRITICAL"),
    ],
)
def test_adversarial_violation_codes(engine, scenario, code):
    response = engine.evaluate(scenario_request(scenario, 42), audit=False)
    assert code in response.violation_codes


def test_forged_approval_token_blocks(engine):
    req = scenario_request("normal_navigation", 42)
    req.approval.token = "fake-token"
    response = engine.evaluate(req, audit=False)
    assert response.decision == Decision.BLOCK
    assert "FORGED_APPROVAL_TOKEN" in response.violation_codes


def test_client_safety_claim_does_not_override_evidence(engine):
    req = scenario_request("combined_safety_privacy_crisis", 42)
    req.safety_approved = True
    req.client_risk_score = 0.0
    req.metadata["safety_approved"] = "true"
    req.metadata["risk_level"] = "low"

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.BLOCK
    assert response.risk_score >= 0.9
    assert "UNAUTHORIZED_ACTION" in response.violation_codes
    assert "RAW_CAMERA_UNAUTHORIZED_RECIPIENT" in response.violation_codes


def test_registered_caller_role_mismatch_blocks(engine):
    req = scenario_request("normal_navigation", 42)
    req.caller.id = "planner-agent-01"
    req.caller.role = CallerRole.SUPERVISOR

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.BLOCK
    assert "CALLER_ROLE_MISMATCH" in response.violation_codes


def test_unregistered_privileged_caller_blocks(engine):
    req = scenario_request("normal_navigation", 42)
    req.caller.id = "fake-supervisor"
    req.caller.role = CallerRole.SUPERVISOR

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.BLOCK
    assert "CALLER_ROLE_MISMATCH" in response.violation_codes


def test_registered_planner_still_passes_nominal_authorization(engine):
    req = scenario_request("normal_navigation", 42)

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.APPROVE
    assert "CALLER_ROLE_MISMATCH" not in response.violation_codes


def test_privacy_marker_claim_does_not_replace_required_filter(engine):
    req = scenario_request("unauthorized_camera_request", 42)
    req.privacy.privacy_filter_applied = False
    req.metadata["privacy_filtered"] = "vision-1"
    req.metadata["redacted"] = True

    response = engine.evaluate(req, audit=False)

    assert response.decision == Decision.BLOCK
    assert "FACE_DATA_WITHOUT_FILTER" in response.violation_codes


def test_replaying_blocked_action_with_new_ids_still_blocks(engine):
    first = scenario_request("unauthorized_camera_request", 42)
    first_response = engine.evaluate(first, audit=False)
    assert first_response.decision == Decision.BLOCK

    replay = scenario_request("unauthorized_camera_request", 42)
    replay.request_id = "blocked-action-new-request"
    replay.nonce = "blocked-action-new-nonce"
    replay_response = engine.evaluate(replay, audit=False)

    assert replay_response.decision == Decision.BLOCK
    assert replay_response.replay_detected is True
    assert "REPLAY_BLOCKED_ACTION" in replay_response.violation_codes


def test_api_rejects_nested_image_payload(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "nested-image-payload"
    request["nonce"] = "nested-image-payload-nonce"
    request["metadata"] = {"debug": {"camera_frame": "base64-image-would-be-here"}}

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 422
    assert "actual image content is not accepted" in response.json()["detail"]


def test_api_rejects_data_uri_image_payload(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "data-uri-image-payload"
    request["nonce"] = "data-uri-image-payload-nonce"
    request["metadata"] = {"debug_blob": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="}

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 422
    assert "actual image content is not accepted" in response.json()["detail"]


def test_api_rejects_base64_image_bytes_under_generic_key(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "base64-image-bytes"
    request["nonce"] = "base64-image-bytes-nonce"
    png_like_bytes = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 80)
    request["metadata"] = {"debug_blob": base64.b64encode(png_like_bytes).decode("ascii")}

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 422
    assert "actual image content is not accepted" in response.json()["detail"]


def test_api_allows_text_camera_metadata(client):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "text-camera-metadata"
    request["nonce"] = "text-camera-metadata-nonce"
    request["metadata"] = {"sensor_status": "camera disabled; metadata flags only"}

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 200
    assert response.json()["decision"] == Decision.APPROVE


def test_reused_approval_token_blocks(tmp_path):
    from roboagent_guard.config import Settings
    from roboagent_guard.security.replay_guard import ReplayGuard
    from roboagent_guard.simulator.runner import EvaluationEngine

    engine = EvaluationEngine(
        Settings.model_validate({"AUDIT_PATH": tmp_path / "audit.jsonl"}),
        ReplayGuard(),
        ApprovalTokenStore({"token-1"}),
    )
    first = scenario_request("normal_navigation", 42)
    first.approval.token = "token-1"
    second = scenario_request("normal_navigation", 42)
    second.request_id = "token-second"
    second.nonce = "token-second-nonce"
    second.approval.token = "token-1"
    assert engine.evaluate(first, audit=False).decision == Decision.APPROVE
    response = engine.evaluate(second, audit=False)
    assert response.decision == Decision.BLOCK
    assert "REUSED_APPROVAL_TOKEN" in response.violation_codes


@pytest.mark.parametrize("field", ["emergency_stop_available", "nearest_obstacle_m"])
def test_missing_critical_fields_rejected(field):
    data = scenario_request("normal_navigation", 42).model_dump(mode="json")
    del data["robot_state"][field]
    with pytest.raises(ValidationError):
        scenario_request("normal_navigation", 42).model_validate(data)
