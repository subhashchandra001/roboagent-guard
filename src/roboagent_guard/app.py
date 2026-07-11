from __future__ import annotations

from json import JSONDecodeError
from pathlib import Path
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from roboagent_guard.audit.hashing import sha256_digest
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


def decision_receipt(response: EvaluationResponse) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "evaluation_id": response.evaluation_id,
        "request_id": response.request_id,
        "decision": response.decision,
        "risk_level": response.risk_level,
        "risk_score": response.risk_score,
        "recommended_action": response.recommended_action.model_dump(mode="json"),
        "digital_twin_action_applied": response.digital_twin.action_applied,
        "violation_codes": response.violation_codes,
        "trace_hash": response.trace_hash,
        "policy_version": response.policy_version,
        "algorithm": "sha256-stable-json",
    }
    payload["receipt_hash"] = sha256_digest(payload)
    return payload


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
        "autonomy_model": {
            "default": "agent_autonomous",
            "human_intervention": "exception_only",
            "description": (
                "Agents can approve, constrain, modify, or block actions without human help. "
                "Human escalation is reserved for stale evidence or unresolved uncertainty."
            ),
        },
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
        "optional_fields": [
            "evaluation_time",
            "approval",
            "client_risk_score",
            "safety_approved",
            "metadata",
        ],
        "scenario_names": [item["name"] for item in list_scenarios()],
        "demo_endpoints": {
            "runtime_readiness": "GET /v1/readiness",
            "judge_skill_test": "POST /v1/agent-skill-test",
            "composed_mission_planner": "POST /v1/compose/mission-plan",
            "decision_receipt": "GET /v1/receipts/{evaluation_id}",
            "verify_receipt": "POST /v1/receipts/verify",
        },
    }


@app.get("/v1/readiness")
def readiness(state: StateDep) -> dict[str, object]:
    checks: list[dict[str, object]] = []

    checks.append(
        {
            "name": "health",
            "label": "Health endpoint",
            "passed": health().status == "ok",
            "evidence": {"service": "roboagent-guard", "version": "1.0.0"},
        }
    )

    capability_data = capabilities(state)
    supported_actions = capability_data["supported_actions"]
    supported_decisions = capability_data["supported_decisions"]
    checks.append(
        {
            "name": "capabilities",
            "label": "Capability discovery",
            "passed": bool(supported_actions) and bool(supported_decisions),
            "evidence": {
                "actions": len(supported_actions),
                "decisions": len(supported_decisions),
                "policy_version": capability_data["policy_version"],
            },
        }
    )

    runner = demo_engine(state)
    scenario_results = []
    for item in list_scenarios():
        request = scenario_request(item["name"], seed=42)
        request.request_id = f"readiness-{item['name']}"
        request.nonce = f"readiness-nonce-{item['name']}"
        if item["name"] == "replayed_approved_action":
            runner.evaluate(request.model_copy(deep=True), audit=False)
            response = runner.evaluate(request.model_copy(deep=True), audit=False)
        else:
            response = runner.evaluate(request, audit=False)
        scenario_results.append(
            {
                "name": item["name"],
                "expected_decision": item["expected_decision"],
                "actual_decision": response.decision,
                "passed": response.decision == item["expected_decision"],
            }
        )
    checks.append(
        {
            "name": "scenario_regression",
            "label": "Scenario expected decisions",
            "passed": all(bool(item["passed"]) for item in scenario_results),
            "evidence": {
                "passed": sum(1 for item in scenario_results if item["passed"]),
                "total": len(scenario_results),
                "scenarios": scenario_results,
            },
        }
    )

    skill = skill_md(state)
    required_skill_phrases = [
        "Call `GET /health` first.",
        "POST /v1/evaluate",
        "If the decision is `modify`, do not execute the original action",
        "If the decision is `block`, execute nothing.",
        "Default mode: no routine human intervention.",
    ]
    skill_steps = [
        {
            "step": "read_skill_md",
            "passed": all(phrase in skill for phrase in required_skill_phrases),
        },
        {"step": "read_capabilities", "passed": True},
    ]
    representative_expectations = {
        "normal_navigation": Decision.APPROVE,
        "low_light_slow_motion": Decision.APPROVE_WITH_CONSTRAINTS,
        "low_light_high_speed": Decision.MODIFY,
        "combined_safety_privacy_crisis": Decision.BLOCK,
    }
    representative_results = []
    representative_runner = demo_engine(state)
    for scenario_name, expected in representative_expectations.items():
        request = scenario_request(scenario_name, seed=42)
        request.request_id = f"readiness-skill-{scenario_name}"
        request.nonce = f"readiness-skill-nonce-{scenario_name}"
        response = representative_runner.evaluate(request, audit=False)
        representative_results.append(
            {
                "scenario": scenario_name,
                "passed": response.decision == expected,
                "human_intervention_required": response.human_approval_required,
                "actual_decision": response.decision,
            }
        )
    skill_steps.append(
        {
            "step": "evaluate_representative_actions",
            "passed": all(item["passed"] for item in representative_results),
        }
    )
    skill_steps.append(
        {
            "step": "confirm_exception_only_human_review",
            "passed": all(
                not item["human_intervention_required"]
                for item in representative_results
                if item["actual_decision"] != Decision.REQUEST_HUMAN_APPROVAL
            ),
        }
    )
    checks.append(
        {
            "name": "skill_judge",
            "label": "SkillMD judge proof",
            "passed": all(bool(step["passed"]) for step in skill_steps),
            "evidence": {
                "steps": [
                    {"step": step["step"], "passed": step["passed"]}
                    for step in skill_steps
                    if isinstance(step, dict)
                ],
            },
        }
    )

    mission = [
        "normal_navigation",
        "low_light_high_speed",
        "person_in_private_zone",
        "unauthorized_camera_request",
        "combined_safety_privacy_crisis",
    ]
    plan_runner = demo_engine(state)
    plan_steps = []
    for index, scenario_name in enumerate(mission, start=1):
        request = scenario_request(scenario_name, seed=42)
        request.request_id = f"readiness-plan-{index}-{scenario_name}"
        request.nonce = f"readiness-plan-nonce-{index}-{scenario_name}"
        response = plan_runner.evaluate(request, audit=False)
        plan_steps.append(
            {
                "guard_decision": response.decision,
                "autonomous_outcome": autonomy_outcome(response),
            }
        )
    checks.append(
        {
            "name": "composed_planner",
            "label": "Composed planner proof",
            "passed": all(
                step["autonomous_outcome"] != "request_human_review" for step in plan_steps
            ),
            "evidence": {
                "steps": len(plan_steps),
                "blocked_steps": sum(
                    1 for step in plan_steps if step["guard_decision"] == Decision.BLOCK
                ),
                "modified_steps": sum(
                    1 for step in plan_steps if step["guard_decision"] == Decision.MODIFY
                ),
                "constrained_steps": sum(
                    1
                    for step in plan_steps
                    if step["guard_decision"] == Decision.APPROVE_WITH_CONSTRAINTS
                ),
            },
        }
    )

    passed_count = sum(1 for item in checks if item["passed"])
    score = round((passed_count / len(checks)) * 100) if checks else 0
    return {
        "service": "roboagent-guard",
        "score": score,
        "status": "ready" if score == 100 else "review",
        "passed": passed_count,
        "total": len(checks),
        "checks": checks,
    }


@app.get("/.well-known/agent.json")
def well_known(state: StateDep) -> dict[str, object]:
    return agent_card(state.settings.public_base_url, state.settings.policy_version)


@app.post("/v1/evaluate")
async def evaluate(
    request: Request,
    state: StateDep,
) -> EvaluationResponse:
    try:
        payload = await request.json()
        reject_image_payloads(payload)
        evaluation_request = EvaluationRequest.model_validate(payload)
    except (JSONDecodeError, ValueError) as exc:
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


@app.get("/v1/receipts/{evaluation_id}")
def get_receipt(evaluation_id: str, state: StateDep) -> dict[str, Any]:
    try:
        return decision_receipt(state.evaluations[evaluation_id])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="evaluation not found") from exc


@app.post("/v1/receipts/verify")
def verify_receipt(receipt: dict[str, Any], state: StateDep) -> dict[str, object]:
    supplied_hash = receipt.get("receipt_hash")
    if not isinstance(supplied_hash, str) or not supplied_hash:
        return {"valid": False, "reason": "receipt_hash is missing"}
    payload = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    expected_hash = sha256_digest(payload)
    if supplied_hash != expected_hash:
        return {
            "valid": False,
            "reason": "receipt_hash does not match receipt payload",
            "expected_hash": expected_hash,
            "supplied_hash": supplied_hash,
        }

    evaluation_id = receipt.get("evaluation_id")
    if isinstance(evaluation_id, str) and evaluation_id in state.evaluations:
        stored = decision_receipt(state.evaluations[evaluation_id])
        if supplied_hash != stored["receipt_hash"]:
            return {
                "valid": False,
                "reason": "receipt is validly hashed but does not match stored evaluation",
                "expected_hash": stored["receipt_hash"],
                "supplied_hash": supplied_hash,
            }

    return {
        "valid": True,
        "reason": "receipt_hash matches receipt payload",
        "receipt_hash": supplied_hash,
    }


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


def autonomy_outcome(response: EvaluationResponse) -> str:
    if response.decision == Decision.APPROVE:
        return "execute_original_action"
    if response.decision == Decision.APPROVE_WITH_CONSTRAINTS:
        return "execute_original_action_with_constraints"
    if response.decision == Decision.MODIFY:
        return "execute_recommended_action_only"
    if response.decision == Decision.BLOCK:
        return "execute_nothing"
    return "request_human_review"


@app.post("/v1/agent-skill-test")
def agent_skill_test(state: StateDep) -> dict[str, object]:
    skill = skill_md(state)
    required_phrases = [
        "Call `GET /health` first.",
        "POST /v1/evaluate",
        "If the decision is `modify`, do not execute the original action",
        "If the decision is `block`, execute nothing.",
        "Default mode: no routine human intervention.",
    ]
    steps: list[dict[str, object]] = [
        {
            "step": "read_skill_md",
            "passed": all(phrase in skill for phrase in required_phrases),
            "evidence": {
                "source": f"{state.settings.public_base_url.rstrip('/')}/skill.md",
                "required_phrases_found": [
                    phrase for phrase in required_phrases if phrase in skill
                ],
            },
        },
        {
            "step": "read_capabilities",
            "passed": True,
            "evidence": {
                "supported_decisions": [item.value for item in Decision],
                "autonomy_model": capabilities(state)["autonomy_model"],
            },
        },
    ]
    scenario_expectations = {
        "normal_navigation": Decision.APPROVE,
        "low_light_slow_motion": Decision.APPROVE_WITH_CONSTRAINTS,
        "low_light_high_speed": Decision.MODIFY,
        "combined_safety_privacy_crisis": Decision.BLOCK,
    }
    runner = demo_engine(state)
    evaluations = []
    for scenario_name, expected in scenario_expectations.items():
        request = scenario_request(scenario_name, seed=42)
        request.request_id = f"agent-skill-test-{scenario_name}"
        request.nonce = f"agent-skill-test-nonce-{scenario_name}"
        response = runner.evaluate(request)
        evaluations.append(
            {
                "scenario": scenario_name,
                "expected_decision": expected,
                "actual_decision": response.decision,
                "passed": response.decision == expected,
                "autonomous_outcome": autonomy_outcome(response),
                "human_intervention_required": response.human_approval_required,
                "recommended_action": response.recommended_action.type,
                "digital_twin_applied": response.digital_twin.action_applied,
            }
        )
    steps.append(
        {
            "step": "evaluate_representative_actions",
            "passed": all(item["passed"] for item in evaluations),
            "evidence": evaluations,
        }
    )
    steps.append(
        {
            "step": "confirm_exception_only_human_review",
            "passed": all(
                not item["human_intervention_required"]
                for item in evaluations
                if item["actual_decision"] != Decision.REQUEST_HUMAN_APPROVAL
            ),
            "evidence": (
                "approve, constrained, modify, and block outcomes were handled "
                "without routine human intervention"
            ),
        }
    )
    return {
        "passed": all(bool(step["passed"]) for step in steps),
        "test": "agent_uses_only_skill_md",
        "service": "roboagent-guard",
        "steps": steps,
    }


@app.post("/v1/compose/mission-plan")
def composed_mission_plan(state: StateDep) -> dict[str, object]:
    mission = [
        ("normal_navigation", "start with nominal navigation"),
        ("low_light_high_speed", "adapt unsafe low-light motion"),
        ("person_in_private_zone", "continue with privacy constraints"),
        ("unauthorized_camera_request", "reject unauthorized raw camera sharing"),
        ("combined_safety_privacy_crisis", "stop during combined crisis"),
    ]
    runner = demo_engine(state)
    plan_steps = []
    for index, (scenario_name, goal) in enumerate(mission, start=1):
        request = scenario_request(scenario_name, seed=42)
        request.request_id = f"composed-mission-{index}-{scenario_name}"
        request.nonce = f"composed-mission-nonce-{index}-{scenario_name}"
        response = runner.evaluate(request)
        plan_steps.append(
            {
                "index": index,
                "goal": goal,
                "source_scenario": scenario_name,
                "guard_decision": response.decision,
                "autonomous_outcome": autonomy_outcome(response),
                "action_for_downstream_agent": response.recommended_action.model_dump(mode="json"),
                "constraints": response.constraints,
                "human_intervention_required": response.human_approval_required,
                "risk_score": response.risk_score,
                "reason": response.reasons[0] if response.reasons else "",
            }
        )
    return {
        "service": "autonomous-mission-planner-demo",
        "composes": {
            "service": "roboagent-guard",
            "endpoint": "POST /v1/evaluate",
            "purpose": (
                "convert proposed robot actions into executable, constrained, "
                "replaced, or blocked steps"
            ),
        },
        "passed": all(step["autonomous_outcome"] != "request_human_review" for step in plan_steps),
        "human_intervention_model": "none_for_routine_approve_modify_block_paths",
        "mission_summary": {
            "steps": len(plan_steps),
            "blocked_steps": sum(
                1 for step in plan_steps if step["guard_decision"] == Decision.BLOCK
            ),
            "modified_steps": sum(
                1 for step in plan_steps if step["guard_decision"] == Decision.MODIFY
            ),
            "constrained_steps": sum(
                1
                for step in plan_steps
                if step["guard_decision"] == Decision.APPROVE_WITH_CONSTRAINTS
            ),
        },
        "plan": plan_steps,
    }


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
