from __future__ import annotations

import math
import random

from roboagent_guard.models.decisions import ActionType, Surface
from roboagent_guard.models.requests import Action
from roboagent_guard.policies.scoring import clamp
from roboagent_guard.simulator.state import TwinState


class DigitalTwin:
    def transition(
        self, state: TwinState, action: Action, seed: int, apply_action: bool
    ) -> TwinState:
        if not apply_action:
            return state.model_copy(deep=True)

        rng = random.Random(seed)
        next_state = state.model_copy(deep=True)

        if action.type == ActionType.STOP:
            next_state.linear_speed_mps = 0.0
            next_state.angular_speed_rps = 0.0
            return next_state

        if action.type == ActionType.SLOW_DOWN:
            next_state.linear_speed_mps = min(action.linear_speed_mps or 0.1, 0.15)
            next_state.angular_speed_rps = action.angular_speed_rps
        elif action.type == ActionType.RELOCALIZE:
            next_state.linear_speed_mps = 0.0
            next_state.angular_speed_rps = 0.0
            next_state.localization_mode = "relocalized"
            next_state.slam_inlier_ratio = clamp(
                next_state.slam_inlier_ratio + 0.25 + rng.random() * 0.05
            )
            next_state.localization_confidence = clamp(
                next_state.localization_confidence + 0.25 + rng.random() * 0.05
            )
        elif action.type == ActionType.DISABLE_STORAGE:
            next_state.raw_storage_enabled = False
        elif action.type == ActionType.SAVE_MAP:
            next_state.mapping_enabled = True
        elif action.type == ActionType.UPDATE_MAP:
            next_state.mapping_enabled = True
            next_state.map_update_count += 1
        elif action.type == ActionType.SHARE_SENSOR_SUMMARY:
            next_state.sensor_summary_shared = True
            next_state.last_recipient_id = action.recipient_id
        elif action.type == ActionType.SHARE_RAW_CAMERA:
            next_state.raw_camera_shared = True
            next_state.last_recipient_id = action.recipient_id
        elif action.type == ActionType.ROTATE:
            next_state.angular_speed_rps = action.angular_speed_rps
            next_state.heading_rad = round(next_state.heading_rad + action.angular_speed_rps, 6)
        elif action.type == ActionType.NAVIGATE:
            speed = action.linear_speed_mps
            next_state.linear_speed_mps = speed
            next_state.angular_speed_rps = action.angular_speed_rps
            if action.target is not None:
                dx = action.target.x - next_state.x
                dy = action.target.y - next_state.y
                distance = math.sqrt(dx * dx + dy * dy)
                travel = min(distance, max(speed, 0.0))
                if distance > 0:
                    next_state.x = round(next_state.x + dx / distance * travel, 6)
                    next_state.y = round(next_state.y + dy / distance * travel, 6)
                    next_state.heading_rad = round(math.atan2(dy, dx), 6)
            next_state.battery_percent = clamp(
                next_state.battery_percent - (0.08 + speed * 0.35), 0, 100
            )
        elif action.type == ActionType.RETURN_TO_BASE:
            next_state.x = 0.0
            next_state.y = 0.0
            next_state.battery_percent = clamp(next_state.battery_percent - 0.2, 0, 100)

        if next_state.surface == Surface.UNEVEN:
            next_state.localization_confidence = clamp(next_state.localization_confidence - 0.02)
        if next_state.illumination_lux < 20:
            next_state.slam_inlier_ratio = clamp(next_state.slam_inlier_ratio - 0.02)
        return next_state
