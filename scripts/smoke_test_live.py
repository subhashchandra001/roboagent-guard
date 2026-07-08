from __future__ import annotations

import argparse

import httpx

from roboagent_guard.simulator.scenarios import scenario_request

SCENARIOS: dict[str, str] = {
    "normal_navigation": "approve",
    "low_light_slow_motion": "approve_with_constraints",
    "low_light_high_speed": "modify",
    "uneven_surface_high_blur": "modify",
    "slam_degradation": "modify",
    "person_in_private_zone": "approve_with_constraints",
    "unauthorized_camera_request": "block",
    "replayed_approved_action": "block",
    "hidden_low_slam_confidence": "modify",
    "combined_safety_privacy_crisis": "block",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    with httpx.Client(timeout=75.0) as client:
        for path in [
            "/",
            "/health",
            "/SKILL.md",
            "/skill.md",
            "/capabilities",
            "/.well-known/agent.json",
            "/v1/scenarios",
            "/v1/demo",
            "/docs",
            "/openapi.json",
        ]:
            response = client.get(base + path)
            response.raise_for_status()
            print(path, response.status_code)

        scenarios = client.get(base + "/v1/scenarios")
        scenarios.raise_for_status()
        assert len(scenarios.json()) >= len(SCENARIOS)

        request = scenario_request("normal_navigation", 42).model_dump(mode="json")
        request["request_id"] = "live-smoke-safe"
        request["nonce"] = "live-smoke-safe-nonce"
        response = client.post(base + "/v1/evaluate", json=request)
        response.raise_for_status()
        print("/v1/evaluate", response.json()["decision"])

        batch_first = scenario_request("normal_navigation", 42).model_dump(mode="json")
        batch_second = scenario_request("unauthorized_camera_request", 42).model_dump(mode="json")
        batch_first["request_id"], batch_first["nonce"] = "live-batch-1", "live-batch-nonce-1"
        batch_second["request_id"], batch_second["nonce"] = "live-batch-2", "live-batch-nonce-2"
        batch = client.post(
            base + "/v1/evaluate/batch", json={"requests": [batch_first, batch_second]}
        )
        batch.raise_for_status()
        print("/v1/evaluate/batch", [item["decision"] for item in batch.json()["results"]])

        for name, expected in SCENARIOS.items():
            scenario = client.post(base + f"/v1/scenarios/{name}/run?seed=42")
            scenario.raise_for_status()
            decision = scenario.json()["decision"]
            assert decision == expected, f"{name}: expected {expected}, got {decision}"
            print(f"/v1/scenarios/{name}/run", decision)

        created = client.post(base + "/v1/scenarios/normal_navigation/run?seed=42")
        created.raise_for_status()
        evaluation_id = created.json()["evaluation_id"]
        fetched = client.get(base + f"/v1/evaluations/{evaluation_id}")
        fetched.raise_for_status()
        print("/v1/evaluations/{evaluation_id}", fetched.json()["decision"])

        judge = client.post(base + "/v1/judge-test")
        judge.raise_for_status()
        assert judge.json()["passed"] is True
        print("/v1/judge-test", judge.json()["passed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
