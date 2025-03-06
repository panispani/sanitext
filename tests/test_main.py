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
