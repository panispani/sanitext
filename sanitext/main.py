import pyperclip
import typer

app = typer.Typer()

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


# Test
#     sample_text = "Thіs tеxt cоntaіns homoglyphs and invіsiblе characters.​"
#     ascii_text = "This text contains homoglyphs and invisible characters."  # this is actually ascii

# CLI design
# mytool --detect         # Detect characters only
# mytool --string         # Process the string and print it
# mytool                  # Process the clipboard string, copy to clipboard, print if unchanged
# mytool --verbose        # Process + show detected info


@app.command()
def main(
    detect: bool = typer.Option(
        False, "--detect", "-d", help="Detect characters only."
    ),
    text: bool = typer.Option(
        False, "--string", "-s", help="Provide the processed string."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose mode (show detected info)."
    ),
):
    """Processes text from the clipboard or prints processed text."""

    if not text:
        text = pyperclip.paste()
        if not text:
            typer.echo("Clipboard is empty and no string was provided!", err=True)
            raise typer.Exit(1)

    if detect:
        detected_info = detect_unicode_anomalies(text)
        typer.echo(f"Detected: {detected_info}")
        raise typer.Exit(0)

    if verbose:
        detected_info = detect_unicode_anomalies(text)
        typer.echo(f"Input: {text}")
        typer.echo(f"Detected: {detected_info}")

    processed_text = normalize_to_standard(text)
    text_log = ("\nOutput:\n" + processed_text) if verbose else ""

    if processed_text != text:
        pyperclip.copy(processed_text)
        typer.echo("Processed and copied to clipboard." + text_log)
    else:
        typer.echo("No changes!" + text_log)


if __name__ == "__main__":
    app()
