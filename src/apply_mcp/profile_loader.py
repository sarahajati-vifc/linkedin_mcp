from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apply_mcp.config import cfg


def load_profile() -> dict[str, Any]:
    with cfg.profile_path.open(encoding="utf-8") as f:
        profile = json.load(f)
    exp_rel = profile.get("experience_markdown")
    if exp_rel:
        exp_path = (cfg.root / exp_rel).resolve()
        if exp_path.exists():
            profile["experience_text"] = exp_path.read_text(encoding="utf-8")
        else:
            profile["experience_text"] = ""
    resume_rel = profile.get("resume_pdf")
    if resume_rel:
        resume_path = (cfg.root / resume_rel).resolve()
        profile["resume_path"] = str(resume_path) if resume_path.exists() else ""
    else:
        profile["resume_path"] = ""
    return profile


def load_companies() -> list[dict[str, Any]]:
    with cfg.companies_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("boards", []))


def resume_path(profile: dict[str, Any] | None = None) -> Path | None:
    profile = profile or load_profile()
    path = profile.get("resume_path") or ""
    if not path:
        return None
    p = Path(path)
    return p if p.exists() else None
