from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from roboagent_guard.dependencies import AppState, get_app_state
from roboagent_guard.discovery.agent_card import agent_card
from roboagent_guard.models.common import HealthResponse
from roboagent_guard.models.decisions import ActionType, Decision
from roboagent_guard.models.requests import BatchEvaluationRequest, EvaluationRequest
from roboagent_guard.models.responses import BatchEvaluationResponse, EvaluationResponse
from roboagent_guard.security.input_safety import reject_image_payloads
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine, run_named_scenario
from roboagent_guard.simulator.scenarios import list_scenarios, scenario_request

app = FastAPI(
    title="RoboAgent Guard",
    description="Making Invisible Robot Risk Visible through Agentic Digital Twins",
    version="1.0.0",
)

StateDep = Annotated[AppState, Depends(get_app_state)]


def engine(state: AppState) -> EvaluationEngine:
    return EvaluationEngine(
        settings=state.settings,
        replay_guard=state.replay_guard,
        token_store=state.token_store,
        audit_store=state.audit_store(),
    )


def demo_engine(state: AppState) -> EvaluationEngine:
    return EvaluationEngine(
        settings=state.settings,
        replay_guard=ReplayGuard(),
        token_store=state.token_store,
        audit_store=state.audit_store(),
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    index = Path("static/index.html")
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<h1>RoboAgent Guard</h1>"


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="roboagent-guard", version="1.0.0")


@app.head("/")
def root_head() -> None:
    return None


@app.get("/healthz")
def healthz() -> HealthResponse:
    return health()


@app.get("/SKILL.md", response_class=PlainTextResponse)
def skill_md(state: StateDep) -> str:
    text = Path("SKILL.md").read_text(encoding="utf-8")
    return text.replace("PUBLIC_BASE_URL", state.settings.public_base_url.rstrip("/"))


@app.get("/skill.md", response_class=PlainTextResponse)
def skill_md_lowercase(state: StateDep) -> str:
    return skill_md(state)


@app.get("/capabilities")
def capabilities(state: StateDep) -> dict[str, Any]:
    return {
        "service": "roboagent-guard",
        "policy_version": state.settings.policy_version,
        "supported_actions": [item.value for item in ActionType],
        "supported_decisions": [item.value for item in Decision],
        "required_fields": [
            "request_id",
            "nonce",
            "timestamp",
            "caller",
            "action",
            "robot_state",
            "perception",
            "privacy",
            "simulation_seed",
        ],
        "scenario_names": [item["name"] for item in list_scenarios()],
    }


@app.get("/.well-known/agent.json")
def well_known(state: StateDep) -> dict[str, object]:
    return agent_card(state.settings.public_base_url, state.settings.policy_version)


@app.post("/v1/evaluate")
async def evaluate(
    request: Request,
    state: StateDep,
) -> EvaluationResponse:
    payload = await request.json()
    try:
        reject_image_payloads(payload)
        evaluation_request = EvaluationRequest.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    response = engine(state).evaluate(evaluation_request)
    state.evaluations[response.evaluation_id] = response
    return response


@app.post("/v1/evaluate/batch")
def evaluate_batch(
    batch: BatchEvaluationRequest,
    state: StateDep,
) -> BatchEvaluationResponse:
    results = []
    runner = engine(state)
    for item in batch.requests:
        response = runner.evaluate(item)
        state.evaluations[response.evaluation_id] = response
        results.append(response)
    return BatchEvaluationResponse(results=results)


@app.get("/v1/scenarios")
def scenarios() -> list[dict[str, str]]:
    return list_scenarios()


@app.post("/v1/scenarios/{scenario_name}/run")
def run_scenario(
    scenario_name: str,
    state: StateDep,
    seed: int | None = None,
) -> EvaluationResponse:
    try:
        request = scenario_request(scenario_name, seed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {scenario_name}") from exc
    response = run_named_scenario(demo_engine(state), scenario_name, request)
    state.evaluations[response.evaluation_id] = response
    return response


@app.get("/v1/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str, state: StateDep) -> object:
    try:
        return state.evaluations[evaluation_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="evaluation not found") from exc


@app.get("/v1/demo")
def demo(state: StateDep) -> dict[str, object]:
    names = [
        "normal_navigation",
        "low_light_high_speed",
        "unauthorized_camera_request",
        "combined_safety_privacy_crisis",
    ]
    output = {}
    runner = demo_engine(state)
    for name in names:
        req = scenario_request(name, seed=42)
        req.request_id = f"demo-{name}"
        req.nonce = f"demo-nonce-{name}"
        response = runner.evaluate(req)
        output[name] = {
            "decision": response.decision,
            "risk_score": response.risk_score,
            "recommended_action": response.recommended_action.type,
            "reasons": response.reasons,
        }
    return {"service": "roboagent-guard", "scenarios": output}


@app.post("/v1/judge-test")
def judge_test(state: StateDep) -> dict[str, object]:
    safe = scenario_request("normal_navigation", seed=42)
    safe.request_id = "judge-safe"
    safe.nonce = "judge-safe-nonce"
    unsafe = scenario_request("combined_safety_privacy_crisis", seed=42)
    unsafe.request_id = "judge-unsafe"
    unsafe.nonce = "judge-unsafe-nonce"
    safe_response = demo_engine(state).evaluate(safe)
    unsafe_response = demo_engine(state).evaluate(unsafe)
    passed = (
        safe_response.decision == Decision.APPROVE and unsafe_response.decision == Decision.BLOCK
    )
    return {
        "passed": passed,
        "safe_decision": safe_response.decision,
        "unsafe_decision": unsafe_response.decision,
    }


def main() -> None:
    import os

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("roboagent_guard.app:app", host="0.0.0.0", port=port)
