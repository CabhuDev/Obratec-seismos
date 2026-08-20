from __future__ import annotations

from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEISMOS_", env_file=".env", extra="ignore")

    ign_feed_url: str = (
        "https://www.ign.es/web/resources/sismologia/tproximos/terremotos.js"
    )
    ign_allowed_hosts: str = "www.ign.es"
    ign_timeout_seconds: float = Field(default=10.0, gt=0, le=30)
    ign_max_response_bytes: int = Field(default=5_000_000, ge=1, le=50_000_000)
    cache_ttl_seconds: int = Field(default=120, ge=30, le=900)
    upstream_retry_seconds: int = Field(default=30, ge=1, le=300)
    cors_origins: str = "http://localhost:5173"

    @model_validator(mode="after")
    def validate_ign_feed_url(self) -> Settings:
        parsed = urlsplit(self.ign_feed_url)
        allowed_hosts = {
            host.strip().lower().rstrip(".")
            for host in self.ign_allowed_hosts.split(",")
            if host.strip()
        }
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if (
            parsed.scheme.lower() != "https"
            or not hostname
            or hostname not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "IGN feed URL must use HTTPS and a hostname in SEISMOS_IGN_ALLOWED_HOSTS"
            )
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
