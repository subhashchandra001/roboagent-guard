from __future__ import annotations

import argparse
from collections.abc import Callable
from time import sleep
from typing import Any
from uuid import uuid4

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


def unique_safe_request(run_id: str, label: str) -> dict[str, Any]:
    request = scenario_request("normal_navigation", 42).model_dump(mode="json", exclude_none=True)
    request["request_id"] = f"{label}-{run_id}"
    request["nonce"] = f"{label}-nonce-{run_id}"
    request["action"]["target"]["x"] = 1.0 + (int(run_id[:6], 16) % 1000) / 1_000_000
    return request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    run_id = uuid4().hex[:12]
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

        request = unique_safe_request(run_id, "live-smoke-safe")
        response = request_with_retry(
            lambda: client.post(base + "/v1/evaluate", json=request), "/v1/evaluate"
        )
        decision = json_body(response)["decision"]
        assert decision == "approve", f"/v1/evaluate expected approve, got {decision}"
        print("/v1/evaluate", decision)

        batch_first = unique_safe_request(run_id, "live-batch-1")
        batch_second = scenario_request("unauthorized_camera_request", 42).model_dump(
            mode="json", exclude_none=True
        )
        batch_second["request_id"] = f"live-batch-2-{run_id}"
        batch_second["nonce"] = f"live-batch-nonce-2-{run_id}"
        batch = request_with_retry(
            lambda: client.post(
                base + "/v1/evaluate/batch", json={"requests": [batch_first, batch_second]}
            ),
            "/v1/evaluate/batch",
        )
        batch_decisions = [item["decision"] for item in json_body(batch)["results"]]
        assert batch_decisions == ["approve", "block"], batch_decisions
        print("/v1/evaluate/batch", batch_decisions)

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

        receipt = request_with_retry(
            lambda: client.get(base + f"/v1/receipts/{evaluation_id}"),
            "/v1/receipts/{evaluation_id}",
        )
        receipt_body = json_body(receipt)
        assert receipt_body["evaluation_id"] == evaluation_id
        verified = request_with_retry(
            lambda: client.post(base + "/v1/receipts/verify", json=receipt_body),
            "/v1/receipts/verify",
        )
        verify_body = json_body(verified)
        assert verify_body["valid"] is True
        print("/v1/receipts/{evaluation_id}", verify_body["valid"])

        judge = request_with_retry(lambda: client.post(base + "/v1/judge-test"), "/v1/judge-test")
        judge_body = json_body(judge)
        assert judge_body["passed"] is True
        print("/v1/judge-test", judge_body["passed"])

        skill_test = request_with_retry(
            lambda: client.post(base + "/v1/agent-skill-test"), "/v1/agent-skill-test"
        )
        skill_body = json_body(skill_test)
        assert skill_body["passed"] is True
        print("/v1/agent-skill-test", skill_body["passed"])

        composition = request_with_retry(
            lambda: client.post(base + "/v1/compose/mission-plan"),
            "/v1/compose/mission-plan",
        )
        composition_body = json_body(composition)
        assert composition_body["passed"] is True
        print("/v1/compose/mission-plan", composition_body["passed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
