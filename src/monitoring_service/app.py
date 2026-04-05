from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monitoring_service.api.routes import build_router
from monitoring_service.handlers.message_processor import MessageProcessor
from monitoring_service.integrations.source_ws import SourceWsConsumer
from monitoring_service.integrations.telegram_gateway import TelegramGateway
from monitoring_service.logging_setup import configure_logging
from monitoring_service.services.config_loader import load_configs
from monitoring_service.services.monitored_log import async_log_writer, flush_monitored_log_on_shutdown
from monitoring_service.settings import load_settings
from monitoring_service.state import RuntimeState


def create_app(base_dir: Path | None = None) -> FastAPI:
    settings = load_settings(base_dir=base_dir)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    configure_logging()
    state = RuntimeState(settings=settings)
    load_configs(state)

    telegram = TelegramGateway(state)
    processor = MessageProcessor(state, telegram)
    source_consumer = SourceWsConsumer(state, processor)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        tasks = [
            asyncio.create_task(telegram.connect_loop()),
            asyncio.create_task(source_consumer.connect_forever()),
            asyncio.create_task(_periodic_status_reporter(state)),
            asyncio.create_task(async_log_writer(state)),
            asyncio.create_task(telegram.keep_alive()),
        ]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            flush_monitored_log_on_shutdown(state)
            await processor.close()

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.state.runtime = state
    app.include_router(build_router(state, processor))
    return app


async def _periodic_status_reporter(state: RuntimeState) -> None:
    while True:
        await asyncio.sleep(30)
        if state.gmgn_monitor_connected:
            logging.info("[HEARTBEAT] 信息源=gmgn-monitor | 状态=已连接")
        if state.ws_connected:
            logging.info("[HEARTBEAT] 信息源=光光监控 | 状态=已连接")

