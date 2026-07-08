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


def allowed_actions_for(role: CallerRole) -> set[ActionType]:
    return ROLE_ACTIONS.get(role, set())
