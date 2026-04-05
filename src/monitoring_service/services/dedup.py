from __future__ import annotations

import logging

from monitoring_service.state import RuntimeState


def dedup_tuple(state: RuntimeState, key_tuple: tuple) -> bool:
    key_str = str(key_tuple)
    if key_str in state.processed_tuple_keys:
        return False
    state.processed_tuple_keys.add(key_str)
    state.processed_keys_counter += 1

    if state.processed_keys_counter > 1000:
        temp_list = list(state.processed_tuple_keys)
        state.processed_tuple_keys.clear()
        state.processed_tuple_keys.update(temp_list[-500:])
        state.processed_keys_counter = 500
    return True


async def check_and_mark_address(state: RuntimeState, address: str) -> bool:
    address_lower = address.lower()
    async with state.address_dedup_lock:
        if address_lower in state.triggered_addresses:
            state.dedup_hits += 1
            logging.info("[DEDUP] Address already triggered: %s...%s", address_lower[:10], address_lower[-8:])
            return False
        state.triggered_addresses.add(address_lower)
    return True

