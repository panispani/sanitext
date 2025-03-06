import unicodedata
import re
import string

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
# INVISIBLE_CHARACTERS = re.compile(r"[\u200B\u200C\u200D\u202F\u2800\u180E\u0F34]")


def detect_unicode_anomalies(text):
    """
    Detect non-standard Unicode characters in the given text.

    Args:
        text (str): The input text to analyze.

    Returns:
        list of tuple:
            A list of tuples where each tuple contains a
            non-standard character and its Unicode name.
    """
    anomalies = []
    for char in text:
        if char in HOMOGLYPH_MAP or INVISIBLE_CHARACTERS.search(char):
            anomalies.append((char, unicodedata.name(char, "Unknown")))
    return anomalies


def detect_suspicious_characters(text):
    """
    Finds characters in the text that are not ASCII letters, digits, punctuation, or common whitespace.

    Args:
        text (str): The input text to check.

    Returns:
        list of tuple: A list of tuples, each containing a suspicious character and its Unicode name.
    """
    # Define the expected character set (ASCII letters, digits, and basic punctuation)
    ALLOWED_CHARACTERS = set(
        string.ascii_letters + string.digits + string.punctuation + " \n\r\t"
    )
    return [
        (char, unicodedata.name(char, "Unknown"))
        for char in text
        if char not in ALLOWED_CHARACTERS
    ]


def normalize_to_standard(text):
    """Replaces non-standard Unicode characters with their ASCII equivalents."""
    # Replace known homoglyphs
    for uni_char, ascii_char in HOMOGLYPH_MAP.items():
        text = text.replace(uni_char, ascii_char)

    # Remove invisible characters
    text = INVISIBLE_CHARACTERS.sub("", text)

    # Apply Unicode normalization
    return unicodedata.normalize("NFKC", text)
