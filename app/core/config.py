from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Platform API"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:244901@localhost/mplbe"
    ADMIN_PASSCODE: str = "SunSunSunday"

    # ── Frontend pairing ─────────────────────────────────────────────────────
    # Folder the API serves at /ui for single-origin event-day running.
    # Empty = <this repo>/frontend (classic monorepo layout). When the frontend
    # lives in its own repo, point this at that checkout, e.g. "../MPL-FE".
    # If the folder does not exist, /ui is simply not mounted (API-only mode).
    FRONTEND_DIR: str = ""

    # ── Event clock ──────────────────────────────────────────────────────────
    # 120 minutes. Admin can add extra minutes per team (extra_time_seconds).
    EVENT_DURATION_SECONDS: int = 7200

    # ── Judge (code execution sandbox) ───────────────────────────────────────
    # "piston" -> Piston cloud / local API (https://emkc.org/api/v2/piston/execute) - RECOMMENDED
    # "mock"   -> local fake judge for development
    JUDGE_BACKEND: str = "piston"
    PISTON_URL: str = "https://emkc.org/api/v2/piston/execute"

    # DEV ONLY: lets the mock judge execute python locally for offline testing
    MOCK_EXECUTE_PYTHON: bool = True

    # ── Limits / guardrails ──────────────────────────────────────────────────
    DEFAULT_CPU_TIME_LIMIT: float = 5.0        # seconds per test case
    DEFAULT_WALL_TIME_LIMIT: float = 10.0
    DEFAULT_MEMORY_LIMIT_KB: int = 256_000
    MAX_SOURCE_BYTES: int = 64_000
    SUBMIT_COOLDOWN_SECONDS: int = 5           # protects the judge queue, NOT an attempt limit

    # ── Languages ────────────────────────────────────────────────────────────
    LANGUAGE_NAMES: Dict[str, str] = {
        "python": "Python (3.10)",
        "c": "C (GCC)",
        "cpp": "C++ (GCC)",
        "java": "Java (OpenJDK)",
    }

    class Config:
        env_file = ".env"


settings = Settings()
