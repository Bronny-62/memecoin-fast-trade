from __future__ import annotations

import json
import logging
import time
from typing import Any

from monitoring_service.integrations.telegram_gateway import TelegramGateway
from monitoring_service.matching import fast_match_with_automaton
from monitoring_service.services.dedup import check_and_mark_address, dedup_tuple
from monitoring_service.services.monitored_log import log_monitored_message
from monitoring_service.state import RuntimeState


class MessageProcessor:
    def __init__(self, state: RuntimeState, telegram: TelegramGateway) -> None:
        self.state = state
        self.telegram = telegram

    def author_tiers(self, screen_name: str) -> list[str]:
        if not screen_name:
            return []
        return self.state.user_tier_map.get(screen_name, [])

    def author_tiers_exact(self, author: str) -> list[str]:
        if not author:
            return []
        tiers: list[str] = []
        if author in self.state.bsc_t0_users:
            tiers.append("BSC_T0")
        if author in self.state.bsc_t1_users:
            tiers.append("BSC_T1")
        if author in self.state.xlayer_t0_users:
            tiers.append("XLAYER_T0")
        if author in self.state.xlayer_t1_users:
            tiers.append("XLAYER_T1")
        return tiers

    def determine_keyword_type(self, keyword: str, address: str) -> str:
        if keyword.lower() in self.state.xlayer_t0_keywords and self.state.xlayer_t0_keywords[keyword.lower()] == address:
            return "BasedBot_T0_KEYS"
        if keyword.lower() in self.state.xlayer_t1_keywords and self.state.xlayer_t1_keywords[keyword.lower()] == address:
            return "BasedBot_T1_KEYS"
        if keyword.lower() in self.state.bsc_t0_keywords and self.state.bsc_t0_keywords[keyword.lower()] == address:
            return "SigmaBot_T0_KEYS"
        if keyword.lower() in self.state.bsc_t1_keywords and self.state.bsc_t1_keywords[keyword.lower()] == address:
            return "SigmaBot_T1_KEYS"
        if keyword.upper() in self.state.xlayer_change_image_map and self.state.xlayer_change_image_map[keyword.upper()] == address:
            return "BasedBot_CHANGE_IMAGE"
        if keyword.upper() in self.state.bsc_change_image_map and self.state.bsc_change_image_map[keyword.upper()] == address:
            return "SigmaBot_CHANGE_IMAGE"
        return "SigmaBot_T1_KEYS"

    async def send_for_matches(self, matches: list[tuple[str, str]]) -> None:
        tasks = []
        for _, address in matches:
            if await check_and_mark_address(self.state, address):
                tasks.append(self.telegram.send_to_sigma_bot(address))
        if tasks:
            await asyncio_gather_safe(tasks)

    async def process_gmgn_native_message(self, data: dict[str, Any], raw: str, start_time: float) -> None:
        data_array = data.get("data", [])
        if not data_array:
            return

        for item in data_array:
            try:
                author_raw = ((item.get("u") or {}).get("s") or "")
                author = author_raw.lower()
                user_tiers = self.author_tiers(author)
                if not user_tiers:
                    continue

                log_monitored_message(self.state, raw, author_raw, source_type="gmgn_native")
                user_text = ((item.get("c") or {}).get("t") or "")
                source_text = ((item.get("sc") or {}).get("t") or "")
                source_user_name = ((item.get("su") or {}).get("s") or "")
                combined_text = f"{user_text} {source_text}".strip() if source_text else user_text

                tier_matches = self._collect_tier_matches(user_tiers, combined_text) if combined_text else []
                source_user_tier_matches = self._collect_tier_matches(user_tiers, source_user_name) if source_user_name else []

                await self._dispatch_tier_matches(
                    tier_matches=tier_matches,
                    author=author,
                    author_raw=author_raw,
                    source="gmgn",
                    msg_type="tweet",
                    dedup_identity=item.get("ti", "") or user_text[:64],
                    start_time=start_time,
                )
                await self._dispatch_tier_matches(
                    tier_matches=source_user_tier_matches,
                    author=author,
                    author_raw=author_raw,
                    source="gmgn",
                    msg_type="source_user",
                    dedup_identity=item.get("ti", "") or source_user_name[:64],
                    start_time=start_time,
                )
            except Exception:
                continue

    async def process_message_from_source(self, raw: str) -> None:
        start_time = time.time()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logging.warning("Skip invalid JSON from source: %s", raw[:200])
            return

        if data.get("channel") == "twitter_user_monitor_basic":
            await self.process_gmgn_native_message(data, raw, start_time)
            return

        msg_type = data.get("msg_type", "")
        payload = data.get("payload", {}) or {}
        source = payload.get("source", "")

        if source == "binance_square":
            await self._process_binance_square(raw, msg_type, payload, start_time)
            return
        if source == "weibo":
            await self._process_weibo(raw, payload, start_time)
            return

        await self._process_legacy_twitter(raw, msg_type, payload, start_time)

    async def _process_binance_square(self, raw: str, msg_type: str, payload: dict[str, Any], start_time: float) -> None:
        author = payload.get("author", "")
        content = payload.get("content", "")
        if not author or not content:
            return

        user_tiers = [tier for tier in self.author_tiers_exact(author.lower()) if tier.startswith("BSC_")]
        if not user_tiers:
            return

        log_monitored_message(self.state, raw, author, source_type="binance_square")
        for tier in user_tiers:
            automaton = self.state.tier_automatons.get(tier)
            if not automaton:
                continue
            matches = fast_match_with_automaton(content, automaton)
            if not matches:
                continue
            await self.send_for_matches(matches)
            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(
                "[TRIGGER] type=%s | source=binance_square | user=%s | tier=%s | key=%s | target=SigmaBot | elapsed=%.1fms",
                msg_type,
                author,
                tier,
                matches[0][0].upper(),
                elapsed_ms,
            )

    async def _process_weibo(self, raw: str, payload: dict[str, Any], start_time: float) -> None:
        author = payload.get("author", "unknown")
        content = payload.get("content", "")
        if not content:
            return

        log_monitored_message(self.state, raw, author, source_type="weibo")
        for tier in ["BSC_T0", "BSC_T1"]:
            automaton = self.state.tier_automatons.get(tier)
            if not automaton:
                continue
            matches = fast_match_with_automaton(content, automaton)
            if not matches:
                continue
            await self.send_for_matches(matches)
            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(
                "[TRIGGER] type=weibo_post | source=weibo | user=%s | tier=%s | key=%s | target=SigmaBot | elapsed=%.1fms",
                author,
                tier,
                matches[0][0].upper(),
                elapsed_ms,
            )
            break

    async def _process_legacy_twitter(self, raw: str, msg_type: str, payload: dict[str, Any], start_time: float) -> None:
        author_raw = ((payload.get("user") or {}).get("screen_name") or "")
        author = author_raw.lower()
        user_tiers = self.author_tiers(author)
        if not user_tiers:
            return

        log_monitored_message(self.state, raw, author_raw or author, source_type="gmgn")

        if msg_type == "follow":
            action_user = payload.get("action_user") or {}
            action_screen_name = action_user.get("screen_name", "")
            if action_screen_name:
                await self._process_follow_event(msg_type, author, author_raw, action_screen_name, start_time)
            return

        if msg_type in {"new_description", "new_avatar"}:
            await self._process_profile_event(msg_type, author, author_raw, payload, user_tiers, start_time)
            return

        is_tweet_related = (
            msg_type in ("new_tweet", "update_tweet", "pin")
            or payload.get("is_self_send")
            or payload.get("is_retweet")
            or payload.get("is_quote")
            or payload.get("is_reply")
        )
        if not is_tweet_related:
            return

        text = (payload.get("tweet") or {}).get("text", "") if msg_type == "pin" else payload.get("text", "")
        if not text:
            return

        tier_matches = self._collect_tier_matches(user_tiers, text)
        dedup_identity = payload.get("tweet_id") or payload.get("new_tweet_id") or text[:64]
        await self._dispatch_tier_matches(
            tier_matches=tier_matches,
            author=author,
            author_raw=author_raw,
            source="websocket",
            msg_type=msg_type,
            dedup_identity=dedup_identity,
            start_time=start_time,
        )

    async def _process_follow_event(
        self,
        msg_type: str,
        author: str,
        author_raw: str,
        action_screen_name: str,
        start_time: float,
    ) -> None:
        sn_upper = str(action_screen_name).upper()
        for tier in self.author_tiers(author):
            for keyword, address in self._keyword_map_for_tier(tier).items():
                if keyword.upper() != sn_upper:
                    continue
                if not dedup_tuple(self.state, (msg_type, author, tier, keyword)):
                    continue
                await self._send_based_on_tier(tier, keyword, address, msg_type, author_raw, start_time)
                break

    async def _process_profile_event(
        self,
        msg_type: str,
        author: str,
        author_raw: str,
        payload: dict[str, Any],
        user_tiers: list[str],
        start_time: float,
    ) -> None:
        if msg_type == "new_description":
            new_value = payload.get("new_value", "")
            if new_value:
                tier_matches = self._collect_tier_matches(user_tiers, new_value)
                await self._dispatch_tier_matches(
                    tier_matches=tier_matches,
                    author=author,
                    author_raw=author_raw,
                    source="websocket",
                    msg_type=msg_type,
                    dedup_identity=new_value[:64] or "desc",
                    start_time=start_time,
                )
                return
        await self._process_change_image_event(msg_type, author, author_raw, user_tiers, start_time)

    async def _process_change_image_event(
        self,
        msg_type: str,
        author: str,
        author_raw: str,
        user_tiers: list[str],
        start_time: float,
    ) -> None:
        sn_upper = (author_raw or "").upper()
        address = None
        target = "SigmaBot"
        keyword_type = "SigmaBot_CHANGE_IMAGE"

        if any(tier.startswith("XLAYER_") for tier in user_tiers):
            address = self.state.xlayer_change_image_map.get(sn_upper)
            target = "BasedBot"
            keyword_type = "BasedBot_CHANGE_IMAGE"
        else:
            address = self.state.bsc_change_image_map.get(sn_upper)

        if not address:
            return
        if not dedup_tuple(self.state, (msg_type, author, "change_image")):
            return
        if not await check_and_mark_address(self.state, address):
            return

        if target == "BasedBot":
            await self.telegram.send_to_based_bot_fast(address, "改名/改头像/简介", keyword_type)
        else:
            await self.telegram.send_to_sigma_bot(address)

        elapsed_ms = (time.time() - start_time) * 1000
        logging.info(
            "[TRIGGER] type=%s | source=websocket | user=%s | key=%s | target=%s | elapsed=%.1fms",
            msg_type,
            author_raw or author,
            "改名/改头像/简介",
            target,
            elapsed_ms,
        )

    async def _dispatch_tier_matches(
        self,
        tier_matches: list[tuple[str, list[tuple[str, str]]]],
        author: str,
        author_raw: str,
        source: str,
        msg_type: str,
        dedup_identity: str,
        start_time: float,
    ) -> None:
        for tier, matches in tier_matches:
            if not matches:
                continue
            key_tuple = (author, tier, dedup_identity, tuple(m[0] for m in matches))
            if not dedup_tuple(self.state, key_tuple):
                continue

            if tier.startswith("XLAYER_"):
                first_keyword, first_address = matches[0]
                if not await check_and_mark_address(self.state, first_address):
                    continue
                await self.telegram.send_to_based_bot_fast(first_address, first_keyword, self.determine_keyword_type(first_keyword, first_address))
                target = "BasedBot"
                display_keyword = first_keyword.upper()
            else:
                await self.send_for_matches(matches)
                target = "SigmaBot"
                display_keyword = matches[0][0].upper()

            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(
                "[TRIGGER] type=%s | source=%s | user=%s | tier=%s | key=%s | target=%s | elapsed=%.1fms",
                msg_type,
                source,
                author_raw or author,
                tier,
                display_keyword,
                target,
                elapsed_ms,
            )

    def _collect_tier_matches(self, user_tiers: list[str], text: str) -> list[tuple[str, list[tuple[str, str]]]]:
        tier_matches: list[tuple[str, list[tuple[str, str]]]] = []
        for tier in user_tiers:
            automaton = self.state.tier_automatons.get(tier)
            if not automaton:
                continue
            matches = fast_match_with_automaton(text, automaton)
            if matches:
                tier_matches.append((tier, matches))
        return tier_matches

    def _keyword_map_for_tier(self, tier: str) -> dict[str, str]:
        if tier == "BSC_T0":
            return {**self.state.bsc_t1_keywords, **self.state.bsc_t0_keywords}
        if tier == "BSC_T1":
            return self.state.bsc_t1_keywords
        if tier == "XLAYER_T0":
            return {**self.state.xlayer_t1_keywords, **self.state.xlayer_t0_keywords}
        if tier == "XLAYER_T1":
            return self.state.xlayer_t1_keywords
        return {}

    async def _send_based_on_tier(
        self,
        tier: str,
        keyword: str,
        address: str,
        msg_type: str,
        author_raw: str,
        start_time: float,
    ) -> None:
        if not await check_and_mark_address(self.state, address):
            return
        if tier.startswith("XLAYER_"):
            await self.telegram.send_to_based_bot_fast(address, keyword, self.determine_keyword_type(keyword, address))
            target = "BasedBot"
        else:
            await self.telegram.send_to_sigma_bot(address)
            target = "SigmaBot"
        elapsed_ms = (time.time() - start_time) * 1000
        logging.info(
            "[TRIGGER] type=%s | source=websocket | user=%s | tier=%s | key=%s | target=%s | elapsed=%.1fms",
            msg_type,
            author_raw,
            tier,
            keyword.upper(),
            target,
            elapsed_ms,
        )

    async def close(self) -> None:
        client = self.state.telegram_client
        if client and client.is_connected():
            await client.disconnect()


async def asyncio_gather_safe(tasks: list[Any]) -> None:
    if tasks:
        await __import__("asyncio").gather(*tasks, return_exceptions=True)

