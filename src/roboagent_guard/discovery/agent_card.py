from __future__ import annotations

from roboagent_guard.models.decisions import Decision


def agent_card(base_url: str, version: str) -> dict[str, object]:
    base = base_url.rstrip("/")
    return {
        "name": "RoboAgent Guard",
        "description": (
            "Evaluates proposed mobile-robot actions for physical, SLAM, authorization, "
            "replay, and privacy risks."
        ),
        "version": version,
        "base_url": base,
        "skill_url": f"{base}/SKILL.md",
        "health_url": f"{base}/health",
        "capabilities_url": f"{base}/capabilities",
        "primary_endpoint": {"method": "POST", "path": "/v1/evaluate"},
        "demo_endpoints": {
            "judge_skill_test": {"method": "POST", "path": "/v1/agent-skill-test"},
            "composed_mission_planner": {"method": "POST", "path": "/v1/compose/mission-plan"},
        },
        "supported_decisions": [item.value for item in Decision],
        "autonomy_model": {
            "default": "agent_autonomous",
            "human_intervention": "exception_only",
            "description": (
                "Agents can approve, constrain, modify, or block actions without human help. "
                "Human escalation is reserved for stale evidence or unresolved uncertainty."
            ),
        },
        "authentication": {
            "required": False,
            "note": (
                "Hackathon demonstration service. Caller authorization is represented in "
                "the request and verified against demonstration policy."
            ),
        },
    }
