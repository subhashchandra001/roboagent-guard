from __future__ import annotations

import argparse

from roboagent_guard.audit.hashing import stable_json
from roboagent_guard.config import Settings
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine, run_named_scenario
from roboagent_guard.simulator.scenarios import scenario_request


def run_once(name: str, seed: int) -> str:
    request = scenario_request(name, seed)
    engine = EvaluationEngine(Settings(), ReplayGuard(), ApprovalTokenStore())
    response = run_named_scenario(engine, name, request)
    return stable_json(response.model_dump(mode="json"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    first = run_once(args.scenario, args.seed)
    second = run_once(args.scenario, args.seed)
    if first != second:
        print("determinism check failed")
        return 1
    print("determinism check passed")
    print(first)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
