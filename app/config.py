from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
DEVELOPMENT_ENVIRONMENTS = {"development", "dev"}
PRODUCTION_ENVIRONMENTS = {"production", "prod"}


def load_app_environment() -> None:
    """Load the project .env before services inspect their configuration.

    Real process environment variables keep their normal precedence so a
    deployment can safely override local file values.
    """

    load_dotenv(dotenv_path=ENV_FILE, override=False)


def environment_values() -> set[str]:
    return {
        value.strip().lower()
        for value in (os.getenv("APP_ENV", ""), os.getenv("FLASK_ENV", ""))
        if value.strip()
    }


def application_environment() -> str:
    values = environment_values()
    if values & PRODUCTION_ENVIRONMENTS:
        return "production"
    if values & DEVELOPMENT_ENVIRONMENTS:
        return "development"
    return next(iter(values), "development")


def is_development_environment() -> bool:
    values = environment_values()
    return bool(values & DEVELOPMENT_ENVIRONMENTS) and not bool(
        values & PRODUCTION_ENVIRONMENTS
    )


load_app_environment()
