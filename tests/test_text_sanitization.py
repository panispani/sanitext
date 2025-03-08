import pytest
import string
import unicodedata
import tempfile
from pathlib import Path

from sanitext.text_sanitization import (
    get_allowed_characters,
    sanitize_text,
    closest_ascii,
    detect_suspicious_characters,
)


@pytest.fixture
def ascii_allowed():
    """
    A fixture that returns the default set of ASCII-printable allowed characters.
    """
    return get_allowed_characters()


@pytest.fixture
def all_unicode_allowed():
    """
    A fixture that returns a set of all Unicode characters.
    """
    return get_allowed_characters(allow_unicode=True)


# -------------------------------------------------------------------
# Tests for get_allowed_characters
# -------------------------------------------------------------------


def test_get_allowed_characters_default(ascii_allowed):
    """
    By default, the allowed set should contain `string.printable` but not beyond.
    """
    # Check that typical ASCII chars are included
    for ch in "ABC123!@# \t\n\r":
        assert ch in ascii_allowed, f"Default allowed set should contain '{ch}'"

    # Check that a typical non-ASCII char is excluded
    assert "é" not in ascii_allowed, "Default allowed set should NOT contain 'é'"


def test_get_allowed_characters_all_unicode(all_unicode_allowed):
    """
    If allow_unicode=True, the allowed set should contain Basic Multilingual Plane.
    """
    # Check that typical ASCII chars are included
    for ch in "ABC123!@# \t\n\r":
        assert ch in all_unicode_allowed

    # Check that a typical non-ASCII char is included
    assert "é" in all_unicode_allowed, "All unicode set should contain 'é'"
    # Check that an unusual symbol is included
    assert "𝑇" in all_unicode_allowed, "All unicode set should contain '𝑇'"


def test_get_allowed_characters_custom_chars(ascii_allowed):
    """
    Adding a custom set of characters via 'allow_chars'.
    """
    extra_chars = "ⓝⓔⓦ"
    custom_allowed = get_allowed_characters(allow_chars=extra_chars)

    # Everything in ascii_allowed should still be included
    for ch in ascii_allowed:
        assert ch in custom_allowed

    # The extra characters should also be included
    for ch in extra_chars:
        assert ch in custom_allowed, f"Custom allowed set should contain '{ch}'"


def test_get_allowed_characters_from_file(ascii_allowed):
    """
    Create a temporary file with some extra characters, then pass
    that file to 'get_allowed_characters(allow_file=...)'.
    """
    extra_chars = "é⛄✅"
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "allowed.txt"
        filepath.write_text(extra_chars, encoding="utf-8")

        custom_allowed = get_allowed_characters(allow_file=filepath)

        # All default ASCII chars must remain
        for ch in ascii_allowed:
            assert ch in custom_allowed

        # Now our extra characters from the file should be included
        for ch in extra_chars:
            assert ch in custom_allowed


# -------------------------------------------------------------------
# Tests for closest_ascii
# -------------------------------------------------------------------


@pytest.mark.parametrize(
    "char,expected",
    [
        # 1) Simple accent
        ("é", "e"),
        # 2) Example with a roman numeral => "Ⅵ" => "VI"
        ("Ⅵ", "VI"),
        # 3) Ligature fi => "ﬁ" => "fi"
        ("ﬁ", "fi"),
        # 4) Already ASCII => "A" => "A"
        ("A", "A"),
    ],
)
def test_closest_ascii_simple(char, expected, ascii_allowed):
    """
    Tests straightforward decomposition or normalization.
    """
    replaced = closest_ascii(char, ascii_allowed)
    assert replaced == expected, f"Expected '{char}' -> '{expected}', got '{replaced}'"


def test_closest_ascii_disallowed_result(ascii_allowed):
    """
    If the normalization yields some chars not in the allowed set, those should be dropped.
    For example, if we artificially remove 'V' from the allowed set, then 'Ⅵ' might degrade further.
    """
    custom_set = ascii_allowed.copy()
    custom_set.discard("V")  # Remove 'V' from the set to cause a partial fallback

    replaced = closest_ascii("Ⅵ", custom_set)
    # "Ⅵ" normally decomposes to "V" + "I", but 'V' is disallowed,
    # so only "I" can remain if "I" is still in the set.
    assert replaced == "I", f"Expected 'I' if 'V' is disallowed, but got '{replaced}'"


def test_closest_ascii_no_decomposition_or_normalization(ascii_allowed):
    """
    If there's no decomposition or normalization that yields an allowed char,
    we expect an empty string.
    """
    # Choose a random symbol that doesn't decompose to ASCII, e.g. '☯'
    symbol = "☯"
    replaced = closest_ascii(symbol, ascii_allowed)
    # Default ASCII set doesn't include '☯',
    # and it doesn't have a direct NFKC or decomposition to ASCII letters.
    assert replaced == "", f"Expected an empty string if no decomposition possible."


# -------------------------------------------------------------------
# Tests for detect_suspicious_characters
# -------------------------------------------------------------------


def test_detect_suspicious_characters_none(ascii_allowed):
    text = "Hello, world!\n\t123"
    # This is all within ASCII printable, so we expect an empty list
    suspicious = detect_suspicious_characters(text, ascii_allowed)
    assert suspicious == [], "Expected no suspicious characters."


def test_detect_suspicious_characters_mixed(ascii_allowed):
    text = "Hello, wörld! Ⅵ abc ﬁ і\n"
    # Among these, "ö", "Ⅵ", and "ﬁ" are not in default ASCII allowed
    suspicious = detect_suspicious_characters(text, ascii_allowed)
    # We'll just check that we found them, not the exact order
    found_chars = [item[0] for item in suspicious]
    assert "ö" in found_chars
    assert "Ⅵ" in found_chars
    assert "ﬁ" in found_chars
    assert "і" in found_chars

    # Also verify that we get the correct Unicode names
    # (we won't do an exact match because names can differ slightly by Python version,
    # but we can do a substring check or partial check)
    for ch, name in suspicious:
        assert ch in found_chars
        # Just do a sanity check
        assert len(name) > 1, "Unicode name should be a non-empty string."


def test_detect_suspicious_characters_empty(ascii_allowed):
    text = ""
    suspicious = detect_suspicious_characters(text, ascii_allowed)
    assert suspicious == [], "Empty text should yield no suspicious characters."


# -------------------------------------------------------------------
# Tests for sanitize_text (non-interactive)
# -------------------------------------------------------------------


# TODO: how do i run only one of them
@pytest.mark.parametrize(
    "text, expected",
    [
        # 1) No disallowed => Should remain the same
        ("Hello, world!\n", "Hello, world!\n"),
        # 2) Contains a decomposable char => e.g., "é"
        ("Café", "Cafe"),
        # 3) Contains a symbol that can't be decomposed => e.g., "☯"
        ("Peace ☯ within", "Peace  within"),  # '☯' replaced with ""
        # 4) Mixed example => "Ⅵ is VI" => "VI is VI"
        ("Ⅵ is VI", "VI is VI"),
    ],
)
def test_sanitize_text_default(text, expected, ascii_allowed):
    """
    By default (non-interactive), sanitize_text should use closest_ascii
    to handle disallowed characters.
    """
    sanitized = sanitize_text(text, allowed_characters=ascii_allowed, interactive=False)
    assert sanitized == expected, (
        f"Failed text: {text}, " f"Found: {sanitized}, " f"Expected: {expected}"
    )


def test_sanitize_text_all_unicode(all_unicode_allowed):
    """
    If everything is allowed, sanitize_text should return the original text.
    """
    text = "Any unicode text: Café ☯ Ⅵ ﬁ 𝔗"
    sanitized = sanitize_text(
        text, allowed_characters=all_unicode_allowed, interactive=False
    )
    assert sanitized == text, "When all unicode is allowed, we expect no changes."


def test_sanitize_text_no_disallowed_return_same(ascii_allowed):
    text = "Just ASCII printable stuff 123 !@#\n"
    sanitized = sanitize_text(text, allowed_characters=ascii_allowed, interactive=False)
    assert (
        sanitized == text
    ), "If there's nothing disallowed, we should get the exact same string."


def test_sanitize_text_all_disallowed():
    """
    If the allowed set is very small, basically everything should get replaced or removed.
    """
    # Suppose we only allow 'A' and 'B'
    minimal_allowed = set("AB")
    text = "Hello, world! Café Ⅵ"
    # 'H', 'e', 'l', 'o', etc. are not in minimal_allowed
    # closest_ascii attempts might degrade them.
    # But eventually, if 'h' -> 'h' is not allowed, it becomes ''
    # because there's no further decomposition that leads to A/B/C.
    # We might still get partial decompositions for e.g. "é" => "e" => still not allowed => ""
    # "Ⅵ" => "VI" => 'V' not allowed => '', 'I' is not allowed => '' => total => ''
    sanitized = sanitize_text(
        text, allowed_characters=minimal_allowed, interactive=False
    )
    assert (
        sanitized == ""
    ), f"With a minimal allowed set, everything gets removed or replaced with ''. Got: {sanitized}"
