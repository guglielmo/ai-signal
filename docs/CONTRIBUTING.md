# Contributing to AI Signal

AI Signal is a terminal-based AI curator that turns information noise into meaningful signal. We welcome contributions that help improve content filtering, UI experience, AI integration, and new features.

## Getting Started

1. Fork the repository
2. Set up your development environment:
   ```bash
   # Clone the repository
   git clone https://github.com/YOUR-USERNAME/ai-signal.git
   cd ai-signal

   # Install dependencies
   poetry install

   # Activate virtual environment
   poetry shell
   ```
3. Create a new feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Git Workflow

### Branches

- `main`: Protected branch, only accepts merge requests
- `feature/*`: New features and non-emergency bug fixes
- `hotfix/*`: Emergency bug fixes
- `release/*`: Release preparation

### Best Practices

- Keep commits atomic and focused
- Write clear commit messages following the conventional commit format:
  ```
  feat(ui): add configuration screen

  - Implements TUI-based configuration panel accessible via 'c' key
  - Adds form fields for API keys, sources, and categories
  - Fixes issue #42
  ```
- Rebase your branch on `main` before submitting merge request
- Squash commits before merging

## Merge Requests

1. Update your feature branch with main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Run tests locally
3. Push your branch and create a merge request
4. Fill out the merge request template
5. Request review from maintainers

### Merge Request Checklist

- [ ] Branch is up to date with `main`
- [ ] Commits are squashed and well-documented
- [ ] Tests are passing
- [ ] Documentation is updated
- [ ] Code follows style guide (Black, isort, Flake8)
- [ ] Type hints are used consistently
- [ ] TUI components follow Textual best practices
- [ ] Configuration changes are backward compatible
- [ ] Token usage is tracked properly (if using AI services)

## Python Coding Standards

### Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black formatter default)
- Use Black for code formatting
- Use isort for import sorting

### Naming Conventions

```python
# Variables and functions: lowercase with underscores
user_count = 0
def calculate_total():
    pass

# Classes: CamelCase
class UserAccount:
    pass

# Constants: uppercase with underscores
MAX_CONNECTIONS = 100
```

### Project Structure
```
ai-signal/
├── src/
│   └── aisignal/
│       ├── __init__.py
│       ├── app.py
│       ├── cli.py
│       ├── core/
│       │   ├── config.py
│       │   ├── config_schema.py
│       │   ├── export.py
│       │   ├── filters.py
│       │   ├── models.py
│       │   ├── resource_manager.py
│       │   ├── sync_exceptions.py
│       │   ├── sync_status.py
│       │   └── token_tracker.py
│       ├── screens/
│       │   ├── base.py
│       │   ├── config.py
│       │   ├── main.py
│       │   ├── modals/
│       │   └── resource/
│       ├── services/
│       │   ├── content.py
│       │   └── storage.py
│       └── styles/
│           └── app.tcss
├── tests/
├── docs/
└── pyproject.toml
```

### Code Quality Tools

- Black for formatting (line length 88)
- isort for import sorting (profile=black)
- Flake8 for linting
- pytest for testing
- pre-commit for git hooks

### Documentation

- Use Google-style docstrings
```python
def process_data(input_data: dict) -> list:
    """Process the input data and return results.

    Args:
        input_data: Dictionary containing raw data.

    Returns:
        List of processed items.

    Raises:
        ValueError: If input_data is empty.
    """
```

## Testing

### pytest Framework

- Use pytest for all tests
- Keep test files in `tests/` directory
- Name test files with `test_` prefix
- Use fixtures for test setup
- Aim for 80%+ coverage
- Use pytest-cov to check coverage

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src/aisignal

# Run specific test file
poetry run pytest tests/test_app.py

# Run specific test
poetry run pytest tests/test_app.py::test_notify_user
```

### Example Test Structure
```python
def test_feature():
    # Arrange
    expected = ...

    # Act
    result = feature()

    # Assert
    assert result == expected
```

### Testing UI Components

For testing Textual UI components:

```python
from textual.pilot import Pilot

async def test_ui_component(pilot: Pilot):
    # Navigate UI
    await pilot.press("c")  # Open config

    # Assert UI state
    assert pilot.app.query_one("#config_panel").visible

    # Interact with form
    await pilot.click("#save_button")
```

## Release Process

### Versioning

AI Signal follows [Semantic Versioning](https://semver.org/) (SemVer) for version numbers:
- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality additions
- **PATCH** version for backward-compatible bug fixes

### Bumping the Version

The project uses Poetry for dependency and package management. To bump the version:

1. Update the version in `pyproject.toml`:
   ```bash
   # For patch version (0.7.2 -> 0.7.3)
   poetry version patch

   # For minor version (0.7.2 -> 0.8.0)
   poetry version minor

   # For major version (0.7.2 -> 1.0.0)
   poetry version major
   ```

2. Build the package to verify everything works:
   ```bash
   poetry build
   ```

### Creating a GitHub Release

1. Commit the version change:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to $(poetry version -s)"
   ```

2. Create a git tag for the new version:
   ```bash
   git tag v$(poetry version -s)
   ```

3. Push the changes and tag to GitHub:
   ```bash
   git push origin main
   git push origin v$(poetry version -s)
   ```

4. Create a new release on GitHub:
   - Go to the [GitHub repository](https://github.com/guglielmo/ai-signal/releases)
   - Click "Draft a new release"
   - Select the tag you just pushed
   - Add a title (usually "v[VERSION]")
   - Add release notes describing the changes
   - Attach the built distribution files from the `dist/` directory
   - Publish the release

### Release Checklist

- [ ] Update version in pyproject.toml
- [ ] Update CHANGELOG.md (if applicable)
- [ ] Update documentation for new features
- [ ] Build and test the package locally
- [ ] Commit changes and create a git tag
- [ ] Push changes and tag to GitHub
- [ ] Create a GitHub release
- [ ] Verify the package is installable from PyPI (if published)

## Questions?

- Open an issue in the [GitHub repository](https://github.com/guglielmo/ai-signal/issues)
- Contact the project maintainer: Guglielmo Celata ([@guglielmo](https://github.com/guglielmo))
- Join the discussion on Mastodon: [@guille@mastodon.uno](https://mastodon.uno/@guille)
