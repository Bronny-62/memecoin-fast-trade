from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque

from .settings import Settings


@dataclass
class RuntimeState:
    settings: Settings

    # keyword mapping
    bsc_t0_keywords: dict[str, str] = field(default_factory=dict)
    bsc_t1_keywords: dict[str, str] = field(default_factory=dict)
    xlayer_t0_keywords: dict[str, str] = field(default_factory=dict)
    xlayer_t1_keywords: dict[str, str] = field(default_factory=dict)
    bsc_change_image_map: dict[str, str] = field(default_factory=dict)
    xlayer_change_image_map: dict[str, str] = field(default_factory=dict)

    # monitored users
    bsc_t0_users: set[str] = field(default_factory=set)
    bsc_t1_users: set[str] = field(default_factory=set)
    xlayer_t0_users: set[str] = field(default_factory=set)
    xlayer_t1_users: set[str] = field(default_factory=set)
    monitored_users_all: set[str] = field(default_factory=set)
    user_tier_map: dict[str, list[str]] = field(default_factory=dict)

    # precompiled automata
    tier_automatons: dict[str, Any] = field(default_factory=dict)

    # transport state
    ws_connected: bool = False
    telegram_ready: bool = False
    gmgn_monitor_connected: bool = False
    gmgn_monitor_connections: int = 0

    # telegram runtime
    telegram_client: Any | None = None
    sigma_bot_entity: Any | None = None
    based_bot_entity: Any | None = None

    # message dedup
    processed_tuple_keys: set[str] = field(default_factory=set)
    processed_keys_counter: int = 0
    triggered_addresses: set[str] = field(default_factory=set)
    dedup_hits: int = 0
    address_dedup_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # monitored message logs
    monitored_messages_log: Deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=1000))
    log_write_queue: Deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=100))

