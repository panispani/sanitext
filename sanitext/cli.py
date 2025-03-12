"""
sanitext: A command-line tool and Python library for text sanitization.

Features:
  - Detect suspicious characters in text.
  - Sanitize text by removing or replacing non-allowed characters.
  - Customizable character filtering:
      - By default, only allows ASCII printable characters.
      - Optionally allow Unicode characters (--allow-unicode).
      - Specify additional allowed characters (--allow-chars).
      - Load a file containing allowed characters (--allow-file).
  - Interactive mode (--interactive):
      - Manually decide what to do with disallowed characters (keep, remove, replace).

Usage examples:
  - sanitext --detect          # Detect characters only
  - sanitext --string "text"   # Process the provided string and print it
  - sanitext                   # Process the clipboard string, copy to clipboard, print if unchanged
  - sanitext --verbose         # Process + show detected info
  - sanitext --very-verbose    # Process + show input, detected info, and output
  - sanitext --allow-chars "αñøç"  # Allow additional characters (only single unicode code point)
  - sanitext --allow-file allowed_chars.txt  # Allow characters from a file
  - sanitext --allow-emoji     # Allow single code point emoji
  - sanitext --interactive     # Prompt user for handling disallowed characters
"""

import pyperclip
import typer
from pathlib import Path

from sanitext.text_sanitization import (
    detect_suspicious_characters,
    sanitize_text,
    get_allowed_characters,
)


app = typer.Typer()


@app.command()
def main(
    detect: bool = typer.Option(
        False, "--detect", "-d", help="Detect characters only."
    ),
    string: str = typer.Option(
        None, "--string", "-s", help="Process the provided string and print it."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose mode (process + show detected info)."
    ),
    very_verbose: bool = typer.Option(
        False,
        "--very-verbose",
        "-vv",
        help="Very verbose mode (process + show input, detected info, and output).",
    ),
    allow_chars: str = typer.Option(
        None,
        "--allow-chars",
        help='Additional characters to allow, e.g. --allow-chars "αñøç"',
    ),
    allow_emoji: bool = typer.Option(
        False,
        "--allow-emoji",
        help='Allow single code point emoji"',  # TODO: extend to multiple codepoints
    ),
    allow_file: Path = typer.Option(
        None,
        "--allow-file",
        help="Path to a file containing characters to allow (one big string or multiple lines).",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive prompt for disallowed characters.",
    ),
):
    # Get text from either CLI or clipboard
    text = string if string is not None else pyperclip.paste()
    if not text:
        typer.echo(
            "Error: No text provided (clipboard is empty and no string was given).",
            err=True,
        )
        raise typer.Exit(1)

    allowed_characters = get_allowed_characters(
        allow_chars=allow_chars,
        allow_file=allow_file,
        allow_emoji=allow_emoji,
    )

    # If detection-only, just do detection and exit
    if detect:
        detected_info = detect_suspicious_characters(
            text, allowed_characters=allowed_characters
        )
        typer.echo(f"Detected: {detected_info}")
        raise typer.Exit(0)

    # Otherwise, sanitize
    processed_text = sanitize_text(
        text,
        allowed_characters=allowed_characters,
        interactive=interactive,
    )

    if very_verbose:
        detected_info = detect_suspicious_characters(
            text, allowed_characters=allowed_characters
        )
        typer.echo(f"Input: {text}")
        typer.echo(f"Detected: {detected_info}")
        typer.echo(f"Output: {processed_text}")
    elif verbose:
        detected_info = detect_suspicious_characters(
            text, allowed_characters=allowed_characters
        )
        typer.echo(f"Detected: {detected_info}")

    # If no `--string`, copy back to clipboard
    if string is None:
        if processed_text != text:
            pyperclip.copy(processed_text)
            typer.echo("Processed and copied to clipboard.")
        else:
            typer.echo("No changes!")
    else:
        typer.echo(processed_text)


if __name__ == "__main__":
    app()
