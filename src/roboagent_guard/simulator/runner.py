from __future__ import annotations

from roboagent_guard.agents.authorization import AuthorizationAgent
from roboagent_guard.agents.physical_risk import PhysicalRiskAgent
from roboagent_guard.agents.privacy import PrivacyAgent
from roboagent_guard.agents.slam_reliability import SlamReliabilityAgent
from roboagent_guard.agents.supervisor import SupervisorAgent
from roboagent_guard.audit.hashing import sha256_digest
from roboagent_guard.audit.store import AuditStore
from roboagent_guard.config import Settings
from roboagent_guard.integrations.nanda_trace import export_nanda_trace
from roboagent_guard.models.common import ComponentResult, Violation
from roboagent_guard.models.decisions import Decision, RiskLevel
from roboagent_guard.models.requests import EvaluationRequest
from roboagent_guard.models.responses import DigitalTwinResult, EvaluationResponse
from roboagent_guard.security.approval_tokens import ApprovalTokenStore
from roboagent_guard.security.freshness import FreshnessGuard
from roboagent_guard.security.replay_guard import ReplayGuard
from roboagent_guard.simulator.digital_twin import DigitalTwin
from roboagent_guard.simulator.state import state_from_request


class EvaluationEngine:
    def __init__(
        self,
        settings: Settings,
        replay_guard: ReplayGuard,
        token_store: ApprovalTokenStore,
        audit_store: AuditStore | None = None,
    ) -> None:
        self.settings = settings
        self.replay_guard = replay_guard
        self.token_store = token_store
        self.audit_store = audit_store
        self.authorization = AuthorizationAgent()
        self.physical = PhysicalRiskAgent()
        self.slam = SlamReliabilityAgent()
        self.privacy = PrivacyAgent()
        self.supervisor = SupervisorAgent()
        self.twin = DigitalTwin()

    def evaluate(self, request: EvaluationRequest, audit: bool = True) -> EvaluationResponse:
        replay = self.replay_guard.check(request)
        freshness = FreshnessGuard(now=request.evaluation_time or request.timestamp).check(request)
        token = self.token_store.consume_if_present(request.approval.token)
        components = {
            "authorization": self.authorization.evaluate(request),
            "physical_risk": self.physical.evaluate(request),
            "slam_reliability": self.slam.evaluate(request),
            "privacy": self.privacy.evaluate(request),
            "replay_and_freshness": self._replay_freshness_component(replay, freshness),
        }
        decision = self.supervisor.decide(
            request,
            components,
            freshness_passed=freshness.passed,
            replay_detected=replay.replay_detected,
            token_violations=token.violations,
        )
        previous_state = state_from_request(request)
        apply_action = decision.decision in {
            Decision.APPROVE,
            Decision.APPROVE_WITH_CONSTRAINTS,
            Decision.MODIFY,
        }
        action_to_apply = (
            request.action
            if decision.decision in {Decision.APPROVE, Decision.APPROVE_WITH_CONSTRAINTS}
            else decision.recommended_action
        )
        resulting_state = self.twin.transition(
            previous_state, action_to_apply, request.simulation_seed, apply_action
        )
        evaluation_id = (
            "eval-"
            + sha256_digest(
                {
                    "request_id": request.request_id,
                    "nonce": request.nonce,
                    "seed": request.simulation_seed,
                    "decision": decision.decision,
                }
            )[:12]
        )
        response = EvaluationResponse(
            evaluation_id=evaluation_id,
            request_id=request.request_id,
            decision=decision.decision,
            risk_level=decision.risk_level,
            risk_score=decision.risk_score,
            slam_risk_score=components["slam_reliability"].score,
            privacy_risk_score=components["privacy"].score,
            authorization_passed=components["authorization"].decision != Decision.BLOCK,
            freshness_passed=freshness.passed,
            replay_detected=replay.replay_detected,
            human_approval_required=decision.human_approval_required,
            recommended_action=decision.recommended_action,
            constraints=decision.constraints,
            reasons=decision.reasons,
            violation_codes=decision.violation_codes,
            component_results=components,
            digital_twin=DigitalTwinResult(
                previous_state=previous_state.model_dump(mode="json"),
                resulting_state=resulting_state.model_dump(mode="json"),
                action_applied=apply_action,
            ),
            policy_version=self.settings.policy_version,
            trace_hash="pending",
        )
        response.trace_hash = sha256_digest(
            response.model_dump(mode="json", exclude={"trace_hash"})
        )
        self.replay_guard.record(request, blocked=response.decision == Decision.BLOCK)
        if audit and self.audit_store is not None:
            self.audit_store.append(request, response)
            export_nanda_trace(request, response, self.settings.nanda_trace_dir)
        return response

    @staticmethod
    def _replay_freshness_component(replay, freshness) -> ComponentResult:
        violations = [
            Violation(
                code=code,
                message="Replay or freshness guard violation.",
                observed=True,
                threshold=False,
            )
            for code in [*replay.violations, *freshness.violations]
        ]
        decision = (
            Decision.BLOCK
            if replay.replay_detected
            else (Decision.REQUEST_HUMAN_APPROVAL if not freshness.passed else Decision.APPROVE)
        )
        return ComponentResult(
            name="replay_and_freshness",
            score=1.0 if violations else 0.0,
            level=(
                RiskLevel.CRITICAL
                if replay.replay_detected
                else (RiskLevel.HIGH if not freshness.passed else RiskLevel.LOW)
            ),
            decision=decision,
            violations=violations,
            recommended_controls=["do_not_retry_nonce"] if replay.replay_detected else [],
            evidence={
                "replay_detected": replay.replay_detected,
                "freshness_passed": freshness.passed,
                "codes": [v.code for v in violations],
            },
            reasons=["Replay or freshness violation detected."]
            if violations
            else ["Request is fresh and unique."],
        )


def run_named_scenario(
    engine: EvaluationEngine, name: str, request: EvaluationRequest
) -> EvaluationResponse:
    if name == "replayed_approved_action":
        engine.evaluate(request.model_copy(deep=True), audit=False)
        return engine.evaluate(request.model_copy(deep=True), audit=True)
    return engine.evaluate(request)
