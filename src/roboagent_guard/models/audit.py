from __future__ import annotations

from typing import Any

from pydantic import Field

from roboagent_guard.models.common import StrictBaseModel


class AuditRecord(StrictBaseModel):
    evaluation_id: str
    request_id: str
    input_digest: str
    component_results: dict[str, Any]
    final_decision: str
    recommended_action: dict[str, Any]
    policy_version: str
    simulation_seed: int
    previous_hash: str
    record_hash: str = Field(default="")
