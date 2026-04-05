from __future__ import annotations

from typing import Any

import ahocorasick

from .normalization import normalize_text


def build_keyword_automaton(keywords_dict: dict[str, str]) -> Any:
    automaton = ahocorasick.Automaton()
    for keyword, address in keywords_dict.items():
        automaton.add_word(keyword.lower(), (keyword, address))
    automaton.make_automaton()
    return automaton


def fast_match_with_automaton(text: str, automaton: Any) -> list[tuple[str, str]]:
    if not text or not automaton:
        return []

    text_lower = normalize_text(text).lower()
    matched: list[tuple[str, str]] = []
    seen_keywords: set[str] = set()
    for _, (original_keyword, address) in automaton.iter(text_lower):
        keyword_lower = original_keyword.lower()
        if keyword_lower not in seen_keywords:
            matched.append((keyword_lower, address))
            seen_keywords.add(keyword_lower)
    return matched

