from __future__ import annotations

import argparse

from roboagent_guard.config import Settings
from roboagent_guard.integrations.nanda_trace import export_nanda_trace
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.runner import EvaluationEngine, run_named_scenario
from roboagent_guard.simulator.scenarios import scenario_request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="combined_safety_privacy_crisis")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    settings = Settings()
    request = scenario_request(args.scenario, args.seed)
    engine = EvaluationEngine(settings, ReplayGuard(), ApprovalTokenStore())
    response = run_named_scenario(engine, args.scenario, request)
    path = export_nanda_trace(request, response, settings.nanda_trace_dir)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
