from __future__ import annotations

from typing import Any


def reject_image_payloads(value: Any) -> None:
    """Reject obvious attempts to send image content instead of metadata flags."""
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"image", "image_data", "frame", "camera_frame", "base64_image"}:
                raise ValueError("actual image content is not accepted")
            reject_image_payloads(child)
    elif isinstance(value, list):
        for child in value:
            reject_image_payloads(child)
