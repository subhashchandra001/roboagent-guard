from __future__ import annotations

from dataclasses import dataclass, field

from roboagent_guard.policies import hard_constraints as codes


@dataclass
class TokenResult:
    passed: bool
    violations: list[str] = field(default_factory=list)


class ApprovalTokenStore:
    def __init__(self, valid_tokens: set[str] | None = None) -> None:
        self.valid_tokens = valid_tokens or {"supervisor-demo-token"}
        self.consumed: set[str] = set()

    def consume_if_present(self, token: str | None) -> TokenResult:
        if token is None:
            return TokenResult(passed=True)
        if token in self.consumed:
            return TokenResult(passed=False, violations=[codes.REUSED_APPROVAL_TOKEN])
        if token not in self.valid_tokens:
            return TokenResult(passed=False, violations=[codes.FORGED_APPROVAL_TOKEN])
        self.consumed.add(token)
        return TokenResult(passed=True)
