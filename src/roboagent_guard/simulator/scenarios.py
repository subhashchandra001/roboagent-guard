from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from roboagent_guard.models.requests import EvaluationRequest

SCENARIO_DIR = Path(__file__).resolve().parents[3] / "scenarios"


def load_scenario(name: str) -> dict[str, Any]:
    path = SCENARIO_DIR / f"{name}.yaml"
    if not path.exists():
        raise KeyError(name)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid scenario {name}")
    return data


def list_scenarios() -> list[dict[str, str]]:
    scenarios: list[dict[str, str]] = []
    for path in sorted(SCENARIO_DIR.glob("*.yaml")):
        data = load_scenario(path.stem)
        scenarios.append(
            {
                "name": path.stem,
                "expected_decision": str(data.get("expected_decision", "")),
                "description": str(data.get("description", "")),
            }
        )
    return scenarios


def scenario_request(name: str, seed: int | None = None) -> EvaluationRequest:
    data = load_scenario(name)
    request_data = data["request"]
    if seed is not None:
        request_data = {**request_data, "simulation_seed": seed}
    return EvaluationRequest.model_validate(request_data)
