from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_config_dir(base_dir: Path | None = None) -> Path:
    root = (base_dir or get_project_root()).resolve()
    return root / "config"


def get_logs_dir(base_dir: Path | None = None) -> Path:
    root = (base_dir or get_project_root()).resolve()
    return root / "logs"

