from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from apply_mcp.config import cfg
from apply_mcp.draft import content_hash, draft_answers, job_matches_profile, strip_html
from apply_mcp.greenhouse import (
    application_url,
    fetch_job,
    fetch_jobs,
    submit_application_api,
)
from apply_mcp.profile_loader import load_companies, load_profile, resume_path
from apply_mcp import store

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("apply-mcp")

mcp = FastMCP(name="apply-mcp")


def _job_key(board_token: str, job_id: Any) -> str:
    return f"greenhouse:{board_token}:{job_id}"


@mcp.tool()
async def get_candidate_profile() -> dict:
    """
    Return the local candidate profile used for drafting applications.
    Includes resume path and whether email/phone/LinkedIn are filled in.
    """
    profile = load_profile()
    return {
        "full_name": profile.get("full_name"),
        "email_set": bool(profile.get("email")),
        "phone_set": bool(profile.get("phone")),
        "linkedin_set": bool(profile.get("linkedin_url")),
        "location": profile.get("location"),
        "target_roles": profile.get("target_roles"),
        "resume_path": profile.get("resume_path"),
        "experience_markdown": profile.get("experience_markdown"),
        "profile_path": str(cfg.profile_path),
        "missing_for_apply": [
            name
            for name, ok in [
                ("email", bool(profile.get("email"))),
                ("phone", bool(profile.get("phone"))),
                ("linkedin_url", bool(profile.get("linkedin_url"))),
                ("resume_pdf", bool(resume_path(profile))),
            ]
            if not ok
        ],
    }


@mcp.tool()
async def list_company_boards() -> list[dict]:
    """List configured Greenhouse company boards from candidate/companies.json."""
    return load_companies()


@mcp.tool()
async def discover_jobs(
    query: str | None = None,
    board_token: str | None = None,
    limit: int = 40,
) -> dict:
    """
    Discover jobs from configured Greenhouse boards (public Job Board API).

    Args:
        query: Optional text filter on title/company/location after fetch
        board_token: Optional single board to scan (e.g. "stripe")
        limit: Max matched jobs to return
    """
    profile = load_profile()
    boards = load_companies()
    if board_token:
        boards = [b for b in boards if b.get("board_token") == board_token] or [
            {
                "name": board_token,
                "ats": "greenhouse",
                "board_token": board_token,
            }
        ]

    matched: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for board in boards:
        token = board["board_token"]
        company = board.get("name") or token
        try:
            jobs = await fetch_jobs(token, content=True)
        except Exception as exc:  # noqa: BLE001
            errors.append({"board_token": token, "error": str(exc)})
            continue

        for job in jobs:
            ok, reasons = job_matches_profile(job, profile)
            if not ok:
                continue
            item = {
                "job_key": _job_key(token, job["id"]),
                "ats": "greenhouse",
                "company": company,
                "board_token": token,
                "job_id": job["id"],
                "title": job.get("title"),
                "location": (job.get("location") or {}).get("name"),
                "absolute_url": job.get("absolute_url")
                or application_url(token, job["id"]),
                "updated_at_remote": job.get("updated_at"),
                "match_reasons": reasons,
                "snippet": strip_html(job.get("content") or "")[:400],
            }
            matched.append(item)

    store.upsert_jobs(matched)
    if query:
        q = query.lower()
        matched = [
            j
            for j in matched
            if q in (j.get("title") or "").lower()
            or q in (j.get("company") or "").lower()
            or q in (j.get("location") or "").lower()
        ]

    matched = matched[:limit]
    return {
        "count": len(matched),
        "jobs": matched,
        "errors": errors,
        "note": "Discovery uses public Greenhouse board APIs. No candidate password needed.",
    }


@mcp.tool()
async def list_queue(query: str | None = None, limit: int = 40) -> dict:
    """List previously discovered matching jobs stored locally."""
    jobs = store.list_jobs(search_term=query, max_items=limit)
    return {"count": len(jobs), "jobs": jobs}


@mcp.tool()
async def prepare_application(job_key: str) -> dict:
    """
    Load Greenhouse questions for a job and draft answers from the local profile.

    Sensitive or unverified required questions are blocked for human input.
    Does not submit anything.
    """
    job_meta = store.get_job(job_key)
    if not job_meta:
        return {
            "error": f"Unknown job_key {job_key}. Run discover_jobs first.",
        }

    profile = load_profile()
    if not profile.get("email") or not profile.get("first_name"):
        return {
            "error": "candidate/profile.json is missing email or name. Fill those before preparing applications.",
            "missing_for_apply": [
                n
                for n, ok in [
                    ("email", bool(profile.get("email"))),
                    ("first_name", bool(profile.get("first_name"))),
                    ("phone", bool(profile.get("phone"))),
                ]
                if not ok
            ],
        }

    detail = await fetch_job(job_meta["board_token"], job_meta["job_id"])
    packet = draft_answers(detail, profile)
    packet["application_url"] = (
        detail.get("absolute_url")
        or application_url(job_meta["board_token"], job_meta["job_id"])
    )
    app = store.save_application(
        {
            "status": "prepared",
            "job_key": job_key,
            "company": job_meta.get("company"),
            "board_token": job_meta["board_token"],
            "job_id": job_meta["job_id"],
            "title": job_meta.get("title"),
            "packet": packet,
            "content_hash": packet["content_hash"],
            "approved": False,
        }
    )
    return {
        "application_id": app["application_id"],
        "status": app["status"],
        "content_hash": app["content_hash"],
        "application_url": packet["application_url"],
        "blocked_questions": packet["blocked_questions"],
        "drafted_answers": packet["drafted_answers"],
        "cover_letter_text": packet["cover_letter_text"],
        "fields": packet["fields"],
        "resume_path": packet["resume_path"],
        "next_step": (
            "Review blocked_questions, call set_application_answers if needed, "
            "then preview_application and approve_application with the content_hash."
        ),
    }


@mcp.tool()
async def set_application_answers(
    application_id: str, answers: dict[str, Any]
) -> dict:
    """
    Set or override application field answers before approval.

    Args:
        application_id: ID from prepare_application
        answers: Map of Greenhouse field names (or special keys cover_letter_text)
                 to values. Example: {"question_123": "answer", "phone": "..."}
    """
    app = store.get_application(application_id)
    if not app:
        return {"error": "Unknown application_id"}

    packet = app["packet"]
    fields = dict(packet.get("fields") or {})
    for key, value in answers.items():
        if key == "cover_letter_text":
            packet["cover_letter_text"] = value
            continue
        fields[key] = value
        # Unblock matching questions when human provides an answer
        still_blocked = []
        for item in packet.get("blocked_questions") or []:
            if item.get("field_name") == key:
                item = {**item, "answer": value, "needs_human": False, "source": "human"}
                packet.setdefault("drafted_answers", []).append(item)
            else:
                still_blocked.append(item)
        packet["blocked_questions"] = still_blocked

    packet["fields"] = fields
    packet["content_hash"] = content_hash(packet)
    app["packet"] = packet
    app["content_hash"] = packet["content_hash"]
    app["approved"] = False
    app["status"] = "prepared"
    app.pop("approved_hash", None)
    app.pop("approved_at", None)
    store.save_application(app)
    return {
        "application_id": application_id,
        "content_hash": app["content_hash"],
        "blocked_questions": packet["blocked_questions"],
        "note": "Approval cleared because content changed. Preview and approve again.",
    }


@mcp.tool()
async def preview_application(application_id: str) -> dict:
    """Preview the exact submission packet and its content hash (no submit)."""
    app = store.get_application(application_id)
    if not app:
        return {"error": "Unknown application_id"}
    packet = app["packet"]
    remaining = [
        q for q in packet.get("blocked_questions") or [] if q.get("required")
    ]
    return {
        "application_id": application_id,
        "status": app.get("status"),
        "approved": bool(app.get("approved")),
        "content_hash": app.get("content_hash"),
        "company": app.get("company"),
        "title": app.get("title"),
        "application_url": packet.get("application_url"),
        "fields": packet.get("fields"),
        "cover_letter_text": packet.get("cover_letter_text"),
        "resume_path": packet.get("resume_path"),
        "required_blocked_remaining": remaining,
        "can_approve": len(remaining) == 0,
    }


@mcp.tool()
async def approve_application(application_id: str, content_hash: str) -> dict:
    """
    Explicitly approve a prepared application packet.

    The content_hash must match preview_application exactly. Editing answers
    invalidates approval.
    """
    app = store.get_application(application_id)
    if not app:
        return {"error": "Unknown application_id"}

    current = app.get("content_hash")
    if content_hash != current:
        return {
            "error": "Hash mismatch. Packet changed or wrong hash supplied.",
            "expected_hint": "Call preview_application and pass its content_hash.",
        }

    remaining = [
        q
        for q in (app.get("packet") or {}).get("blocked_questions") or []
        if q.get("required")
    ]
    if remaining:
        return {
            "error": "Required questions still need human answers.",
            "required_blocked_remaining": remaining,
        }

    app["approved"] = True
    app["approved_hash"] = content_hash
    app["approved_at"] = datetime.now(timezone.utc).isoformat()
    app["status"] = "approved"
    store.save_application(app)
    store.audit(
        "application_approved",
        application_id=application_id,
        content_hash=content_hash,
    )
    return {
        "application_id": application_id,
        "status": "approved",
        "approved_hash": content_hash,
        "next_step": "Call submit_application. Default mode is manual (safe).",
    }


@mcp.tool()
async def submit_application(
    application_id: str, mode: str = "manual"
) -> dict:
    """
    Submit an approved application.

    Modes:
      - manual (default): does NOT post to Greenhouse. Returns the apply URL,
        answers, and resume path for you to submit yourself.
      - api: posts via Greenhouse Job Board API. Requires GREENHOUSE_JOB_BOARD_API_KEY
        (employer board API key — NOT your Greenhouse login password). Also requires
        the company to be marked allowed_for_api_submit in companies.json.

    Approval with matching content hash is always required.
    """
    app = store.get_application(application_id)
    if not app:
        return {"error": "Unknown application_id"}

    if not app.get("approved") or app.get("approved_hash") != app.get("content_hash"):
        return {
            "error": "Application is not approved for the current packet hash.",
            "hint": "Call preview_application then approve_application.",
        }

    mode = (mode or "manual").lower()
    packet = app["packet"]

    if mode == "manual":
        app["status"] = "manual_ready"
        store.save_application(app)
        store.audit(
            "application_manual_ready",
            application_id=application_id,
            content_hash=app["content_hash"],
        )
        return {
            "ok": True,
            "mode": "manual",
            "application_id": application_id,
            "application_url": packet.get("application_url"),
            "fields": packet.get("fields"),
            "cover_letter_text": packet.get("cover_letter_text"),
            "resume_path": packet.get("resume_path"),
            "message": (
                "Open application_url, paste the answers, upload the resume, "
                "and submit yourself. This MCP did not contact Greenhouse submit."
            ),
        }

    if mode == "api":
        boards = {
            b["board_token"]: b for b in load_companies() if b.get("board_token")
        }
        board = boards.get(app["board_token"], {})
        if not board.get("allowed_for_api_submit"):
            return {
                "error": (
                    f"API submit blocked for board '{app['board_token']}'. "
                    "Set allowed_for_api_submit=true in candidate/companies.json "
                    "only after you intentionally enable it."
                )
            }
        api_key = cfg.greenhouse_job_board_api_key
        if not api_key:
            return {
                "error": (
                    "GREENHOUSE_JOB_BOARD_API_KEY is not set. "
                    "This is an employer Job Board API key, not your login password. "
                    "Use mode='manual' instead."
                )
            }

        result = await submit_application_api(
            board_token=app["board_token"],
            job_id=app["job_id"],
            fields=packet.get("fields") or {},
            resume_path=packet.get("resume_path") or None,
            api_key=api_key,
        )
        app["status"] = "submitted" if result.get("ok") else "submit_failed"
        app["submit_result"] = result
        store.save_application(app)
        store.audit(
            "application_api_submit",
            application_id=application_id,
            ok=bool(result.get("ok")),
            status=result.get("status"),
        )
        return {
            "mode": "api",
            "application_id": application_id,
            **result,
        }

    return {
        "error": f"Unknown mode '{mode}'. Use 'manual' or 'api'.",
    }


@mcp.tool()
async def list_applications(limit: int = 30) -> dict:
    """List prepared/approved/submitted applications from the local store."""
    apps = store.list_applications(max_items=limit)
    compact = [
        {
            "application_id": a.get("application_id"),
            "status": a.get("status"),
            "company": a.get("company"),
            "title": a.get("title"),
            "approved": a.get("approved"),
            "content_hash": a.get("content_hash"),
            "updated_at": a.get("updated_at"),
            "application_url": (a.get("packet") or {}).get("application_url"),
        }
        for a in apps
    ]
    return {"count": len(compact), "applications": compact}


@mcp.tool()
async def record_outcome(
    application_id: str, outcome: str, notes: str = ""
) -> dict:
    """
    Record what happened after a manual or API submission.

    Args:
        application_id: Application id
        outcome: e.g. submitted_manually, rejected, interviewed, offer, withdrawn
        notes: Optional free text
    """
    app = store.get_application(application_id)
    if not app:
        return {"error": "Unknown application_id"}
    app["outcome"] = outcome
    app["outcome_notes"] = notes
    app["status"] = f"outcome:{outcome}"
    store.save_application(app)
    store.audit(
        "application_outcome",
        application_id=application_id,
        outcome=outcome,
        notes=notes,
    )
    return {"application_id": application_id, "outcome": outcome, "notes": notes}


if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    logger.info("Starting apply-mcp with transport=%s", transport)
    mcp.run(transport=transport)
