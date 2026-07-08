from __future__ import annotations

from pathlib import Path

from roboagent_guard.audit.hashing import stable_json
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.models.responses import EvaluationResponse


def export_nanda_trace(
    request: EvaluationRequest, response: EvaluationResponse, out_dir: Path
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{response.evaluation_id}.jsonl"
    events = [
        {
            "ts": 1.0,
            "kind": "send",
            "agent": request.caller.id,
            "to": "roboagent_guard",
            "msg": f"{request.action.type}:{request.action.linear_speed_mps} risk_checked",
        },
        {
            "ts": 2.0,
            "kind": "send",
            "agent": "roboagent_guard",
            "to": request.caller.id,
            "msg": f"decision:{response.decision} safe_action:{response.recommended_action.type}",
        },
    ]
    path.write_text("\n".join(stable_json(event) for event in events) + "\n", encoding="utf-8")
    return path
