from __future__ import annotations

import asyncio
import json
from datetime import datetime

from monitoring_service.state import RuntimeState


def log_monitored_message(state: RuntimeState, raw_message: str, author: str, source_type: str = "twitter") -> None:
    timestamp = datetime.now().isoformat()
    try:
        if isinstance(raw_message, str):
            message_obj = json.loads(raw_message)
        else:
            message_obj = raw_message
    except (json.JSONDecodeError, TypeError):
        message_obj = {"raw": str(raw_message)}

    log_entry = {
        "timestamp": timestamp,
        "author": author,
        "source_type": source_type,
        "message": message_obj,
    }
    state.monitored_messages_log.append(log_entry)
    state.log_write_queue.append(log_entry)


async def async_log_writer(state: RuntimeState) -> None:
    while True:
        await asyncio.sleep(1)
        if not state.log_write_queue:
            continue
        _flush_monitored_log(state)
        state.log_write_queue.clear()


def flush_monitored_log_on_shutdown(state: RuntimeState) -> None:
    if state.log_write_queue:
        _flush_monitored_log(state)


def _flush_monitored_log(state: RuntimeState) -> None:
    state.settings.logs_dir.mkdir(parents=True, exist_ok=True)
    with state.settings.monitored_log_file.open("w", encoding="utf-8", newline="") as f:
        for entry in state.monitored_messages_log:
            f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")

