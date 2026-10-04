from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from typing import Any


def strip_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _location_fit(
    location: str, content: str, prefs: dict[str, Any]
) -> tuple[bool, str]:
    """
    Allowed:
      - remote roles open to Canada
      - hybrid roles in Montreal
    Not allowed by default:
      - remote-only outside Canada
      - hybrid/onsite outside Montreal
    """
    modes = prefs.get("work_modes") or {}
    remote_canada_ok = bool(modes.get("remote_canada_ok", True))
    hybrid_montreal_ok = bool(modes.get("hybrid_montreal_ok", True))
    onsite_montreal_ok = bool(modes.get("onsite_montreal_ok", False))
    remote_outside_canada_ok = bool(modes.get("remote_outside_canada_ok", False))

    loc = location or ""
    blob = f"{loc} {content or ''}"

    montreal_terms = ("montreal", "montréal")
    canada_terms = (
        "canada",
        "canadian",
        "quebec",
        "québec",
        "ontario",
        "british columbia",
        "toronto",
        "vancouver",
        "ottawa",
        "calgary",
        "edmonton",
        "winnipeg",
        "halifax",
    )
    remote_terms = ("remote", "work from home", "wfh", "distributed")
    hybrid_terms = ("hybrid",)
    onsite_terms = ("on-site", "onsite", "in-office", "in office")

    has_montreal = any(t in blob for t in montreal_terms)
    has_canada = any(t in blob for t in canada_terms) or has_montreal
    has_remote = any(t in blob for t in remote_terms)
    has_hybrid = any(t in blob for t in hybrid_terms)
    has_onsite = any(t in blob for t in onsite_terms) and not has_hybrid

    # Explicit non-Canada remote/geo exclusions in the location string.
    reject = [x.lower() for x in prefs.get("locations_reject") or []]
    for term in reject:
        if not term:
            continue
        if term in loc and not has_canada and not has_montreal:
            return False, f"Rejected location: {term}"

    us_only_remote = any(
        t in loc
        for t in (
            "us-remote",
            "remote us",
            "remote-us",
            "remote from the us",
            "united states",
            "usa",
        )
    )
    if us_only_remote and not has_canada and not remote_outside_canada_ok:
        return False, "US-only remote role"

    if has_remote and has_canada and remote_canada_ok:
        return True, "Remote Canada fit"

    if has_hybrid and has_montreal and hybrid_montreal_ok:
        return True, "Montreal hybrid fit"

    if has_onsite and has_montreal and onsite_montreal_ok:
        return True, "Montreal onsite fit"

    # Location is just Montreal with no mode stated -> treat as local hybrid-capable.
    if has_montreal and not has_remote and hybrid_montreal_ok:
        return True, "Montreal-based role"

    # Generic "Remote" with Canada mentioned in JD.
    if has_remote and has_canada and remote_canada_ok:
        return True, "Remote with Canada eligibility"

    # Generic remote with no country: reject unless outside-Canada remote allowed.
    if has_remote and not has_canada and not remote_outside_canada_ok:
        return False, "Remote role without Canada eligibility"

    # Non-Montreal office locations.
    if (has_onsite or has_hybrid or not has_remote) and not has_montreal:
        return False, "Non-Montreal office/hybrid location"

    if prefs.get("require_location_fit", True):
        return False, "Location does not match Canada-remote or Montreal-hybrid preference"

    return True, "Location unchecked"


def job_matches_profile(job: dict[str, Any], profile: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    title = (job.get("title") or "").lower()
    location = ((job.get("location") or {}).get("name") or "").lower()
    content = strip_html(job.get("content") or "").lower()
    blob = f"{title} {location} {content}"

    prefs = profile.get("preferences") or {}

    role_title_tokens = (
        "product manager",
        "product lead",
        "product owner",
        "technical product manager",
        "technical product lead",
        "group product manager",
        "principal product manager",
        "staff product manager",
        "growth product manager",
        "product management",
    )
    title_hit = [t for t in role_title_tokens if t in title]
    for role in profile.get("target_roles") or []:
        role_l = role.lower().strip()
        if role_l and role_l in title and role_l not in title_hit:
            title_hit.append(role_l)

    if not title_hit:
        return False, ["Title is not a product-management role"]

    reasons.append(f"Title match: {', '.join(title_hit[:3])}")

    loc_ok, loc_reason = _location_fit(location, content, prefs)
    if not loc_ok:
        return False, [loc_reason]
    reasons.append(loc_reason)

    keywords = [k.lower() for k in profile.get("keywords") or []]
    hit_kw = [k for k in keywords if k in blob]
    if hit_kw:
        reasons.append(f"Keyword hits: {', '.join(hit_kw[:8])}")

    return True, reasons


def is_sensitive_question(question_text: str, profile: dict[str, Any]) -> bool:
    text = (question_text or "").lower()
    keys = [k.lower() for k in profile.get("sensitive_question_keywords") or []]
    return any(k in text for k in keys)


def draft_answers(
    job: dict[str, Any], profile: dict[str, Any]
) -> dict[str, Any]:
    questions = job.get("questions") or []
    pre = profile.get("preapproved_answers") or {}
    drafted: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    fields: dict[str, Any] = {
        "first_name": profile.get("first_name") or "",
        "last_name": profile.get("last_name") or "",
        "email": profile.get("email") or "",
        "phone": profile.get("phone") or "",
        "location": profile.get("location") or "",
    }

    experience = profile.get("experience_text") or profile.get("summary") or ""

    for q in questions:
        label = q.get("label") or q.get("description") or ""
        field = q.get("fields") or []
        required = bool(q.get("required"))
        q_type = (q.get("type") or "").lower()

        # Greenhouse nests field metadata
        field_name = None
        values = None
        if field:
            field_name = field[0].get("name")
            values = field[0].get("values")

        sensitive = is_sensitive_question(label, profile)
        answer: Any = None
        source = None
        needs_human = False

        label_l = label.lower()
        if "linkedin" in label_l:
            answer = pre.get("linkedin") or profile.get("linkedin_url") or ""
            source = "profile.linkedin_url / preapproved_answers.linkedin"
        elif "how did you hear" in label_l or "how you heard" in label_l:
            answer = pre.get("how_heard") or ""
            source = "preapproved_answers.how_heard"
        elif "website" in label_l or "portfolio" in label_l:
            answer = pre.get("website") or ""
            source = "preapproved_answers.website"
        elif q_type in {"input_file", "attachment"} or "resume" in label_l:
            answer = profile.get("resume_path") or ""
            source = "profile.resume_pdf"
        elif sensitive:
            needs_human = True
            source = "blocked: sensitive"
        elif required and q_type in {"textarea", "input_text", "multi_value_multi_select"}:
            # Only draft short evidence-backed blurbs for open text when clearly about experience.
            if any(
                w in label_l
                for w in ("why", "interest", "experience", "cover", "about you")
            ):
                answer = _short_interest_blurb(job, profile, experience)
                source = "drafted from confirmed profile summary/experience"
            else:
                needs_human = True
                source = "blocked: no verified answer"
        elif required:
            needs_human = True
            source = "blocked: required without verified mapping"
        else:
            source = "optional skipped"

        item = {
            "label": label,
            "field_name": field_name,
            "required": required,
            "type": q_type,
            "values": values,
            "answer": answer,
            "source": source,
            "sensitive": sensitive,
            "needs_human": needs_human,
        }
        if needs_human:
            blocked.append(item)
        else:
            drafted.append(item)
            if field_name and answer not in (None, ""):
                fields[field_name] = answer

    cover_letter = _short_interest_blurb(job, profile, experience)
    packet = {
        "job_id": job.get("id"),
        "title": job.get("title"),
        "location": (job.get("location") or {}).get("name"),
        "absolute_url": job.get("absolute_url"),
        "fields": fields,
        "drafted_answers": drafted,
        "blocked_questions": blocked,
        "cover_letter_text": cover_letter,
        "resume_path": profile.get("resume_path") or "",
        "candidate": {
            "full_name": profile.get("full_name"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
        },
    }
    packet["content_hash"] = content_hash(packet)
    return packet


def _short_interest_blurb(
    job: dict[str, Any], profile: dict[str, Any], experience: str
) -> str:
    title = job.get("title") or "this role"
    company_loc = (job.get("location") or {}).get("name") or ""
    summary = (profile.get("summary") or "").strip()
    # Keep grounded: no invented company-specific claims.
    parts = [
        f"I am applying for {title}"
        + (f" ({company_loc})" if company_loc else "")
        + ".",
        summary,
        "My recent work includes leading digital product, analytics and growth systems "
        "as Technical Product Lead at Hullo (VIFC), after Technical PM work at Wallex "
        "and product roles at Digikala. I am looking for Technical Product Manager / "
        "Product Lead roles where I can own product strategy with strong data foundations.",
    ]
    # Do not paste the entire experience file into every answer.
    _ = experience
    return " ".join(p for p in parts if p)


def content_hash(packet: dict[str, Any]) -> str:
    clone = {
        k: v
        for k, v in packet.items()
        if k not in {"content_hash", "approved_at", "approval"}
    }
    raw = json.dumps(clone, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
