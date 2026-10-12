"""
Core Obfuscation Engine
=======================
Provides functions for injecting and stripping invisible Zero-Width Space characters (\u200B),
inspecting text composition, and generating obfuscation statistics.
"""

from __future__ import annotations
import random
import re
from typing import Dict, Any, Set

# Standard invisible Unicode characters
ZW_SPACE = "\u200b"       # Zero-Width Space (Primary workflow character)
ZW_NON_JOINER = "\u200c"  # Zero-Width Non-Joiner
ZW_JOINER = "\u200d"      # Zero-Width Joiner
WORD_JOINER = "\u2060"    # Word Joiner
ZW_NO_BREAK = "\ufeff"    # Zero-Width No-Break Space (Byte Order Mark)

ALL_INVISIBLE_CHARS: Set[str] = {
    ZW_SPACE,
    ZW_NON_JOINER,
    ZW_JOINER,
    WORD_JOINER,
    ZW_NO_BREAK,
}

# Frequency presets mapping
FREQUENCY_LEVELS = {
    "minimum": 0.20,
    "normal": 0.45,
    "medium": 0.70,
    "maximum": 1.00,
}


def strip_invisible_characters(text: str, targets: Set[str] | None = None) -> str:
    """
    Removes all invisible zero-width Unicode characters from the given text.

    :param text: Input string.
    :param targets: Set of invisible characters to strip. Defaults to ALL_INVISIBLE_CHARS.
    :return: Sanitized string without invisible characters.
    """
    if not text:
        return ""
    chars_to_remove = targets if targets is not None else ALL_INVISIBLE_CHARS
    return "".join(c for c in text if c not in chars_to_remove)


def count_invisible_characters(text: str, targets: Set[str] | None = None) -> int:
    """
    Counts the number of invisible zero-width characters in the given text.
    """
    if not text:
        return 0
    chars_to_count = targets if targets is not None else ALL_INVISIBLE_CHARS
    return sum(1 for c in text if c in chars_to_count)


def insert_zero_width_spaces(
    text: str,
    frequency: float | str = 0.45,
    clean_existing: bool = True,
    seed: int | None = None,
    **kwargs,
) -> str:
    """
    Inserts invisible Zero-Width Space characters (\u200B) inside/after alphanumeric characters
    to disrupt automated tokenization patterns while keeping visual rendering identical.

    :param text: The input string to obfuscate.
    :param frequency: Probability (0.0 to 1.0) or level name ('minimum', 'normal', 'medium', 'maximum').
    :param clean_existing: If True, existing invisible characters are removed first to prevent compound bloat.
    :param seed: Optional random seed for deterministic reproduction / testing.
    :return: The obfuscated string with invisible zero-width spaces injected.
    """
    if not text:
        return ""

    # Resolve frequency from preset string or numeric value
    if isinstance(frequency, str):
        freq_float = FREQUENCY_LEVELS.get(frequency.lower().strip(), 0.45)
    else:
        freq_float = float(frequency)

    # Clamp frequency between 0.0 and 1.0
    freq_float = max(0.0, min(1.0, freq_float))

    # Clean existing invisible characters if requested
    processed_text = strip_invisible_characters(text) if clean_existing else text

    if freq_float <= 0.0:
        return processed_text

    rng = random.Random(seed) if seed is not None else random

    obfuscated_chars = []
    for char in processed_text:
        obfuscated_chars.append(char)

        # Only insert after alphanumeric characters to avoid breaking visible spaces,
        # line endings (\n, \r), emoji variation sequences, and punctuation marks.
        if char.isalnum():
            if rng.random() < freq_float:
                obfuscated_chars.append(ZW_SPACE)

    return "".join(obfuscated_chars)


def reveal_invisible_characters(text: str, marker: str = "[ZWSP]") -> str:
    """
    Replaces invisible characters with a visible marker for visual inspection and debugging.
    """
    if not text:
        return ""
    return "".join(marker if c in ALL_INVISIBLE_CHARS else c for c in text)


def get_text_statistics(text: str) -> Dict[str, Any]:
    """
    Calculates detailed text statistics including visible chars, hidden chars, words, lines, and UTF-8 size.
    """
    if not text:
        return {
            "total_chars": 0,
            "visible_chars": 0,
            "invisible_chars": 0,
            "words": 0,
            "lines": 0,
            "utf8_bytes": 0,
        }

    total_chars = len(text)
    invisible_chars = count_invisible_characters(text)
    visible_chars = total_chars - invisible_chars

    # Word count: strip invisible chars first so words split cleanly on whitespace
    clean_text = strip_invisible_characters(text)
    words = len(re.findall(r"\S+", clean_text))

    # Lines: count newlines + 1 if text is non-empty
    lines = len(text.splitlines()) if text else 0

    utf8_bytes = len(text.encode("utf-8"))

    return {
        "total_chars": total_chars,
        "visible_chars": visible_chars,
        "invisible_chars": invisible_chars,
        "words": words,
        "lines": lines,
        "utf8_bytes": utf8_bytes,
    }
