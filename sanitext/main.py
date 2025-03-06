import pyperclip
import typer

from .text_sanitization import detect_unicode_anomalies, normalize_to_standard

app = typer.Typer()

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
    string: str = typer.Option(
        None, "--string", "-s", help="Provide the processed string."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose mode (show detected info)."
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
