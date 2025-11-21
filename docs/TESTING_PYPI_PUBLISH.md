# Testing PyPI Publishing Workflow

Quick guide to test the PyPI publishing process locally before creating a release.

## Prerequisites

```bash
# Install build tools
python -m pip install build twine
```

## Quick Test (Recommended)

Use the included `test_publish.py` script:

```bash
# Navigate to ia-auth-sessions directory
cd ia_auth_sessions

# Test build without running tests (fast)
python test_publish.py --skip-tests

# Test build with tests (recommended before release)
python test_publish.py
```

## Expected Output

```
🚀 ia-auth-sessions - PyPI Publishing Test
============================================================

🧹 Cleaning previous build artifacts...
   Removed: dist
   Removed: build

📦 Installing build dependencies...
   ✓ pip, build, twine installed

🏗️  Building package...
   ✓ Created source distribution (tar.gz)
   ✓ Created wheel (.whl)

📦 Built artifacts:
   ia_auth_sessions-0.1.0-py3-none-any.whl (XX.X KB)
   ia_auth_sessions-0.1.0.tar.gz (XX.X KB)

🔍 Checking package with twine...
   Checking dist/ia_auth_sessions-0.1.0-py3-none-any.whl: PASSED
   Checking dist/ia_auth_sessions-0.1.0.tar.gz: PASSED

✅ Package build and check complete!
```

## Test Options

### Skip Tests (Fast Build)
```bash
python test_publish.py --skip-tests
```
Use when you just want to verify the build works.

### Full Test (With Tests)
```bash
python test_publish.py
```
Runs tests before building (recommended before actual release).

### Test Publish to TestPyPI
```bash
# Set your TestPyPI token
export TEST_PYPI_TOKEN="pypi-AgE..."

# Run with publish flag
python test_publish.py --test-pypi
```

### Keep Previous Build
```bash
python test_publish.py --no-clean
```
Skip cleaning previous build artifacts.

## Manual Testing Steps

If you prefer manual steps:

```bash
# 1. Clean previous builds
rm -rf dist build *.egg-info

# 2. Build the package
python -m build

# 3. Check the package
python -m twine check dist/*

# Should output:
# Checking dist/ia_auth_sessions-0.1.0-py3-none-any.whl: PASSED
# Checking dist/ia_auth_sessions-0.1.0.tar.gz: PASSED
```

## PowerShell (Windows)

```powershell
# Clean previous builds
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build
python -m build

# Check
python -m twine check dist/*
```

## Inspect Built Package

```bash
# List contents of wheel
python -m zipfile -l dist/ia_auth_sessions-0.1.0-py3-none-any.whl

# Extract and inspect
python -m zipfile -e dist/ia_auth_sessions-0.1.0-py3-none-any.whl temp_extract
```

## Test Installation Locally

```bash
# Install from local wheel
pip install dist/ia_auth_sessions-0.1.0-py3-none-any.whl

# Verify
python -c "import ia_auth_sessions; print('Successfully imported')"

# Uninstall
pip uninstall ia-auth-sessions
```

## Common Issues

### Tests fail
```bash
# Run tests separately to debug
pytest tests/ -v

# Skip tests for quick build check
python test_publish.py --skip-tests
```

### Missing dependencies
```bash
# Install with dev dependencies
pip install -e ".[dev]"
```

### Build warnings
Most warnings are informational. Critical errors will prevent the build.

## Next Steps After Successful Test

1. ✅ Verify build passes locally
2. Update version in `pyproject.toml`
3. Commit changes
4. Create release or push tag (GitHub Actions will publish)

See [PUBLISHING.md](../PUBLISHING.md) for full publishing instructions.
