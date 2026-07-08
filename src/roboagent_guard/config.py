from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    public_base_url: str = Field(default="http://127.0.0.1:8000", alias="PUBLIC_BASE_URL")
    policy_version: str = Field(default="1.0.0", alias="POLICY_VERSION")
    audit_path: Path = Field(default=Path("artifacts/traces/audit.jsonl"), alias="AUDIT_PATH")
    nanda_trace_dir: Path = Field(default=Path("artifacts/nanda_traces"), alias="NANDA_TRACE_DIR")


@lru_cache
def get_settings() -> Settings:
    return Settings()
