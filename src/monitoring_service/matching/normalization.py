from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def has_special_characters(text: str) -> bool:
    if not text:
        return False
    special_char_pattern = re.compile(
        r"[\U0001F600-\U0001F64F"
        r"\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF"
        r"\U00002600-\U000027BF"
        r"\U0001F900-\U0001F9FF"
        r"\U0001F018-\U0001F270"
        r"\U0001F200-\U0001F2FF"
        r"\U0001F700-\U0001F77F"
        r"\U0001FA00-\U0001FA6F"
        r"\U0001FA70-\U0001FAFF"
        r"\U00002702-\U000027B0"
        r"\U000024C2-\U0001F251"
        r"\U00000300-\U0000036F"
        r"\U00002000-\U0000206F"
        r"\U00002070-\U0000209F"
        r"\U000020A0-\U000020CF"
        r"\U000000A0-\U000000FF"
        r"\U00000250-\U000002AF"
        r"\U000002B0-\U000002FF"
        r"\U00000100-\U0000017F"
        r"\U00000180-\U0000024F]"
    )
    return bool(special_char_pattern.search(text))


def has_emoji(text: str) -> bool:
    return has_special_characters(text)


def is_word_boundary_char(char: str | None) -> bool:
    if not char:
        return True
    if char.isspace() or char in '.,!?;:"()[]{}+-=*/\\|<>@#$%^&~`\'_':
        return True
    if "\u4e00" <= char <= "\u9fff" or "\u3000" <= char <= "\u303f" or "\uff00" <= char <= "\uffef":
        return True
    if has_special_characters(char):
        return True
    return False


def is_number_boundary_char(char: str | None, keyword: str) -> bool:
    if not char:
        return True
    if keyword.isdigit():
        return not char.isdigit()
    return is_word_boundary_char(char)


def find_smart_word_boundaries(text: str, keyword: str, case_sensitive: bool = False) -> bool:
    if not text or not keyword:
        return False

    search_text = text if case_sensitive else text.lower()
    search_keyword = keyword if case_sensitive else keyword.lower()
    start_pos = 0

    while True:
        pos = search_text.find(search_keyword, start_pos)
        if pos == -1:
            break
        prev_char = search_text[pos - 1] if pos > 0 else None
        next_pos = pos + len(search_keyword)
        next_char = search_text[next_pos] if next_pos < len(search_text) else None

        if search_keyword.isdigit():
            is_prev_boundary = pos == 0 or is_number_boundary_char(prev_char, search_keyword)
            is_next_boundary = next_pos >= len(search_text) or is_number_boundary_char(next_char, search_keyword)
        else:
            is_prev_boundary = pos == 0 or is_word_boundary_char(prev_char)
            is_next_boundary = next_pos >= len(search_text) or is_word_boundary_char(next_char)

        if is_prev_boundary and is_next_boundary:
            return True
        start_pos = pos + 1
    return False

