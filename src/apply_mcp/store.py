from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from apply_mcp.config import cfg


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if not cfg.store_path.exists():
        return {"jobs": {}, "applications": {}, "audit": []}
    with cfg.store_path.open(encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict[str, Any]) -> None:
    cfg.store_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg.store_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)


def upsert_jobs(jobs: list[dict[str, Any]]) -> int:
    data = _load()
    count = 0
    for job in jobs:
        job_key = job["job_key"]
        data["jobs"][job_key] = {**job, "updated_at": _now()}
        count += 1
    _save(data)
    return count


def list_jobs(
    min_score_reasons: int = 0,
    search_term: str | None = None,
    max_items: int = 50,
) -> list[dict[str, Any]]:
    data = _load()
    jobs = list(data.get("jobs", {}).values())
    if search_term:
        needle = search_term.lower()
        jobs = [
            j
            for j in jobs
            if needle in (j.get("title") or "").lower()
            or needle in (j.get("company") or "").lower()
            or needle in (j.get("location") or "").lower()
        ]
    if min_score_reasons:
        jobs = [
            j
            for j in jobs
            if len(j.get("match_reasons") or []) >= min_score_reasons
        ]
    jobs.sort(key=lambda j: (j.get("title") or "", j.get("company") or ""))
    return jobs[:max_items]


def get_job(job_key: str) -> dict[str, Any] | None:
    return _load().get("jobs", {}).get(job_key)


def save_application(app: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    app_id = app.get("application_id") or str(uuid.uuid4())
    app["application_id"] = app_id
    app["updated_at"] = _now()
    if "created_at" not in app:
        app["created_at"] = _now()
    data["applications"][app_id] = app
    data.setdefault("audit", []).append(
        {
            "at": _now(),
            "event": "application_saved",
            "application_id": app_id,
            "status": app.get("status"),
        }
    )
    _save(data)
    return app


def get_application(application_id: str) -> dict[str, Any] | None:
    return _load().get("applications", {}).get(application_id)


def list_applications(max_items: int = 50) -> list[dict[str, Any]]:
    apps = list(_load().get("applications", {}).values())
    apps.sort(key=lambda a: a.get("updated_at") or "", reverse=True)
    return apps[:max_items]


def audit(event: str, **payload: Any) -> None:
    data = _load()
    data.setdefault("audit", []).append({"at": _now(), "event": event, **payload})
    _save(data)
