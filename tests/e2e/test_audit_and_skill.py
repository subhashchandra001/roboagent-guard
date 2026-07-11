from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from roboagent_guard.audit.store import AuditStore
from roboagent_guard.audit.verification import verify_audit_chain
from roboagent_guard.config import Settings
from roboagent_guard.dependencies import AppState
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine
from roboagent_guard.simulator.scenarios import scenario_request


def test_audit_chain_and_tamper_detection(tmp_path):
    path = tmp_path / "audit.jsonl"
    settings = Settings.model_validate({"AUDIT_PATH": path, "NANDA_TRACE_DIR": tmp_path / "nanda"})
    engine = EvaluationEngine(settings, ReplayGuard(), ApprovalTokenStore(), AuditStore(path))
    req = scenario_request("normal_navigation", 42)
    engine.evaluate(req)
    ok, errors = verify_audit_chain(path)
    assert ok, errors
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    record["final_decision"] = "block"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    ok, errors = verify_audit_chain(path)
    assert not ok
    assert errors


def test_skill_only_workflow(client):
    skill = client.get("/SKILL.md").text
    assert "Call `GET /health` first." in skill
    assert "POST /v1/evaluate" in skill
    assert "If the decision is `block`, execute nothing." in skill
    assert client.get("/skill.md").text == skill
    assert client.get("/health").json()["status"] == "ok"
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "skill-flow"
    request["nonce"] = "skill-flow-nonce"
    response = client.post("/v1/evaluate", json=request)
    assert response.status_code == 200
    assert response.json()["decision"] == "approve"


def test_api_client_uses_isolated_audit_path(client, tmp_path):
    request = scenario_request("normal_navigation", 42).model_dump(mode="json")
    request["request_id"] = "isolated-audit"
    request["nonce"] = "isolated-audit-nonce"

    response = client.post("/v1/evaluate", json=request)

    assert response.status_code == 200
    assert (tmp_path / "audit.jsonl").exists()


def test_app_state_audit_store_initialization_is_thread_safe(tmp_path):
    settings = Settings.model_validate(
        {"AUDIT_PATH": tmp_path / "audit.jsonl", "NANDA_TRACE_DIR": tmp_path / "nanda"}
    )
    state = AppState(settings=settings)

    with ThreadPoolExecutor(max_workers=8) as pool:
        stores = list(pool.map(lambda _: state.audit_store(), range(32)))

    assert len({id(store) for store in stores}) == 1
    assert stores[0].path == settings.audit_path
