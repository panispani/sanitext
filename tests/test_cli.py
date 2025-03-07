import pytest
import pyperclip
from typer.testing import CliRunner
from sanitext.main import app

runner = CliRunner()


def test_cli_detect():
    """Test detection of unicode anomalies."""
    result = runner.invoke(app, ["--detect", "-s", "Thіs іs а test."])
    assert "Detected:" in result.output
    assert "CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I" in result.output
    assert "CYRILLIC SMALL LETTER A" in result.output
    assert result.exit_code == 0


def test_cli_process():
    """Test processing and replacing text."""
    result = runner.invoke(app, ["--string", "Thіs іs а test."])
    assert "This is a test." in result.output
    assert result.exit_code == 0


def test_cli_verbose():
    """Test verbose mode output."""
    result = runner.invoke(app, ["--verbose", "-s", "Thіs іs а test."])
    assert "Input: Thіs іs а test." in result.output
    assert "Detected:" in result.output
    assert "Output: This is a test." in result.output
    assert result.exit_code == 0


def test_cli_clipboard(monkeypatch):
    """Test clipboard processing."""
    monkeypatch.setattr(pyperclip, "paste", lambda: "Thіs іs а test.")  # Mock clipboard
    result = runner.invoke(app)
    assert "Processed and copied to clipboard." in result.output
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
