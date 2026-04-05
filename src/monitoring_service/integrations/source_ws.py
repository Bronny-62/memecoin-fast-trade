from __future__ import annotations

import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from monitoring_service.handlers.message_processor import MessageProcessor
from monitoring_service.state import RuntimeState


class SourceWsConsumer:
    def __init__(self, state: RuntimeState, processor: MessageProcessor) -> None:
        self.state = state
        self.processor = processor

    async def connect_forever(self) -> None:
        ws_url = self.state.settings.ws_url
        if not ws_url:
            return
        backoff = 1
        while True:
            try:
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10, max_queue=1000) as ws:
                    self.state.ws_connected = True
                    backoff = 1
                    async for message in ws:
                        await self.processor.process_message_from_source(message)
            except (ConnectionClosedError, ConnectionClosedOK) as exc:
                logging.warning("Source WS connection closed: %s", exc)
            except Exception as exc:
                logging.error("Source WS error: %s", exc)
            finally:
                self.state.ws_connected = False
                await asyncio.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 30)

