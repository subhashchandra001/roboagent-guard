from __future__ import annotations

import argparse
from collections.abc import Callable
from time import sleep
from typing import Any

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


def request_with_retry(
    request: Callable[[], httpx.Response],
    label: str,
    attempts: int = 5,
) -> httpx.Response:
    last_response: httpx.Response | None = None
    for attempt in range(1, attempts + 1):
        response = request()
        if response.status_code < 500 and response.status_code != 404:
            return response
        last_response = response
        sleep(1.5 * attempt)
    assert last_response is not None
    raise httpx.HTTPStatusError(
        f"{label} returned {last_response.status_code} after {attempts} attempts",
        request=last_response.request,
        response=last_response,
    )


def json_body(response: httpx.Response) -> Any:
    response.raise_for_status()
    return response.json()


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
            response = request_with_retry(lambda path=path: client.get(base + path), path)
            response.raise_for_status()
            print(path, response.status_code)

        scenarios = request_with_retry(lambda: client.get(base + "/v1/scenarios"), "/v1/scenarios")
        assert len(json_body(scenarios)) >= len(SCENARIOS)

        request = scenario_request("normal_navigation", 42).model_dump(mode="json")
        request["request_id"] = "live-smoke-safe"
        request["nonce"] = "live-smoke-safe-nonce"
        response = request_with_retry(
            lambda: client.post(base + "/v1/evaluate", json=request), "/v1/evaluate"
        )
        print("/v1/evaluate", json_body(response)["decision"])

        batch_first = scenario_request("normal_navigation", 42).model_dump(mode="json")
        batch_second = scenario_request("unauthorized_camera_request", 42).model_dump(mode="json")
        batch_first["request_id"], batch_first["nonce"] = "live-batch-1", "live-batch-nonce-1"
        batch_second["request_id"], batch_second["nonce"] = "live-batch-2", "live-batch-nonce-2"
        batch = request_with_retry(
            lambda: client.post(
                base + "/v1/evaluate/batch", json={"requests": [batch_first, batch_second]}
            ),
            "/v1/evaluate/batch",
        )
        print("/v1/evaluate/batch", [item["decision"] for item in json_body(batch)["results"]])

        for name, expected in SCENARIOS.items():
            path = f"/v1/scenarios/{name}/run"
            scenario = request_with_retry(
                lambda name=name: client.post(base + f"/v1/scenarios/{name}/run?seed=42"), path
            )
            decision = json_body(scenario)["decision"]
            assert decision == expected, f"{name}: expected {expected}, got {decision}"
            print(f"/v1/scenarios/{name}/run", decision)

        created = request_with_retry(
            lambda: client.post(base + "/v1/scenarios/normal_navigation/run?seed=42"),
            "/v1/scenarios/normal_navigation/run",
        )
        evaluation_id = json_body(created)["evaluation_id"]
        fetched = request_with_retry(
            lambda: client.get(base + f"/v1/evaluations/{evaluation_id}"),
            "/v1/evaluations/{evaluation_id}",
        )
        print("/v1/evaluations/{evaluation_id}", json_body(fetched)["decision"])

        judge = request_with_retry(lambda: client.post(base + "/v1/judge-test"), "/v1/judge-test")
        judge_body = json_body(judge)
        assert judge_body["passed"] is True
        print("/v1/judge-test", judge_body["passed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
