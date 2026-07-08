from __future__ import annotations

import math
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def finite_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    return value


FiniteFloat = Annotated[float, AfterValidator(finite_float)]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class Target(StrictBaseModel):
    x: FiniteFloat = Field(ge=-1000, le=1000)
    y: FiniteFloat = Field(ge=-1000, le=1000)


class Violation(StrictBaseModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=300)
    observed: Any | None = None
    threshold: Any | None = None


class ComponentResult(StrictBaseModel):
    name: str
    score: FiniteFloat = Field(ge=0.0, le=1.0)
    level: str
    decision: str
    violations: list[Violation] = Field(default_factory=list)
    recommended_controls: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


class HealthResponse(StrictBaseModel):
    status: str
    service: str
    version: str
