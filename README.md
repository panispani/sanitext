# Sanitext

**Sanitize text from LLMs**

Sanitext is a **command-line tool** and **Python library** for detecting and removing unwanted characters in text. It supports:

- ASCII-only sanitization (default)
- Unicode support (`--allow-unicode`)
- Custom character allowlists (`--allow-chars`, `--allow-file`)
- Interactive review of non-allowed characters (`--interactive`)

## Installation

```bash
pip install sanitext
```

By default, sanitext uses the string in your clipboard unless you specify one with `--string`.

## CLI usage example

```bash
# Process the clipboard string, copy to clipboard, print if unchanged
sanitext
# Detect characters only
sanitext --detect
# Process the provided string and print it
sanitext --string "Héllø, 𝒲𝑜𝓇𝓁𝒹!"
# Process + show detected info
sanitext --verbose
# Allow Unicode characters (use with caution)
sanitext --allow-unicode
# Allow additional characters
sanitext --allow-chars "αøñç"
# Allow characters from a file
sanitext --allow-file allowed_chars.txt
# Prompt user for handling disallowed characters
# y (Yes) -> keep it
# n (No) -> remove it
# r (Replace) -> provide a replacement character
sanitext --interactive
```

## Python library usage example

```python
from sanitext.text_sanitization import (
    sanitize_text,
    detect_suspicious_characters,
    get_allowed_characters,
)

text = "“2×3 – 4 = 5”"

# Detect suspicious characters
suspicious_characters = detect_suspicious_characters(text)
# [('“', 'LEFT DOUBLE QUOTATION MARK'), ('×', 'MULTIPLICATION SIGN'), ('–', 'EN DASH'), ('”', 'RIGHT DOUBLE QUOTATION MARK')]
print(f"Suspicious characters: {suspicious_characters}")

# Sanitize text
sanitized_text = sanitize_text(text)
print(f"Sanitized text: {sanitized_text}")
allowed_characters = get_allowed_characters()
allowed_characters.add("×") # Allow the multiplication sign
sanitized_text = sanitize_text(text, allowed_characters=allowed_characters)
print(f"Sanitized text: {sanitized_text}")
```

## Dev setup

```bash
# Install dependencies
poetry install
# Use it
poetry run python sanitext/cli.py --help
poetry run python sanitext/cli.py --string "your string"
# Run tests
poetry run pytest
poetry run pytest -s tests/test_cli.py
# Run tests over different python versions (TODO: setup github action)
poetry run tox
# Publish to PyPI
poetry build
poetry publish
```
