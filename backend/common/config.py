"""Settings read from environment variables (never hard-coded)."""

import os
from dataclasses import dataclass, field


def _default_user_agent() -> str:
    return os.getenv(
        "SCRAPER_USER_AGENT",
        "InternRadar/0.1 (+https://github.com/kingzakaria/internradar)",
    )


@dataclass(frozen=True)
class Settings:
    user_agent: str = field(default_factory=_default_user_agent)
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "20"))
    # Minimum pause between two requests made by the same client (politeness).
    min_request_interval: float = float(os.getenv("MIN_REQUEST_INTERVAL", "1.0"))


settings = Settings()