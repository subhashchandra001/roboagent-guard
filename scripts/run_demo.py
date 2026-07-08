from __future__ import annotations

import argparse
import json

from roboagent_guard.config import Settings
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine, run_named_scenario
from roboagent_guard.simulator.scenarios import scenario_request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    request = scenario_request(args.scenario, args.seed)
    engine = EvaluationEngine(Settings(), ReplayGuard(), ApprovalTokenStore())
    response = run_named_scenario(engine, args.scenario, request)
    print(json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
