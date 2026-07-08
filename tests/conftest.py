from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from roboagent_guard.app import app
from roboagent_guard.config import Settings
from roboagent_guard.dependencies import app_state
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine
from roboagent_guard.simulator.scenarios import scenario_request


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    app_state.replay_guard = ReplayGuard()
    app_state.token_store = ApprovalTokenStore()
    app_state.evaluations = {}
    return TestClient(app)


@pytest.fixture
def engine(tmp_path: Path) -> EvaluationEngine:
    settings = Settings.model_validate(
        {"AUDIT_PATH": tmp_path / "audit.jsonl", "NANDA_TRACE_DIR": tmp_path / "nanda"}
    )
    return EvaluationEngine(settings, ReplayGuard(), ApprovalTokenStore())


@pytest.fixture
def safe_request():
    return scenario_request("normal_navigation", 42)
