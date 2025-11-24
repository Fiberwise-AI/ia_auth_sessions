# Contributing to ia-auth-sessions

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/fiberwise-ai/ia_auth_sessions.git
cd ia_auth_sessions

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ia_auth_sessions --cov-report=html

# Run specific test file
pytest tests/test_session_manager.py -v
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for public APIs

## Making Changes

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest tests/`
4. Commit: `git commit -m "Description of changes"`
5. Push: `git push origin feature/your-feature`
6. Create a Pull Request

## Publishing a Release

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.

Quick steps:
1. Update version in `pyproject.toml`
2. Test build: `python test_publish.py`
3. Commit and tag: `git tag v0.1.1 && git push --tags`
4. GitHub Actions will automatically publish to PyPI

## Testing the Publishing Workflow

```bash
# Test build locally
python test_publish.py --skip-tests

# Test with all tests
python test_publish.py

# Test publish to TestPyPI (requires TEST_PYPI_TOKEN)
python test_publish.py --test-pypi
```

## Questions?

Open an issue or discussion on GitHub.
