# Contributing to [Project Name]

## Getting Started

1. Fork the repository
2. Create a new feature branch from `main`:
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
- Write clear commit messages:
  ```
  feat(component): add new feature X
  
  - Implements functionality Y
  - Fixes issue #123
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
- [ ] Code follows style guide

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
project_name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── core/
│       ├── utils/
│       └── config/
├── tests/
├── docs/
└── setup.py
```

### Code Quality Tools

- Black for formatting
- isort for import sorting
- Flake8 for linting
- Mypy for type checking
- Bandit for security checks

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

## Questions?

Open an issue or contact the maintainers for help.