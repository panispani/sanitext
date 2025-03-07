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
  - sanitext --allow-unicode   # Allow Unicode characters (use with caution..) TODO does this even work
  - sanitext --allow-chars "αβñç"  # Allow additional characters
  - sanitext --allow-file allowed_chars.txt  # Allow characters from a file
  - sanitext --interactive    # Prompt user for handling disallowed characters
"""

import pyperclip
import typer

from sanitext.text_sanitization import detect_unicode_anomalies, normalize_to_standard

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
        False, "--verbose", "-v", help="Verbose mode (process and show detected info)."
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

    # Detection-only mode
    if detect:
        detected_info = detect_unicode_anomalies(text)
        typer.echo(f"Detected: {detected_info}")
        raise typer.Exit(0)

    processed_text = normalize_to_standard(text)

    if verbose:
        detected_info = detect_unicode_anomalies(text)
        typer.echo(f"Input: {text}")
        typer.echo(f"Detected: {detected_info}")
        typer.echo(f"Output: {processed_text}")

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
