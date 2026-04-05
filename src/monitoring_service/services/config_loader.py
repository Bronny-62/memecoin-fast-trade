from __future__ import annotations

import json

from monitoring_service.matching import build_keyword_automaton, has_emoji, normalize_text
from monitoring_service.state import RuntimeState


def _prepare_keywords(raw_map: dict[str, str]) -> dict[str, str]:
    prepared: dict[str, str] = {}
    for keyword, address in raw_map.items():
        key_normalized = normalize_text(keyword)
        prepared[key_normalized] = address
        if has_emoji(keyword):
            key_lower = keyword.lower()
            if key_lower != key_normalized:
                prepared[key_lower] = address
        else:
            prepared[keyword.lower()] = address
    return prepared


def _build_user_tier_map(state: RuntimeState) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for user in state.bsc_t0_users:
        result.setdefault(user, []).append("BSC_T0")
    for user in state.bsc_t1_users:
        result.setdefault(user, []).append("BSC_T1")
    for user in state.xlayer_t0_users:
        result.setdefault(user, []).append("XLAYER_T0")
    for user in state.xlayer_t1_users:
        result.setdefault(user, []).append("XLAYER_T1")
    return result


def load_configs(state: RuntimeState) -> None:
    _load_token_mapping(state)
    _load_monitored_users(state)
    state.tier_automatons = {
        "BSC_T0": build_keyword_automaton({**state.bsc_t1_keywords, **state.bsc_t0_keywords}),
        "BSC_T1": build_keyword_automaton(state.bsc_t1_keywords),
        "XLAYER_T0": build_keyword_automaton({**state.xlayer_t1_keywords, **state.xlayer_t0_keywords}),
        "XLAYER_T1": build_keyword_automaton(state.xlayer_t1_keywords),
    }
    state.user_tier_map = _build_user_tier_map(state)


def _load_token_mapping(state: RuntimeState) -> None:
    try:
        with state.settings.token_mapping_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error("CONFIG ERROR: '%s' not found.", state.settings.token_mapping_file)
        return
    except json.JSONDecodeError as exc:
        raise ValueError(f"token_mapping parse error: {exc}") from exc

    state.bsc_t0_keywords = _prepare_keywords(data.get("SigmaBot_T0_KEYS") or data.get("BSC_T0_KEYS") or {})
    state.bsc_t1_keywords = _prepare_keywords(data.get("SigmaBot_T1_KEYS") or data.get("BSC_T1_KEYS") or {})
    state.xlayer_t0_keywords = _prepare_keywords(data.get("BasedBot_T0_KEYS") or data.get("XLAYER_T0_KEYS") or {})
    state.xlayer_t1_keywords = _prepare_keywords(data.get("BasedBot_T1_KEYS") or data.get("XLAYER_T1_KEYS") or {})
    state.bsc_change_image_map = {
        k.upper(): v for k, v in ((data.get("SigmaBot_CHANGE_IMAGE") or data.get("BSC_CHANGE_IMAGE") or {})).items()
    }
    state.xlayer_change_image_map = {
        k.upper(): v for k, v in ((data.get("BasedBot_CHANGE_IMAGE") or data.get("XLAYER_CHANGE_IMAGE") or {})).items()
    }

def _load_monitored_users(state: RuntimeState) -> None:
    try:
        with state.settings.monitored_users_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error("CONFIG ERROR: '%s' not found.", state.settings.monitored_users_file)
        return
    except json.JSONDecodeError as exc:
        raise ValueError(f"monitored_users parse error: {exc}") from exc

    state.bsc_t0_users = set(u.lower() for u in (data.get("SigmaBot_T0_Users") or []))
    state.bsc_t1_users = set(u.lower() for u in (data.get("SigmaBot_T1_Users") or []))
    state.xlayer_t0_users = set(u.lower() for u in (data.get("BasedBot_T0_Users") or []))
    state.xlayer_t1_users = set(u.lower() for u in (data.get("BasedBot_T1_Users") or []))
    state.monitored_users_all = state.bsc_t0_users | state.bsc_t1_users | state.xlayer_t0_users | state.xlayer_t1_users

