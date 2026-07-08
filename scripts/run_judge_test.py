from __future__ import annotations

import argparse
from collections.abc import Callable
from time import sleep

import httpx
from fastapi.testclient import TestClient

from roboagent_guard.app import app
from roboagent_guard.models.decisions import Decision
from roboagent_guard.simulator.scenarios import scenario_request


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


def local_check() -> int:
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    skill = client.get("/SKILL.md")
    assert skill.status_code == 200
    assert client.get("/skill.md").status_code == 200
    for phrase in [
        "Call `GET /health` first.",
        "POST /v1/evaluate",
        "If the decision is `block`, execute nothing.",
    ]:
        assert phrase in skill.text
    assert client.get("/capabilities").status_code == 200
    safe = scenario_request("normal_navigation", 42).model_dump(mode="json")
    safe["request_id"] = "judge-local-safe"
    safe["nonce"] = "judge-local-safe-nonce"
    unsafe = scenario_request("combined_safety_privacy_crisis", 42).model_dump(mode="json")
    unsafe["request_id"] = "judge-local-unsafe"
    unsafe["nonce"] = "judge-local-unsafe-nonce"
    safe_response = client.post("/v1/evaluate", json=safe).json()
    unsafe_response = client.post("/v1/evaluate", json=unsafe).json()
    assert safe_response["decision"] == Decision.APPROVE
    assert unsafe_response["decision"] in {Decision.MODIFY, Decision.BLOCK}
    print("judge test passed")
    return 0


def live_check(base_url: str) -> int:
    base = base_url.rstrip("/")
    with httpx.Client(timeout=75.0) as client:
        assert (
            request_with_retry(lambda: client.get(f"{base}/health"), "/health").status_code
            == 200
        )
        assert (
            request_with_retry(lambda: client.get(f"{base}/SKILL.md"), "/SKILL.md").status_code
            == 200
        )
        assert (
            request_with_retry(lambda: client.get(f"{base}/skill.md"), "/skill.md").status_code
            == 200
        )
        assert (
            request_with_retry(
                lambda: client.get(f"{base}/capabilities"), "/capabilities"
            ).status_code
            == 200
        )
        safe = scenario_request("normal_navigation", 42).model_dump(mode="json")
        safe["request_id"] = "judge-live-safe"
        safe["nonce"] = "judge-live-safe-nonce"
        unsafe = scenario_request("combined_safety_privacy_crisis", 42).model_dump(mode="json")
        unsafe["request_id"] = "judge-live-unsafe"
        unsafe["nonce"] = "judge-live-unsafe-nonce"
        safe_response = request_with_retry(
            lambda: client.post(f"{base}/v1/evaluate", json=safe), "/v1/evaluate safe"
        )
        safe_response.raise_for_status()
        unsafe_response = request_with_retry(
            lambda: client.post(f"{base}/v1/evaluate", json=unsafe), "/v1/evaluate unsafe"
        )
        unsafe_response.raise_for_status()
        assert safe_response.json()["decision"] == Decision.APPROVE
        assert unsafe_response.json()["decision"] == Decision.BLOCK
        scenario = request_with_retry(
            lambda: client.post(f"{base}/v1/scenarios/normal_navigation/run?seed=42"),
            "/v1/scenarios/normal_navigation/run",
        )
        scenario.raise_for_status()
        assert scenario.json()["decision"] == Decision.APPROVE
    print("live judge test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if args.local:
        return local_check()
    if args.base_url:
        return live_check(args.base_url)
    parser.error("use --local or --base-url")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
