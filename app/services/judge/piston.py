"""Piston API client for fast, serverless, sandbox code execution.

Piston API endpoint: https://emkc.org/api/v2/piston/execute
No API keys required. Supports Python, C++, C, Java, JavaScript, Rust, Go, etc.
"""
from __future__ import annotations

import asyncio
import time
from typing import List, Optional
import httpx

from app.core.config import settings
from app.services.judge.base import (
    JudgeJob,
    JudgeOutcome,
    STATUS_ACCEPTED,
    STATUS_WRONG_ANSWER,
    STATUS_TIME_LIMIT,
    STATUS_COMPILATION_ERROR,
    STATUS_INTERNAL_ERROR,
)

# Map internal language keys to Piston language aliases and versions
PISTON_LANGUAGE_MAP = {
    "python": {"language": "python", "version": "3.10.0"},
    "python3": {"language": "python", "version": "3.10.0"},
    "py": {"language": "python", "version": "3.10.0"},
    "cpp": {"language": "c++", "version": "10.2.0"},
    "c++": {"language": "c++", "version": "10.2.0"},
    "c": {"language": "c", "version": "10.2.0"},
    "java": {"language": "java", "version": "15.0.2"},
    "javascript": {"language": "javascript", "version": "18.15.0"},
    "js": {"language": "javascript", "version": "18.15.0"},
    "node": {"language": "javascript", "version": "18.15.0"},
    "rust": {"language": "rust", "version": "1.68.2"},
    "go": {"language": "go", "version": "1.16.2"},
}


class PistonClient:
    """Interchangeable drop-in judge backend using the public Piston API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or getattr(settings, "PISTON_URL", "https://emkc.org/api/v2/piston/execute")).rstrip("/")
        # Concurrency limit for parallel test case requests
        self._sem = asyncio.Semaphore(8)

    async def judge_one(self, job: JudgeJob, client: httpx.AsyncClient) -> JudgeOutcome:
        """Execute a single test case job on Piston and compute the outcome."""
        lang_info = PISTON_LANGUAGE_MAP.get(job.language.lower(), {"language": job.language.lower(), "version": "*"})

        payload = {
            "language": lang_info["language"],
            "version": lang_info["version"],
            "files": [{"content": job.source_code}],
            "stdin": job.stdin or "",
            "run_timeout": int(job.wall_time_limit * 1000),
            "compile_timeout": 10000,
        }

        t0 = time.perf_counter()
        async with self._sem:
            try:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    timeout=httpx.Timeout(connect=8.0, read=job.wall_time_limit + 5.0, write=8.0, pool=15.0),
                )
            except httpx.TimeoutException:
                elapsed = time.perf_counter() - t0
                return JudgeOutcome(
                    status_id=STATUS_TIME_LIMIT,
                    status="Time Limit Exceeded",
                    time=elapsed,
                    message=f"Execution timed out (> {job.wall_time_limit}s)",
                )
            except Exception as exc:
                return JudgeOutcome(
                    status_id=STATUS_INTERNAL_ERROR,
                    status="Internal Error",
                    message=f"Piston connection error: {exc}",
                )

        elapsed = time.perf_counter() - t0

        if resp.status_code != 200:
            return JudgeOutcome(
                status_id=STATUS_INTERNAL_ERROR,
                status="Internal Error",
                message=f"Piston returned HTTP {resp.status_code}: {resp.text}",
            )

        data = resp.json()

        # Check compilation errors (C, C++, Java, Rust)
        compile_stage = data.get("compile")
        if compile_stage and compile_stage.get("code") not in (0, None):
            compile_err = compile_stage.get("stderr") or compile_stage.get("output") or "Compilation failed"
            return JudgeOutcome(
                status_id=STATUS_COMPILATION_ERROR,
                status="Compilation Error",
                compile_output=compile_err,
                time=elapsed,
                message="Compilation Error",
            )

        run_stage = data.get("run", {})
        stdout = run_stage.get("stdout", "")
        stderr = run_stage.get("stderr", "")
        exit_code = run_stage.get("code")
        signal = run_stage.get("signal")

        # Check for Runtime / Signal errors
        if signal == "SIGKILL" or "timed out" in stderr.lower():
            return JudgeOutcome(
                status_id=STATUS_TIME_LIMIT,
                status="Time Limit Exceeded",
                stdout=stdout,
                stderr=stderr,
                time=elapsed,
                message="Time Limit Exceeded",
            )

        if exit_code not in (0, None):
            return JudgeOutcome(
                status_id=STATUS_WRONG_ANSWER if not stderr else 11,  # 11 = Runtime Error (NZEC)
                status="Runtime Error" if stderr else "Runtime Error (NZEC)",
                stdout=stdout,
                stderr=stderr,
                time=elapsed,
                message=stderr or f"Process exited with non-zero code {exit_code}",
            )

        # Check stdout vs expected output
        expected = job.expected_output or ""
        actual_norm = stdout.strip()
        expected_norm = expected.strip()

        if actual_norm == expected_norm:
            return JudgeOutcome(
                status_id=STATUS_ACCEPTED,
                status="Accepted",
                stdout=stdout,
                stderr=stderr,
                time=elapsed,
                message="Accepted",
            )
        else:
            return JudgeOutcome(
                status_id=STATUS_WRONG_ANSWER,
                status="Wrong Answer",
                stdout=stdout,
                stderr=stderr,
                time=elapsed,
                message="Output mismatch",
            )

    async def run_batch(self, jobs: List[JudgeJob]) -> List[JudgeOutcome]:
        """Execute a batch of test cases concurrently."""
        if not jobs:
            return []

        async with httpx.AsyncClient() as client:
            tasks = [self.judge_one(job, client) for job in jobs]
            return await asyncio.gather(*tasks)

    async def health(self) -> bool:
        """Alias for admin health check endpoint."""
        return await self.health_check()

    async def health_check(self) -> bool:
        """Verify that Piston endpoint is reachable."""
        try:
            runtimes_url = self.base_url.replace("/execute", "/runtimes")
            async with httpx.AsyncClient(timeout=6.0) as client:
                r = await client.get(runtimes_url)
                return r.status_code == 200
        except Exception:
            return False
