from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(
    os.getenv(
        "JOBIFY_ROOT",
        Path(__file__).resolve().parents[2],
    )
)


class ApplyConfig:
    def __init__(self) -> None:
        self.root = ROOT
        self.candidate_dir = Path(
            os.getenv("CANDIDATE_DIR", str(ROOT / "candidate"))
        )
        self.profile_path = Path(
            os.getenv("CANDIDATE_PROFILE", str(self.candidate_dir / "profile.json"))
        )
        self.companies_path = Path(
            os.getenv(
                "CANDIDATE_COMPANIES", str(self.candidate_dir / "companies.json")
            )
        )
        self.data_dir = Path(
            os.getenv("APPLY_DATA_DIR", str(self.candidate_dir / "data"))
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "applications.json"
        # Optional employer Job Board API key. Candidates usually leave this empty
        # and use submit mode "manual". Do NOT put Greenhouse login passwords here.
        self.greenhouse_job_board_api_key = os.getenv(
            "GREENHOUSE_JOB_BOARD_API_KEY", ""
        ).strip()
        self.submission_mode_default = os.getenv(
            "APPLY_SUBMISSION_MODE", "manual"
        ).strip()
        self.request_timeout_s = float(os.getenv("APPLY_HTTP_TIMEOUT", "30"))


cfg = ApplyConfig()
