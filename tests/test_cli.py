import pytest
import pyperclip
from typer.testing import CliRunner
from unittest.mock import patch
from pathlib import Path
import tempfile

from sanitext.cli import app

runner = CliRunner()


def test_cli_detect():
    """Test detection of unicode anomalies."""
    result = runner.invoke(app, ["--detect", "-s", "Thіs іs а test."])
    assert "Detected:" in result.output
    # Check that suspicious chars are reported
    # Example substring checks for partial Unicode names
    assert "CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I" in result.output
    assert "CYRILLIC SMALL LETTER A" in result.output
    assert result.exit_code == 0


def test_cli_process():
    """Test processing and replacing text."""
    result = runner.invoke(app, ["--string", "Thіs іs а test.🔥"])
    assert "This is a test." in result.output
    assert result.exit_code == 0


def test_cli_verbose():
    """Test verbose mode output."""
    result = runner.invoke(app, ["--verbose", "-s", "Thіs іs а test."])
    assert "Detected:" in result.output
    assert "Output: This is a test." not in result.output
    assert result.exit_code == 0


def test_cli_very_verbose():
    """Test very verbose mode output."""
    result = runner.invoke(app, ["--very-verbose", "-s", "Thіs іs а test."])
    assert "Input: Thіs іs а test." in result.output
    assert "Detected:" in result.output
    assert "Output: This is a test." in result.output
    assert result.exit_code == 0


def test_cli_clipboard(monkeypatch):
    """Test clipboard processing."""
    monkeypatch.setattr(pyperclip, "paste", lambda: "Thіs іs а test.")  # Mock clipboard
    result = runner.invoke(app)
    assert "Processed and copied to clipboard." in result.output
    # Confirm the final sanitized text is indeed in the clipboard
    assert pyperclip.paste() == "This is a test."
    assert result.exit_code == 0


def test_cli_no_clipboard(monkeypatch):
    """Test error when clipboard is empty."""
    monkeypatch.setattr(pyperclip, "paste", lambda: "")  # Empty clipboard
    result = runner.invoke(app)
    assert (
        "Error: No text provided (clipboard is empty and no string was given)."
        in result.output
    )
    assert result.exit_code == 1


def test_cli_allow_chars():
    """
    Test allowing extra characters manually via --allow-chars.
    """
    # 'ä' is normally disallowed. If we allow it explicitly, it should pass through.
    input_text = "Look, an umlaut: ä"
    result = runner.invoke(app, ["--allow-chars", "ä", "-s", input_text])
    assert "Look, an umlaut: ä" in result.output
    # Without --allow-chars "ä", it would normally become "Look, an umlaut: a"
    assert result.exit_code == 0


def test_cli_allow_emoji():
    """
    Test allowing single code point emoji via --allow-emoji.
    """
    # '😎' is normally disallowed. If we allow it explicitly, it should pass through.
    input_text = "Look, a boss 😎"
    result = runner.invoke(app, ["--allow-emoji", "-s", input_text])
    assert "Look, a boss 😎" in result.output
    # Without --allow-emoji, it would normally become "Look, a boss "
    assert result.exit_code == 0


def test_cli_allow_file():
    """
    Test allowing extra characters from a file.
    """
    # We want to allow 'é' from a file
    extra_chars = "é\n"
    input_text = "Café ø"
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "allowed_chars.txt"
        # Write the extra char to the file
        fpath.write_text(extra_chars, encoding="utf-8")

        # Now run the CLI using that file
        result = runner.invoke(app, ["--allow-file", str(fpath), "-s", input_text])
        assert (
            "Café o" in result.output
        ), "Expected 'é' to remain because we allowed it."
        assert result.exit_code == 0


def test_cli_detect_with_allowed_file():
    """
    Use --detect with a file-based allowed char.
    The char from the file is allowed, other disallowed remain suspicious.
    """
    extra_chars = "é\n"  # We'll allow 'é' only
    input_text = "Café ☯"
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "allowed_chars.txt"
        fpath.write_text(extra_chars, encoding="utf-8")

        result = runner.invoke(
            app, ["--detect", "--allow-file", str(fpath), "-s", input_text]
        )
        # 'é' is allowed now, so it shouldn't appear in "Detected:"
        # '☯' is disallowed => must appear in "Detected:"
        assert "Café" not in result.output  # It's not a direct sanitization
        # Instead, we see "Detected: [ ... (☯, 'YIN YANG') ... ]"
        assert "☯" in result.output
        # We do not expect 'é' in the detected list
        assert "é" not in result.output
        assert "Detected:" in result.output
        assert result.exit_code == 0


def test_cli_string_none_copy_back_if_changed(monkeypatch):
    """
    If --string is not provided, we pull from clipboard.
    If the sanitized text changes, it is copied back.
    If no changes, we see "No changes!"
    """
    # 1. Case: text has disallowed characters => it changes => "Processed and copied..."
    monkeypatch.setattr(pyperclip, "paste", lambda: "Café ☯")  # Disallowed char: ☯
    with patch.object(pyperclip, "copy") as mock_copy:
        result = runner.invoke(app)
        assert "Processed and copied to clipboard." in result.output
        # The sanitized text should presumably be "Cafe "
        # or "Cafe  " (depending on newlines) or similar.
        sanitized = mock_copy.call_args[0][0]
        assert "☯" not in sanitized  # The symbol should be removed
        assert result.exit_code == 0

    # 2. Case: text has only allowed ASCII => no changes => "No changes!"
    monkeypatch.setattr(pyperclip, "paste", lambda: "Just ASCII!")
    with patch.object(pyperclip, "copy") as mock_copy:
        result = runner.invoke(app)
        assert "No changes!" in result.output
        assert not mock_copy.called, "Should not copy if nothing changed."
        assert result.exit_code == 0


def test_cli_interactive_keep(monkeypatch):
    """
    Demonstrate interactive mode for a single disallowed character,
    where the user chooses 'keep' (y).
    """
    # Suppose the input text is "Café". 'é' is disallowed by default ASCII rules.
    text = "Café"

    # We'll have the user input "y" => keep the char
    # (The sanitize_text logic should then preserve it.)
    def mock_input(prompt):
        return "y"

    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr(pyperclip, "paste", lambda: text)

    result = runner.invoke(app, ["--interactive"])

    # We expect the final output to contain "Café" because we "kept" 'é'
    assert "No changes!" in result.output
    # Possibly "Processed and copied to clipboard."
    # because the text was changed from the default logic's perspective
    # (well, actually we 'kept' the char, so let's see if it was considered changed or not).
    # If the code doesn't consider "keep" as a no-change scenario, it'll copy.
    # It's up to the internal logic. We'll be lenient here, just check exit code.
    assert result.exit_code == 0


def test_cli_interactive_remove_replace(monkeypatch):
    """
    More advanced interactive test: multiple distinct disallowed chars,
    user decisions: first => remove, second => replace with '?'.
    """
    # Input has 2 disallowed characters: "é" and "☯"
    text = "Some text: Café ☯"

    # We'll queue the interactive responses:
    # For 'é' => user chooses 'n' => remove
    # For '☯' => user chooses 'r' => then input "?"
    user_inputs = iter(["n", "r", "?"])

    def mock_input(prompt):
        return next(user_inputs)

    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr(pyperclip, "paste", lambda: text)

    result = runner.invoke(app, ["--interactive", "-vv"])

    # We expect: "Café" => "Caf" because 'é' was removed,
    # Then " ☯" => " ?" because '☯' was replaced with '?'
    # So the final is "Some text: Caf ?"
    assert "Some text: Caf ?" in result.output, f"Got: {result.output}"
    assert result.exit_code == 0


def test_cli_help():
    """
    Simple check that `sanitext --help` works (and doesn't crash).
    """
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Just check that some usage text is displayed
    assert (
        "Usage: main [OPTIONS]" in result.output
        or "Usage: cli [OPTIONS]" in result.output
    )
    assert "--detect" in result.output
    assert "--interactive" in result.output
    assert "--allow-chars" in result.output
    assert "--allow-emoji" in result.output
    assert "--allow-file" in result.output
