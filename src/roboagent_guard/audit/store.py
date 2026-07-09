from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from roboagent_guard.audit.hashing import sha256_digest, stable_json
from roboagent_guard.models.audit import AuditRecord
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.models.responses import EvaluationResponse


class AuditStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.previous_hash = self._last_hash()

    def append(self, request: EvaluationRequest, response: EvaluationResponse) -> AuditRecord:
        with self._lock:
            self.previous_hash = self._last_hash()
            record = AuditRecord(
                evaluation_id=response.evaluation_id,
                request_id=request.request_id,
                input_digest=sha256_digest(request),
                component_results=response.component_results,
                final_decision=response.decision,
                recommended_action=response.recommended_action.model_dump(mode="json"),
                policy_version=response.policy_version,
                simulation_seed=request.simulation_seed,
                previous_hash=self.previous_hash,
            )
            payload = record.model_dump(mode="json", exclude={"record_hash"})
            record.record_hash = sha256_digest(payload)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(stable_json(record) + "\n")
            self.previous_hash = record.record_hash
            return record

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [
            json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line
        ]

    def _last_hash(self) -> str:
        records = self.records()
        if not records:
            return "genesis"
        return str(records[-1]["record_hash"])
