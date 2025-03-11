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
from sanitext.emoji_set import EMOJI_SET


@pytest.fixture
def ascii_allowed():
    """
    A fixture that returns the default set of ASCII-printable allowed characters.
    """
    return get_allowed_characters()


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

    # Check that an emoji is excluded
    assert "😀" not in ascii_allowed, "Default allowed set should NOT contain '😀'"


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


def test_get_allowed_characters_emoji(ascii_allowed):
    """
    Adding support for single code point emoji via 'allow_emoji'.
    """
    custom_allowed = get_allowed_characters(allow_emoji=True)

    # Everything in ascii_allowed should still be included
    for ch in ascii_allowed:
        assert ch in custom_allowed

    # Emojis should also be included
    assert "😀" in custom_allowed, f"Custom allowed set should contain '😀'"
    for ch in EMOJI_SET:
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


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello, world! 👋", [("👋", "WAVING HAND SIGN")]),
        (
            "Thіs tеxt cоntaіns homoglyphs.",  # Uses homoglyphs
            [
                ("і", "CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I"),
                ("е", "CYRILLIC SMALL LETTER IE"),
                ("о", "CYRILLIC SMALL LETTER O"),
                ("і", "CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I"),
            ],
        ),
        ("Normal ASCII text.", []),  # No anomalies
        ("Invisible​ character.", [("​", "ZERO WIDTH SPACE")]),  # Invisible character
        (
            "𝑇ℎ𝑖𝑠.",  # Unicode math characters
            [
                ("𝑇", "MATHEMATICAL ITALIC CAPITAL T"),
                ("ℎ", "PLANCK CONSTANT"),
                ("𝑖", "MATHEMATICAL ITALIC SMALL I"),
                ("𝑠", "MATHEMATICAL ITALIC SMALL S"),
            ],
        ),
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
def test_detect_suspicious_characters_parametrized(text, expected):
    detected_characters = detect_suspicious_characters(
        text, allowed_characters=get_allowed_characters()
    )
    assert detected_characters == expected, (
        f"Failed text: {text}, "
        f"Found: {detected_characters}, "
        f"Expected: {expected}"
    )


# -------------------------------------------------------------------
# Tests for sanitize_text (non-interactive)
# -------------------------------------------------------------------


# TODO: how to run only one of these easily
@pytest.mark.parametrize(
    "text, expected",
    [
        # No disallowed => Should remain the same
        ("Hello, world!\n", "Hello, world!\n"),
        # Contains a decomposable char => e.g., "é"
        ("Café", "Cafe"),
        # Contains a symbol that can't be decomposed => e.g., "☯"
        ("Peace ☯ within", "Peace  within"),  # '☯' replaced with ""
        # Mixed example => "Ⅵ is VI" => "VI is VI"
        ("Ⅵ is VI", "VI is VI"),
        # Homoglyphs
        (
            "Thіs tеxt cоntaіns homoglyphs.",
            "This text contains homoglyphs.",
        ),
        # No changes
        ("Normal ASCII text.", "Normal ASCII text."),
        # Remove invisible character
        ("Invisible​ character.", "Invisible character."),
        # Convert math bold
        ("𝑇ℎ𝑖𝑠 𝑡𝑒𝑥𝑡 𝑢𝑠𝑒𝑠 𝑚𝑎𝑡ℎ 𝑏𝑜𝑙𝑑.", "This text uses math bold."),
        # Remove multiple invisible characters
        ("​ ​", " "),
        # Remove standalone invisible character
        ("​", ""),
        # Empty input should remain empty
        ("", ""),
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


# -------------------------------------------------------------------
# Testing interactive mode
# -------------------------------------------------------------------
def test_sanitize_text_interactive(monkeypatch, ascii_allowed):
    """
    Mock user input for interactive decisions:
        - keep 'é'
        - remove 'ø'
        - replace '☯' with '?'
    """
    # We'll contrive a text with exactly three distinct disallowed characters: é, ☯, and ø
    text = "Hello é, ø, and ☯!"

    # A queue of user responses:
    # 1) 'y' => keep 'é'
    # 2) 'n' => remove 'ø'
    # 3) 'r' => replace '☯' with '?'
    inputs = iter(["y", "n", "r", "?"])

    def fake_input(prompt):
        return next(inputs)

    # Use monkeypatch to replace 'input'
    monkeypatch.setattr("builtins.input", fake_input)

    sanitized = sanitize_text(text, allowed_characters=ascii_allowed, interactive=True)
    # We expect: "Hello é, , and ?!"
    # Because 'é' was kept, 'ø' was removed, '☯' was replaced with '?'
    assert sanitized == "Hello é, , and ?!"


def test_sanitize_text_interactive_repeated_characters(monkeypatch, ascii_allowed):
    """
    Mock user input for interactive decisions:
      - é => Replace with "!"
      No need to ask again, even though é appears 3 times because its fate
      has been decided
    """
    # We'll contrive a text with exactly three distinct disallowed characters: é, ☯, and ø
    text = "Hello é, é, and é!"

    # 'y' => replace 'é' with '!'
    inputs = iter(["r", "!"])

    def fake_input(prompt):
        return next(inputs)

    # Use monkeypatch to replace 'input'
    monkeypatch.setattr("builtins.input", fake_input)

    sanitized = sanitize_text(text, allowed_characters=ascii_allowed, interactive=True)
    # We expect: "Hello !, !, and !!"
    # Because all 'é' were replaced with '!'
    assert sanitized == "Hello !, !, and !!"
