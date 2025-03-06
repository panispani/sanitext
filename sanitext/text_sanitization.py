# Test
#     sample_text = "Thіs tеxt cоntaіns homoglyphs and invіsiblе characters.​"
#     ascii_text = "This text contains homoglyphs and invisible characters."  # this is actually ascii


import unicodedata
import re

# Mapping Unicode homoglyphs to standard ASCII equivalents
HOMOGLYPH_MAP = {
    "а": "a",
    "е": "e",
    "о": "o",
    "с": "c",
    "р": "p",
    "х": "x",
    "і": "i",
    "ԁ": "d",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "„": '"',
    "‐": "-",
    "–": "-",
    "—": "-",
    " ": " ",
    " ": " ",
    "​": "",
    " ": " ",
    " ": " ",
    " ": " ",
    "⠀": " ",
    "᠎": " ",
    "𝐀": "A",
    "𝐁": "B",
    "ℂ": "C",
    "ℰ": "E",
    "ℱ": "F",
    "ℝ": "R",
    "ℤ": "Z",
    "Ａ": "A",
    "Ｂ": "B",
    "Ｃ": "C",
    "Ｄ": "D",
    "Ｅ": "E",
    "１": "1",
    "２": "2",
    "３": "3",
}

# Pattern to detect invisible characters
INVISIBLE_CHARACTERS = re.compile(r"[​‌‍ ⠀᠎༴]")


def detect_unicode_anomalies(text):
    """Detects non-standard Unicode characters in a given text."""
    anomalies = []
    for char in text:
        if char in HOMOGLYPH_MAP or INVISIBLE_CHARACTERS.search(char):
            anomalies.append((char, unicodedata.name(char, "Unknown")))
    return anomalies


def normalize_to_standard(text):
    """Replaces non-standard Unicode characters with their ASCII equivalents."""
    # Replace known homoglyphs
    for uni_char, ascii_char in HOMOGLYPH_MAP.items():
        text = text.replace(uni_char, ascii_char)

    # Remove invisible characters
    text = INVISIBLE_CHARACTERS.sub("", text)

    # Apply Unicode normalization
    return unicodedata.normalize("NFKC", text)
