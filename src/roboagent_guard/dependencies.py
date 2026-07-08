from __future__ import annotations

from dataclasses import dataclass, field

from roboagent_guard.audit.store import AuditStore
from roboagent_guard.config import Settings, get_settings
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.replay_guard import ReplayGuard


@dataclass
class AppState:
    settings: Settings = field(default_factory=get_settings)
    replay_guard: ReplayGuard = field(default_factory=ReplayGuard)
    token_store: ApprovalTokenStore = field(default_factory=ApprovalTokenStore)
    evaluations: dict[str, object] = field(default_factory=dict)

    def audit_store(self) -> AuditStore:
        return AuditStore(self.settings.audit_path)


app_state = AppState()


def get_app_state() -> AppState:
    return app_state
