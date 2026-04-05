from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

from monitoring_service.paths import get_config_dir, get_logs_dir, get_project_root


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    sigma_bot_username: str
    sigma_bot_id: int
    based_bot_username: str
    based_bot_id: int
    personal_target: str | None
    ws_url: str
    proxy_type: str
    proxy_addr: str
    proxy_port: str
    proxy_username: str
    proxy_password: str
    listen_port: int
    config_file: Path
    config_dir: Path
    logs_dir: Path
    token_mapping_file: Path
    monitored_users_file: Path
    monitored_log_file: Path


def load_settings(base_dir: Path | None = None) -> Settings:
    root = (base_dir or get_project_root()).resolve()
    config_dir = get_config_dir(root)
    logs_dir = get_logs_dir(root)
    config_file = config_dir / "config.ini"
    if not config_file.exists():
        raise FileNotFoundError("config/config.ini not found")

    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")

    try:
        return Settings(
            api_id=int(config["Telegram"]["api_id"]),
            api_hash=config["Telegram"]["api_hash"],
            sigma_bot_username=config["Telegram"]["sigma_bot_username"],
            sigma_bot_id=int(config["Telegram"].get("sigma_bot_id", "0") or "0"),
            based_bot_username=config["Telegram"].get("BasedBot_username", ""),
            based_bot_id=int(config["Telegram"].get("BasedBot_id", "0") or "0"),
            personal_target=config["Telegram"].get("personal_notification_target", None),
            ws_url=config.get("Source", "ws_url", fallback=""),
            proxy_type=config["Telegram"].get("proxy_type", "").strip(),
            proxy_addr=config["Telegram"].get("proxy_addr", "").strip(),
            proxy_port=config["Telegram"].get("proxy_port", "").strip(),
            proxy_username=config["Telegram"].get("proxy_username", "").strip(),
            proxy_password=config["Telegram"].get("proxy_password", "").strip(),
            listen_port=int(config.get("Server", "listen_port", fallback="8051")),
            config_file=config_file,
            config_dir=config_dir,
            logs_dir=logs_dir,
            token_mapping_file=config_dir / "token_mapping.json",
            monitored_users_file=config_dir / "monitored_users.json",
            monitored_log_file=logs_dir / "monitored_messages.log",
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"config/config.ini format error: {exc}") from exc

