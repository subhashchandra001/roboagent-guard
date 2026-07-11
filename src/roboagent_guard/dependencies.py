from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from roboagent_guard.audit.store import AuditStore
from roboagent_guard.config import Settings, get_settings
from roboagent_guard.models.responses import EvaluationResponse
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard


@dataclass
class AppState:
    settings: Settings = field(default_factory=get_settings)
    replay_guard: ReplayGuard = field(default_factory=ReplayGuard)
    token_store: ApprovalTokenStore = field(default_factory=ApprovalTokenStore)
    evaluations: dict[str, EvaluationResponse] = field(default_factory=dict)
    _audit_store: AuditStore | None = None
    _audit_store_lock: Lock = field(default_factory=Lock)

    def audit_store(self) -> AuditStore:
        with self._audit_store_lock:
            if self._audit_store is None or self._audit_store.path != self.settings.audit_path:
                self._audit_store = AuditStore(self.settings.audit_path)
        return self._audit_store


app_state = AppState()


def get_app_state() -> AppState:
    return app_state
