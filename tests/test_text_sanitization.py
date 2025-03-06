import pytest
import unicodedata
from sanitext.text_sanitization import (
    detect_unicode_anomalies,
    normalize_to_standard,
    HOMOGLYPH_MAP,
    INVISIBLE_CHARACTERS,
)


def test_homoglyph_map_integrity():
    """Ensure all keys in HOMOGLYPH_MAP have a valid Unicode name."""
    for char in HOMOGLYPH_MAP:
        assert unicodedata.name(char, None) is not None
