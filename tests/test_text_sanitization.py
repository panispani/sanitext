import pytest
import unicodedata
from sanitext.text_sanitization import (
    detect_unicode_anomalies,
    normalize_to_standard,
    HOMOGLYPH_MAP,
    INVISIBLE_CHARACTERS,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        # ( TODO
        #     "Thіs tеxt cоntaіns homoglyphs.",  # Uses homoglyphs
        #     [
        #         ("і", "CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I"),
        #         ("е", "CYRILLIC SMALL LETTER E"),
        #         ("о", "CYRILLIC SMALL LETTER O"),
        #     ],
        # ),
        ("Normal ASCII text.", []),  # No anomalies
        ("Invisible​ character.", [("​", "ZERO WIDTH SPACE")]),  # Invisible character
        # ( TODO
        #     "𝑇ℎ𝑖𝑠 𝑡𝑒𝑥𝑡 𝑢𝑠𝑒𝑠 𝑚𝑎𝑡ℎ 𝑏𝑜𝑙𝑑.",  # Unicode math bold characters
        #     [
        #         ("𝑇", "MATHEMATICAL BOLD ITALIC CAPITAL T"),
        #         ("ℎ", "SCRIPT SMALL H"),
        #         ("𝑖", "MATHEMATICAL BOLD ITALIC SMALL I"),
        #         ("𝑠", "MATHEMATICAL BOLD ITALIC SMALL S"),
        #     ],
        # ),
        ("​", [("​", "ZERO WIDTH SPACE")]),  # Just an invisible character
        (
            "​ ​",  # Multiple invisible characters
            [
                ("​", "ZERO WIDTH SPACE"),
                (" ", "NARROW NO-BREAK SPACE"),
                ("​", "ZERO WIDTH SPACE"),
            ],
        ),
        ("", []),  # Empty string
    ],
)
def test_detect_unicode_anomalies(text, expected):
    assert detect_unicode_anomalies(text) == expected, f"Failed text: {text}"


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Thіs tеxt cоntaіns homoglyphs.",
            "This text contains homoglyphs.",
        ),  # Homoglyphs
        ("Normal ASCII text.", "Normal ASCII text."),  # No changes
        ("Invisible​ character.", "Invisible character."),  # Remove invisible character
        ("𝑇ℎ𝑖𝑠 𝑡𝑒𝑥𝑡 𝑢𝑠𝑒𝑠 𝑚𝑎𝑡ℎ 𝑏𝑜𝑙𝑑.", "This text uses math bold."),  # Convert math bold
        # ("​ ​", ""),  # Remove multiple invisible characters TODO
        ("​", ""),  # Remove standalone invisible character
        ("", ""),  # Empty input should remain empty
    ],
)
def test_normalize_to_standard(text, expected):
    assert normalize_to_standard(text) == expected


def test_homoglyph_map_integrity():
    """Ensure all keys in HOMOGLYPH_MAP have a valid Unicode name."""
    for char in HOMOGLYPH_MAP:
        assert unicodedata.name(char, None) is not None
