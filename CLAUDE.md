# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Signal is a terminal-based AI curator designed to help users filter and organize content from various sources. It leverages AI capabilities to analyze, categorize, and rank content based on user preferences, transforming information noise into meaningful signal.

The application uses a terminal user interface (TUI) built with the Textual library, providing a keyboard-driven experience for managing and interacting with curated content. It integrates with OpenAI and Jina AI services for content analysis and extraction, and supports exporting to Obsidian and sharing to social media platforms.

## Common Commands

### Setup and Development

```bash
# Clone and set up development environment
git clone https://github.com/guglielmo/ai-signal.git
cd ai-signal
poetry install

# Enter the virtual environment
poetry shell

# Run the application in development mode
aisignal version
aisignal run
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/aisignal

# Run specific test file
poetry run pytest tests/test_app.py

# Run specific test
poetry run pytest tests/test_app.py::test_notify_user

# Run only core service tests
poetry run pytest tests/test_*_service.py

# Run integration tests
poetry run pytest tests/test_*_integration.py

# Run with verbose async output
poetry run pytest -v --tb=short
```

### Code Quality

```bash
# Format code with Black
poetry run black src/

# Sort imports with isort
poetry run isort src/

# Run linting with Flake8
poetry run flake8 src/

# Run all code quality tools
poetry run black src/ && poetry run isort src/ && poetry run flake8 src/
```

### Building and Packaging

```bash
# Build the package
poetry build

# Install the built package locally
pip install dist/ai_signal-*.whl
```

## Architecture Overview

AI Signal is undergoing migration to a clean core architecture (Week 1-2 of 5-week plan). The architecture separates business logic from UI through interfaces and dependency injection.

### Current Architecture State (Sprint 1-2 Complete)

**Core Layer** (`src/aisignal/core/`):
- `interfaces.py`: ABC definitions for all services (IStorageService, IConfigService, IContentService)
- `models.py`: Domain models (Resource, ParsedItem, etc.)
- `services/`: Service implementations
  - `storage_service.py`: Unified storage (wraps MarkdownSourceStorage + ParsedItemStorage)
  - `config_service.py`: Configuration management
  - `content_service.py`: Content fetching and AI analysis
- `adapters/`: Adapter implementations for external dependencies
  - `storage_adapter.py`, `config_adapter.py`, `content_adapter.py`

**Utilities** (`src/aisignal/utils/`):
- `advanced_service_container.py`: Dependency injection with singleton/transient/scoped lifetimes

**UI Layer** (`src/aisignal/ui/textual/`):
- `app.py`: Main Textual application
- `screens/`: UI screens (main, detail, config, modals)

**Legacy Services** (`src/aisignal/services/`): Being phased out as migration completes

### Dependency Injection Pattern

Services are registered and resolved via the DI container:

```python
from aisignal.utils.advanced_service_container import ServiceContainer
from aisignal.core.interfaces import IStorageService

container = ServiceContainer()
container.register_singleton(IStorageService, StorageService)
storage = container.get(IStorageService)  # Auto-resolves dependencies
```

### Data Flow

1. Configuration loaded via `IConfigService`
2. Content fetched from sources via `IContentService`
3. AI analysis (OpenAI, Jina AI) with token tracking
4. Storage via `IStorageService` (SQLite backend)
5. UI displays via Textual screens
6. Export to Obsidian or social media sharing

## Important Files and Directories

**Core Architecture**:
- `src/aisignal/core/interfaces.py`: Service interface definitions (ABC)
- `src/aisignal/core/models.py`: Domain models and data classes
- `src/aisignal/core/services/`: Service implementations
- `src/aisignal/core/adapters/`: Adapter pattern implementations
- `src/aisignal/utils/advanced_service_container.py`: Dependency injection container

**Application**:
- `src/aisignal/ui/textual/app.py`: Main Textual TUI application
- `src/aisignal/ui/textual/screens/`: UI screens (main, detail, config)
- `src/aisignal/cli.py`: CLI entry point

**Legacy** (being migrated):
- `src/aisignal/services/`: Old service implementations

**Testing**:
- `tests/conftest.py`: Test fixtures and setup
- `tests/mocks.py`: Mock service implementations
- `tests/test_*_service.py`: Service unit tests
- `tests/test_*_integration.py`: Integration tests

## Coding Standards

- Follow PEP 8 style guide
- Use Black with 88 character line limit
- Use type hints for function parameters and return values
- Follow Google-style docstrings
- Use isort for import sorting (profile: "black")
- Maintain test coverage (aim for 80%+)
- All core service interfaces must use ABC (Abstract Base Classes)
- Service implementations should use async/await for I/O operations
- Use `OperationResult` pattern for error handling in core services

## Git Workflow

- Keep commits atomic and focused
- Write clear commit messages following the conventional commit format:
  ```
  feat(component): add new feature X
  
  - Implements functionality Y
  - Fixes issue #123
  ```
- Branch naming: `feature/*`, `hotfix/*`, `release/*`
- Rebase feature branches on `main` before submitting PRs
- Squash commits before merging

## Configuration

AI Signal is configured via a YAML file (`~/.config/aisignal/config.yaml`) with these main sections:
- Content sources and sync interval
- Categories of interest
- AI prompts for content extraction
- Quality thresholds and filters
- API keys for OpenAI and Jina AI
- Integration settings (Obsidian, social media)

## Working with the New Architecture

### Creating New Services

When adding new services to the core layer:

1. Define interface in `core/interfaces.py`:
```python
class IMyService(ABC):
    @abstractmethod
    async def my_operation(self, param: str) -> OperationResult:
        pass
```

2. Implement service in `core/services/`:
```python
class MyService(IMyService):
    def __init__(self, dependency: IOtherService):
        self.dependency = dependency

    async def my_operation(self, param: str) -> OperationResult:
        # Implementation
        pass
```

3. Register in DI container:
```python
container.register_singleton(IMyService, MyService)
```

### Testing with Mocks

The `tests/mocks.py` file contains mock implementations of all services. Use these for testing:

```python
from tests.mocks import MockStorageService

async def test_my_feature():
    mock_storage = MockStorageService()
    # Test with mock
```

### Migration Status

Current migration state (see `docs/multi-ui-migration/01-migration-plan.md`):
- ✅ Week 1: Foundation and interfaces complete
- ✅ Week 2: Storage, Config, and Content services implemented
- 🚧 Week 3: Textual app refactoring (in progress)
- ⏳ Week 4: Event system
- ⏳ Week 5: Multi-user preparation

When working with code, prefer the new core services over legacy implementations in `src/aisignal/services/`.