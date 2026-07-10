from __future__ import annotations

import base64
import binascii
import re
from typing import Any

IMAGE_KEYS = {
    "base64_image",
    "camera_frame",
    "camera_image",
    "frame",
    "image",
    "image_data",
    "jpeg",
    "jpg",
    "png",
    "raw_camera",
}
IMAGE_MAGIC_PREFIXES = (
    b"\xff\xd8\xff",
    b"\x89PNG\r\n\x1a\n",
    b"GIF87a",
    b"GIF89a",
    b"BM",
)
BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def _key_suggests_image_content(key: str) -> bool:
    lowered = key.lower()
    return (
        lowered in IMAGE_KEYS
        or lowered.endswith("_image")
        or lowered.endswith("_frame")
        or lowered.endswith("_photo")
    )


def _looks_like_image_bytes(data: bytes) -> bool:
    return data.startswith(IMAGE_MAGIC_PREFIXES) or (
        len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    )


def _looks_like_embedded_image(value: str) -> bool:
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered.startswith("data:image/"):
        return True
    if ";base64," in lowered and "image/" in lowered[:80]:
        return True

    payload = stripped.split(",", 1)[1] if "," in stripped else stripped
    compact = "".join(payload.split())
    if len(compact) < 64 or len(compact) % 4 != 0 or not BASE64_RE.match(compact):
        return False
    try:
        decoded = base64.b64decode(compact[:4096], validate=True)
    except (binascii.Error, ValueError):
        return False
    return _looks_like_image_bytes(decoded)


def reject_image_payloads(value: Any) -> None:
    """Reject obvious attempts to send image content instead of metadata flags."""
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if _key_suggests_image_content(lowered):
                raise ValueError("actual image content is not accepted")
            reject_image_payloads(child)
    elif isinstance(value, list):
        for child in value:
            reject_image_payloads(child)
    elif isinstance(value, str) and _looks_like_embedded_image(value):
        raise ValueError("actual image content is not accepted")
