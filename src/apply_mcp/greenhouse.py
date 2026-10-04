from __future__ import annotations

import base64
import logging
from typing import Any

import aiohttp

from apply_mcp.config import cfg

logger = logging.getLogger(__name__)

BASE = "https://boards-api.greenhouse.io/v1/boards"


async def fetch_jobs(board_token: str, content: bool = True) -> list[dict[str, Any]]:
    params = {"content": "true"} if content else None
    url = f"{BASE}/{board_token}/jobs"
    timeout = aiohttp.ClientTimeout(total=cfg.request_timeout_s)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                logger.warning("Board not found: %s", board_token)
                return []
            resp.raise_for_status()
            data = await resp.json()
            return list(data.get("jobs", []))


async def fetch_job(board_token: str, job_id: int | str) -> dict[str, Any]:
    url = f"{BASE}/{board_token}/jobs/{job_id}"
    params = {"questions": "true"}
    timeout = aiohttp.ClientTimeout(total=cfg.request_timeout_s)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


def application_url(board_token: str, job_id: int | str) -> str:
    return f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"


def _auth_header(api_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def submit_application_api(
    board_token: str,
    job_id: int | str,
    fields: dict[str, Any],
    resume_path: str | None,
    api_key: str,
) -> dict[str, Any]:
    """
    Submit via Greenhouse Job Board API.

    Requires the employer's Job Board API key (not a candidate login password).
    Most candidates should use manual submit instead.
    """
    if not api_key:
        raise ValueError(
            "GREENHOUSE_JOB_BOARD_API_KEY is required for API submit. "
            "Use mode='manual' instead, or leave API submit disabled."
        )

    url = f"{BASE}/{board_token}/jobs/{job_id}"
    timeout = aiohttp.ClientTimeout(total=cfg.request_timeout_s)
    form = aiohttp.FormData()
    for key, value in fields.items():
        if value is None:
            continue
        form.add_field(key, str(value))

    if resume_path:
        with open(resume_path, "rb") as resume_file:
            resume_bytes = resume_file.read()
        form.add_field(
            "resume",
            resume_bytes,
            filename="resume.pdf",
            content_type="application/pdf",
        )

    headers = _auth_header(api_key)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, data=form, headers=headers) as resp:
            text = await resp.text()
            if resp.status >= 400:
                return {
                    "ok": False,
                    "status": resp.status,
                    "error": text[:2000],
                }
            try:
                body = await resp.json(content_type=None)
            except Exception:
                body = {"raw": text[:2000]}
            return {"ok": True, "status": resp.status, "response": body}
