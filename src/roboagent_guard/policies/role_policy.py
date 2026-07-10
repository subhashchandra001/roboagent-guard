from roboagent_guard.models.decisions import ActionType, CallerRole

ROLE_ACTIONS: dict[CallerRole, set[ActionType]] = {
    CallerRole.PLANNER: {
        ActionType.NAVIGATE,
        ActionType.STOP,
        ActionType.SLOW_DOWN,
        ActionType.RELOCALIZE,
        ActionType.ROTATE,
        ActionType.RETURN_TO_BASE,
    },
    CallerRole.MAPPING_AGENT: {ActionType.SAVE_MAP, ActionType.UPDATE_MAP},
    CallerRole.PRIVACY_AGENT: {
        ActionType.SHARE_SENSOR_SUMMARY,
        ActionType.DISABLE_STORAGE,
    },
    CallerRole.SUPERVISOR: set(ActionType) - {ActionType.SHARE_RAW_CAMERA},
    CallerRole.OBSERVER: set(),
    CallerRole.ROBOT: {ActionType.STOP, ActionType.RELOCALIZE, ActionType.DISABLE_STORAGE},
    CallerRole.MALICIOUS_AGENT: set(),
}

RAW_CAMERA_ROLES = {CallerRole.SUPERVISOR}
MAP_SAVE_ROLES = {CallerRole.MAPPING_AGENT, CallerRole.SUPERVISOR}
STORAGE_ROLES = {CallerRole.MAPPING_AGENT, CallerRole.SUPERVISOR}
PRIVILEGED_ROLES = {
    CallerRole.MAPPING_AGENT,
    CallerRole.PRIVACY_AGENT,
    CallerRole.ROBOT,
    CallerRole.SUPERVISOR,
}

CALLER_ROLE_REGISTRY: dict[str, CallerRole] = {
    "planner-agent-01": CallerRole.PLANNER,
    "planner-01": CallerRole.PLANNER,
    "mapping-agent-01": CallerRole.MAPPING_AGENT,
    "privacy-agent-01": CallerRole.PRIVACY_AGENT,
    "robot-01": CallerRole.ROBOT,
    "supervisor-01": CallerRole.SUPERVISOR,
    "supervisor-demo": CallerRole.SUPERVISOR,
    "unknown-agent": CallerRole.OBSERVER,
}


def allowed_actions_for(role: CallerRole) -> set[ActionType]:
    return ROLE_ACTIONS.get(role, set())


def registered_role_for(caller_id: str) -> CallerRole | None:
    return CALLER_ROLE_REGISTRY.get(caller_id)
