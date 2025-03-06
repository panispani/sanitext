# Sanitext

Sanitize text from LLMs

```bash
# Install dependencies
poetry install
# Use it
poetry run python sanitext/main.py --help
poetry run python sanitext/main.py --string ok
# Run tests
poetry run pytest
poetry run pytest -s tests/test_main.py
# Run tests over different python versions (TODO: setup github action)
poetry run tox
# Publish to PyPI
poetry build
poetry publish
```
