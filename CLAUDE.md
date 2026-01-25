# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Signal is a terminal-based AI curator designed to help users filter and organize content from various sources. It leverages AI capabilities to analyze, categorize, and rank content based on user preferences, transforming information noise into meaningful signal.

The application uses a terminal user interface (TUI) built with the Textual library, providing a keyboard-driven experience for managing and interacting with curated content. It integrates with OpenAI and Jina AI services for content analysis and extraction, and supports exporting to Obsidian and sharing to social media platforms.

**Current Version:** 0.11.0
**Test Coverage:** 94% (194 passing tests)
**Python:** 3.9-3.12 supported

## Project Status Documentation

**IMPORTANT:** [STATUS.md](STATUS.md) in the project root is the **single source of truth** for:
- Current project status and version
- What's working and what's in development
- Detailed roadmap with phases and priorities
- GitHub issues and milestones alignment
- Technical debt and known issues

**Guidelines for updating project status:**
1. **Always update STATUS.md** when project status changes
2. **Keep it aligned** with GitHub Issues and Milestones
3. **Never duplicate** roadmap or status information in other files
4. **README.md** should only contain a brief status summary that points to STATUS.md
5. **CLAUDE.md** should reference STATUS.md for current priorities, not duplicate content
6. When completing features or milestones, update STATUS.md and close corresponding GitHub issues

**Where status information belongs:**
- ✅ **STATUS.md**: Detailed status, roadmap, phases, what's working, what's in development
- ✅ **GitHub Issues**: Individual tasks and bugs
- ✅ **GitHub Milestones**: Feature groupings and release planning
- ✅ **README.md**: Brief current version and status summary only (points to STATUS.md)
- ❌ **NOT in CLAUDE.md**: No detailed roadmaps or status (reference STATUS.md instead)
- ❌ **NOT in code comments**: No project-level status information

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

AI Signal features a **clean, modular architecture** with strict separation of concerns:
- **Core Layer**: Business logic and domain models (interface-driven, ABC-based)
- **UI Layer**: Textual TUI screens and components
- **Event System**: Pub/sub communication between layers (thread-safe, async)
- **Dependency Injection**: Automated service resolution with lifecycle management

### Layer Structure

**Core Layer** (`src/aisignal/core/`):
- `interfaces.py`: ABC definitions for all services (IStorageService, IConfigService, IContentService, ICoreService, IEventBus, IResourceManager)
- `models.py`: Domain models (Resource, UserContext, OperationResult, BaseEvent and subclasses)
- `services/`: Service implementations
  - `storage_service.py`: Unified storage (SQLite backend)
  - `config_service.py`: Configuration management (YAML config)
  - `content_service.py`: Content fetching and AI analysis (OpenAI, Jina AI)
  - `core_service.py`: Main orchestrator service
  - `event_bus.py`: Event pub/sub system (thread-safe)
  - `resource_manager.py`: Resource collection management
- `adapters/`: External dependency adapters (storage, config, content)

**Utilities** (`src/aisignal/utils/`):
- `advanced_service_container.py`: DI container with singleton/transient/scoped lifetimes

**UI Layer** (`src/aisignal/ui/textual/`):
- `app.py`: Main Textual application (event-driven)
- `screens/`: UI screens (MainScreen, DetailScreen, ConfigScreen, modals)

**Legacy** (`src/aisignal/services/`, `src/aisignal/screens/`): Old implementations, avoid using

### Dependency Injection Pattern

Services are registered and resolved via the DI container:

```python
from aisignal.utils.advanced_service_container import ServiceContainer
from aisignal.core.interfaces import IStorageService

container = ServiceContainer()
container.register_singleton(IStorageService, StorageService)
storage = container.get(IStorageService)  # Auto-resolves dependencies
```

**Lifecycle Types**:
- `singleton`: Single instance shared across app (default for services)
- `transient`: New instance per request
- `scoped`: Single instance per scope (e.g., per-request in web apps)

### Event System Pattern

Subscribe to and publish events via the EventBus:

```python
from aisignal.core.interfaces import IEventBus
from aisignal.core.models import SyncProgressEvent

# Subscribe to events
async def on_sync_progress(event: SyncProgressEvent):
    print(f"Sync: {event.current}/{event.total} - {event.message}")

event_bus = container.get(IEventBus)
event_bus.subscribe(SyncProgressEvent, on_sync_progress)

# Publish events (from Core services)
await event_bus.publish(SyncProgressEvent(
    current=1, total=10, message="Fetching source 1/10"
))
```

**Thread Safety**: EventBus is thread-safe with lock-protected subscriber management. All event handlers run asynchronously via `asyncio.create_task()`.

### Event-Driven Communication

The Event Bus enables decoupled communication between Core and UI layers:

**Event Types** (see `core/models.py`):
- `SyncProgressEvent`: Progress updates during sync operations
- `ResourceUpdatedEvent`: When resources are created/updated/removed
- `SyncCompletedEvent`: When sync operations complete

**Event Flow** (example: sync sources):
```
1. User triggers sync in UI
2. UI calls ICoreService.sync_sources()
3. Core emits SyncProgressEvent(current=0, "Starting...")
4. EventBus notifies all subscribers
5. UI updates progress modal
6. Core creates new resources
7. Core emits ResourceUpdatedEvent for each
8. UI refreshes resource list in real-time
9. Core emits SyncCompletedEvent
10. UI updates status
```

See `docs/architecture/event-bus.md` and `docs/architecture/event-catalog.md` for detailed event documentation.

### Data Flow

1. Configuration loaded via `IConfigService` from `~/.config/aisignal/config.yaml`
2. Content fetched from sources via `IContentService` (Jina AI for HTML, native parsing for feeds)
3. AI analysis via OpenAI with token tracking
4. Storage via `IStorageService` (SQLite backend)
5. UI updates via EventBus (pub/sub pattern)
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

**Legacy** (migration complete, may still contain some old implementations):
- `src/aisignal/services/`: Old service implementations (prefer Core services instead)

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

See `docs/configuration.md` for detailed configuration guide.

## Debugging and Development Tips

### Running with Development Mode

```bash
# Run with Textual console for debugging
poetry run textual console

# In another terminal, run the app
poetry run aisignal run

# See real-time logs in the console window
```

### Common Issues

**Import errors after adding new services:**
- Ensure service is registered in DI container
- Check circular import dependencies
- Use `from __future__ import annotations` for forward references

**Event handlers not firing:**
- Verify subscription happens before event publish
- Check event type matches exactly (not subclass)
- Ensure async handlers are awaited

**Tests failing with "Event loop closed":**
- Use `@pytest.mark.asyncio` decorator
- Don't manually create event loops in tests
- Use fixtures from `conftest.py`

**Database locked errors:**
- Ensure proper async/await usage in storage operations
- Check for concurrent writes without proper locking
- Use `OperationResult` pattern for error handling

## Critical Patterns and Conventions

### OperationResult Pattern

All core service methods return `OperationResult[T]` for consistent error handling:

```python
from aisignal.core.models import OperationResult, OperationStatus

async def get_resource(resource_id: str) -> OperationResult[Resource]:
    if not resource_id:
        return OperationResult(
            status=OperationStatus.INVALID_INPUT,
            message="Resource ID is required"
        )

    resource = await self._storage.get(resource_id)
    if not resource:
        return OperationResult(
            status=OperationStatus.NOT_FOUND,
            message=f"Resource {resource_id} not found"
        )

    return OperationResult(
        status=OperationStatus.SUCCESS,
        data=resource
    )

# Usage
result = await storage.get_resource("abc123")
if result.is_success():
    print(result.data.title)
else:
    print(f"Error: {result.message}")
```

**Available Statuses**: `SUCCESS`, `ERROR`, `NOT_FOUND`, `INVALID_INPUT`, `UNAUTHORIZED`

### Async/Await for I/O

All I/O operations (file, network, database) MUST use async/await:

```python
# Correct
async def fetch_content(url: str) -> OperationResult[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return OperationResult(status=OperationStatus.SUCCESS, data=await response.text())

# Incorrect - blocking I/O
def fetch_content(url: str) -> str:
    return requests.get(url).text  # Blocks event loop!
```

### UserContext for Multi-User Readiness

All operations accept a `UserContext` parameter (currently single-user):

```python
async def sync_sources(self, user_context: UserContext) -> OperationResult:
    # user_context.user_id used for multi-tenant isolation
    resources = await self._storage.get_all_resources(user_context)
```

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
from tests.mocks import MockStorageService, create_test_container

async def test_my_feature():
    mock_storage = MockStorageService()
    # Test with mock

# Or use the pre-configured test container
def test_with_container(container):  # Uses conftest.py fixture
    storage = container.get(IStorageService)  # Auto-injected mock
```

**Test Fixtures** (from `tests/conftest.py`):
- `container`: Pre-configured DI container with all mock services
- `empty_container`: Empty container for custom test setup
- `sample_resource()`, `sample_resources()`: Test data generators

**Test Markers**:
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Slow-running tests

Run specific test categories:
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m integration          # Only integration tests
pytest tests/test_*_service.py # Only service unit tests
```

### Current Development Focus

**✅ Architecture Migration Complete** (January 25, 2026)

The core architecture migration has been successfully completed with excellent quality metrics:
- ✅ Clean core architecture with interface-driven design (ABC-based)
- ✅ Event Bus pub/sub system with real-time UI updates (Issues #25, #26)
- ✅ Dependency injection with automated service resolution
- ✅ 94% test coverage across core services (194 tests passing)
- ✅ Thread-safe concurrent operations with lock protection
- ✅ All core features functional and production-ready

**🎯 Current Priority:** See [STATUS.md](STATUS.md) for the current development focus, roadmap, and what's in development.

**Quick Summary:**
- RSS/Atom feed integration (nearly complete, 88%)
- Focus on cost reduction and performance improvements
- See STATUS.md for detailed roadmap and phases

**Always prefer**:
- New core services (`src/aisignal/core/`) over legacy (`src/aisignal/services/`)
- Interface-based design (ABC) for new components
- Event-driven updates via EventBus
- Async/await for I/O operations
- `OperationResult` pattern for error handling