from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from monitoring_service.handlers.message_processor import MessageProcessor
from monitoring_service.services.config_loader import load_configs
from monitoring_service.state import RuntimeState


def build_router(state: RuntimeState, processor: MessageProcessor) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        state.gmgn_monitor_connections += 1
        state.gmgn_monitor_connected = True
        try:
            while True:
                raw_data = await websocket.receive_text()
                try:
                    data = json.loads(raw_data)
                    inner_raw = data.get("content")
                    if inner_raw:
                        await processor.process_message_from_source(inner_raw)
                    else:
                        await processor.process_message_from_source(raw_data)
                except json.JSONDecodeError:
                    await processor.process_message_from_source(raw_data)
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logging.error("[WebSocket] error: %s", exc)
        finally:
            state.gmgn_monitor_connections = max(0, state.gmgn_monitor_connections - 1)
            state.gmgn_monitor_connected = state.gmgn_monitor_connections > 0

    @router.get("/health")
    async def health_check() -> dict[str, object]:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "monitored_BSC_T0_keywords": len(state.bsc_t0_keywords),
            "monitored_BSC_T1_keywords": len(state.bsc_t1_keywords),
            "monitored_XLAYER_T0_keywords": len(state.xlayer_t0_keywords),
            "monitored_XLAYER_T1_keywords": len(state.xlayer_t1_keywords),
            "monitored_BSC_CHANGE_IMAGE": len(state.bsc_change_image_map),
            "monitored_XLAYER_CHANGE_IMAGE": len(state.xlayer_change_image_map),
            "monitored_BSC_T0_users": len(state.bsc_t0_users),
            "monitored_BSC_T1_users": len(state.bsc_t1_users),
            "monitored_XLAYER_T0_users": len(state.xlayer_t0_users),
            "monitored_XLAYER_T1_users": len(state.xlayer_t1_users),
            "ws_connected": state.ws_connected,
            "telegram_ready": state.telegram_ready,
            "gmgn_monitor_connected": state.gmgn_monitor_connected,
            "sigma_bot_ready": bool(state.sigma_bot_entity),
            "based_bot_ready": bool(state.based_bot_entity),
            "logged_messages_count": len(state.monitored_messages_log),
            "log_capacity": state.monitored_messages_log.maxlen,
            "triggered_addresses_count": len(state.triggered_addresses),
            "dedup_hits": state.dedup_hits,
        }

    @router.get("/reload_config")
    async def reload_config_endpoint() -> dict[str, object]:
        try:
            load_configs(state)
            return {"status": "success", "reloaded_files": ["token_mapping", "monitored_users"]}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    @router.get("/xlayer_status")
    async def xlayer_status() -> dict[str, object]:
        total_xlayer_users = len(state.xlayer_t0_users) + len(state.xlayer_t1_users)
        total_xlayer_keywords = len(state.xlayer_t0_keywords) + len(state.xlayer_t1_keywords)
        return {
            "xlayer_enabled": total_xlayer_users > 0 and total_xlayer_keywords > 0,
            "xlayer_t0_users_count": len(state.xlayer_t0_users),
            "xlayer_t1_users_count": len(state.xlayer_t1_users),
            "xlayer_t0_keywords_count": len(state.xlayer_t0_keywords),
            "xlayer_t1_keywords_count": len(state.xlayer_t1_keywords),
            "xlayer_t0_users": list(state.xlayer_t0_users),
            "xlayer_t1_users": list(state.xlayer_t1_users),
            "xlayer_t0_keywords": list(state.xlayer_t0_keywords.keys()),
            "xlayer_t1_keywords": list(state.xlayer_t1_keywords.keys()),
            "based_bot_connected": bool(state.based_bot_entity),
            "based_bot_username": state.settings.based_bot_username,
            "based_bot_id": state.settings.based_bot_id,
        }

    return router

