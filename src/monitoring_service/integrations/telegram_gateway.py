from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from telethon import TelegramClient

from monitoring_service.state import RuntimeState


class TelegramGateway:
    def __init__(self, state: RuntimeState) -> None:
        self.state = state

    def get_client(self) -> TelegramClient:
        if self.state.telegram_client is None:
            proxy = self._build_proxy()
            self.state.telegram_client = TelegramClient(
                "anon",
                self.state.settings.api_id,
                self.state.settings.api_hash,
                proxy=proxy,
                system_version="4.16.30-vxCUSTOM",
            )
        return self.state.telegram_client

    def _build_proxy(self) -> Any:
        proxy_type = self.state.settings.proxy_type
        proxy_addr = self.state.settings.proxy_addr
        proxy_port = self.state.settings.proxy_port
        if not (proxy_type and proxy_addr and proxy_port):
            return None
        try:
            from python_socks import ProxyType

            proxy_type_map = {"socks5": ProxyType.SOCKS5, "socks4": ProxyType.SOCKS4, "http": ProxyType.HTTP}
            key = proxy_type.lower()
            if key not in proxy_type_map:
                logging.warning("Unknown proxy type: %s", proxy_type)
                return None
            return (
                proxy_type_map[key],
                proxy_addr,
                int(proxy_port),
                False,
                self.state.settings.proxy_username or None,
                self.state.settings.proxy_password or None,
            )
        except Exception as exc:
            logging.error("Failed to configure proxy: %s", exc)
            return None

    async def connect_loop(self) -> None:
        backoff = 2
        while True:
            try:
                client = self.get_client()
                if not client.is_connected():
                    await client.connect()
                if not await client.is_user_authorized():
                    logging.warning("Telegram session unauthorized. Run monitoring_service.tools.telegram_auth first.")
                await self._resolve_bots(client)
                self.state.telegram_ready = bool(client.is_connected() and self.state.sigma_bot_entity is not None)
                if self.state.telegram_ready:
                    backoff = 2
                await asyncio.sleep(30)
            except Exception as exc:
                self.state.telegram_ready = False
                logging.error("Telegram loop error: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _resolve_bots(self, client: TelegramClient) -> None:
        if self.state.settings.sigma_bot_id:
            try:
                self.state.sigma_bot_entity = await client.get_entity(self.state.settings.sigma_bot_id)
            except Exception:
                self.state.sigma_bot_entity = None
        if not self.state.sigma_bot_entity and self.state.settings.sigma_bot_username:
            try:
                self.state.sigma_bot_entity = await client.get_entity(self.state.settings.sigma_bot_username)
            except Exception:
                self.state.sigma_bot_entity = None

        if self.state.settings.based_bot_id:
            try:
                self.state.based_bot_entity = await client.get_entity(self.state.settings.based_bot_id)
            except Exception:
                self.state.based_bot_entity = None
        if not self.state.based_bot_entity and self.state.settings.based_bot_username:
            try:
                self.state.based_bot_entity = await client.get_entity(self.state.settings.based_bot_username)
            except Exception:
                self.state.based_bot_entity = None

    async def keep_alive(self) -> None:
        while True:
            await asyncio.sleep(60)
            try:
                client = self.state.telegram_client
                if client and client.is_connected() and self.state.telegram_ready:
                    await client.get_dialogs(limit=1)
            except Exception:
                pass

    async def send_to_sigma_bot(self, address: str) -> None:
        client = self.state.telegram_client
        if not client or not client.is_connected() or not self.state.sigma_bot_entity:
            return

        async def _send() -> None:
            try:
                tasks = [client.send_message(self.state.sigma_bot_entity, address)]
                if self.state.settings.personal_target:
                    tasks.append(client.send_message(self.state.settings.personal_target, f"Token: {address}"))
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as exc:
                logging.error("Send to Sigma Bot failed: %s", exc)

        asyncio.create_task(_send())

    async def send_to_based_bot_fast(self, address: str, keyword: str, keyword_type: str) -> bool:
        del keyword, keyword_type
        client = self.state.telegram_client
        if not client or not client.is_connected() or not self.state.based_bot_entity:
            return False

        async def _send() -> None:
            started = time.time()
            try:
                await client.send_message(self.state.based_bot_entity, address)
            except Exception as exc:
                logging.error("Send to BasedBot failed: %s", exc)
            finally:
                elapsed_ms = (time.time() - started) * 1000
                logging.debug("BasedBot dispatch elapsed=%.1fms", elapsed_ms)

        asyncio.create_task(_send())
        return True

