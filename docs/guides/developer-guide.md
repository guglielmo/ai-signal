# AI Signal - Developer Guide

**Version:** 0.10.0
**Last Updated:** January 25, 2026
**Architecture:** Core Services with Interface-Driven Design

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Working with Core Services](#working-with-core-services)
4. [Dependency Injection](#dependency-injection)
5. [Event System](#event-system)
6. [Creating New Services](#creating-new-services)
7. [Testing Guide](#testing-guide)
8. [Best Practices](#best-practices)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

Welcome to the AI Signal developer guide! This document will help you understand and work with AI Signal's clean core architecture, which features:

- **Interface-driven design** using Python ABC (Abstract Base Classes)
- **Dependency injection** for testability and modularity
- **Event-driven communication** between layers
- **Comprehensive test coverage** (94%, 194 tests)
- **Production-ready code** with strict separation of concerns

### Prerequisites

- Python 3.9-3.12
- Poetry for dependency management
- Understanding of async/await patterns
- Familiarity with ABC and type hints

### Quick Start

```bash
# Clone and setup
git clone https://github.com/guglielmo/ai-signal.git
cd ai-signal
poetry install
poetry shell

# Run tests to verify setup
pytest

# Run the application
aisignal run
```

---

## Architecture Overview

### Layer Structure

AI Signal follows a clean architecture with strict layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer (Textual)                      │
│  - MainScreen, ResourceDetailScreen, ConfigScreen            │
│  - Event subscribers for real-time updates                   │
└─────────────────┬────────────────────────────────────────────┘
                  │ Uses services via DI
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Container (DI)                          │
│  - Manages service lifecycles (singleton/transient/scoped)   │
│  - Auto-resolves dependencies                                │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ICoreService (Orchestrator)                          │  │
│  │  - Coordinates business logic                        │  │
│  │  - Publishes events                                  │  │
│  └──┬───────────────────────────────────────────────┬───┘  │
│     │                                                │       │
│  ┌──▼──────────────┐  ┌───────────────┐  ┌────────▼─────┐ │
│  │ IStorageService │  │  IEventBus    │  │IContentService│ │
│  │ (Persistence)   │  │  (Pub/Sub)    │  │ (AI Analysis) │ │
│  └─────────────────┘  └───────────────┘  └──────────────┘ │
│  ┌──────────────────┐                                       │
│  │ IConfigService   │                                       │
│  │ (Configuration)  │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│  - SQLite database                                           │
│  - OpenAI API (GPT-4o-mini)                                  │
│  - Jina AI Reader API                                        │
│  - File system (config, exports)                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Interface-First**: All core components implement ABC interfaces
2. **Dependency Injection**: Services are injected, never instantiated directly
3. **Event-Driven**: Communication between layers uses pub/sub pattern
4. **Testability**: All services have mock implementations
5. **Async by Default**: All I/O operations use async/await

---

## Working with Core Services

### Available Services

AI Signal provides these core service interfaces:

| Interface | Purpose | Implementation |
|-----------|---------|----------------|
| `ICoreService` | Main orchestrator, coordinates all operations | `CoreService` |
| `IStorageService` | Data persistence (resources, sources, settings) | `StorageService` |
| `IConfigService` | Configuration management | `ConfigService` |
| `IContentService` | Content fetching and AI analysis | `ContentService` |
| `IEventBus` | Pub/sub event system | `EventBus` |
| `IResourceManager` | Resource collection management | `ResourceManager` |

### Getting a Service Instance

**Never instantiate services directly.** Always use the DI container:

```python
from aisignal.utils.advanced_service_container import ServiceContainer
from aisignal.core.interfaces import IStorageService, ICoreService

# Get the container (usually injected into your class)
container = ServiceContainer()

# Get service instances
storage = container.get(IStorageService)
core = container.get(ICoreService)
```

### Using Services

All service methods return `OperationResult[T]` for consistent error handling:

```python
from aisignal.core.interfaces import IStorageService
from aisignal.core.models import UserContext

async def example_service_usage(storage: IStorageService):
    user_context = UserContext(user_id="default")

    # Get all resources
    result = await storage.get_all_resources(user_context)

    if result.is_success():
        resources = result.data
        print(f"Found {len(resources)} resources")
        for resource in resources:
            print(f"- {resource.title}")
    else:
        print(f"Error: {result.message}")
        # Handle error based on status
        if result.status == OperationStatus.NOT_FOUND:
            print("No resources found")
        elif result.status == OperationStatus.ERROR:
            print(f"System error: {result.message}")
```

### OperationResult Pattern

All Core methods return `OperationResult[T]`:

```python
from aisignal.core.models import OperationResult, OperationStatus

# Success case
result = OperationResult(
    status=OperationStatus.SUCCESS,
    data=my_data,
    message="Operation completed successfully"
)

# Error cases
result = OperationResult(
    status=OperationStatus.NOT_FOUND,
    message="Resource not found"
)

result = OperationResult(
    status=OperationStatus.INVALID_INPUT,
    message="Invalid resource ID"
)

# Check results
if result.is_success():
    process(result.data)
else:
    handle_error(result.status, result.message)
```

**Available Statuses:**
- `SUCCESS`: Operation completed successfully
- `ERROR`: General error occurred
- `NOT_FOUND`: Requested resource not found
- `INVALID_INPUT`: Input validation failed
- `UNAUTHORIZED`: User not authorized (future use)

---

## Dependency Injection

### Service Container Basics

The `ServiceContainer` manages all service lifecycles and dependencies:

```python
from aisignal.utils.advanced_service_container import ServiceContainer
from aisignal.core.interfaces import IStorageService, IConfigService
from aisignal.core.services.storage_service import StorageService
from aisignal.core.services.config_service import ConfigService

container = ServiceContainer()

# Register services
container.register_singleton(IStorageService, StorageService)
container.register_singleton(IConfigService, ConfigService)

# Get instances (dependencies auto-resolved)
storage = container.get(IStorageService)
config = container.get(IConfigService)
```

### Lifecycle Types

**Singleton (default):**
```python
# Same instance shared across entire application
container.register_singleton(IStorageService, StorageService)

storage1 = container.get(IStorageService)
storage2 = container.get(IStorageService)
assert storage1 is storage2  # True - same instance
```

**Transient:**
```python
# New instance created each time
container.register_transient(IMyService, MyService)

service1 = container.get(IMyService)
service2 = container.get(IMyService)
assert service1 is not service2  # True - different instances
```

**Scoped:**
```python
# Single instance per scope (e.g., per-request in web apps)
container.register_scoped(IMyService, MyService)

with container.create_scope() as scope:
    service1 = scope.get(IMyService)
    service2 = scope.get(IMyService)
    assert service1 is service2  # True - same within scope

# Different scope = different instance
with container.create_scope() as scope:
    service3 = scope.get(IMyService)
    assert service1 is not service3  # True
```

### Dependency Auto-Resolution

The container automatically resolves constructor dependencies:

```python
class MyService(IMyService):
    def __init__(
        self,
        storage: IStorageService,  # Auto-injected
        config: IConfigService      # Auto-injected
    ):
        self.storage = storage
        self.config = config

# Just register - dependencies resolved automatically
container.register_singleton(IMyService, MyService)
service = container.get(IMyService)  # storage and config auto-injected
```

---

## Event System

### Overview

The EventBus enables decoupled communication between Core and UI layers using pub/sub pattern.

**Key Features:**
- Thread-safe subscriber management
- Async event handlers
- Type-safe event definitions
- No polling required

### Available Events

```python
from aisignal.core.models import (
    SyncProgressEvent,
    ResourceUpdatedEvent,
    SyncCompletedEvent
)
```

| Event | When Published | Data |
|-------|---------------|------|
| `SyncProgressEvent` | During sync operations | `current`, `total`, `message` |
| `ResourceUpdatedEvent` | Resource created/updated/deleted | `resource_id`, `action`, `resource` |
| `SyncCompletedEvent` | Sync operation completes | `success`, `message`, `stats` |

### Subscribing to Events

```python
from aisignal.core.interfaces import IEventBus
from aisignal.core.models import SyncProgressEvent

async def on_sync_progress(event: SyncProgressEvent):
    """Handler for sync progress events."""
    print(f"Progress: {event.current}/{event.total} - {event.message}")

# Subscribe to events
event_bus = container.get(IEventBus)
event_bus.subscribe(SyncProgressEvent, on_sync_progress)
```

### Publishing Events (Core Services Only)

**Note:** Only Core services should publish events, not UI components.

```python
from aisignal.core.interfaces import IEventBus
from aisignal.core.models import SyncProgressEvent

class MyCoreService:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

    async def sync_data(self):
        total = 10
        for i in range(total):
            # Do work
            process_item(i)

            # Publish progress
            await self.event_bus.publish(SyncProgressEvent(
                current=i + 1,
                total=total,
                message=f"Processing item {i+1}/{total}"
            ))
```

### Event Flow Example

Complete example of event-driven sync:

```python
# 1. UI subscribes to events
async def on_progress(event: SyncProgressEvent):
    ui.update_progress_bar(event.current, event.total)

async def on_completed(event: SyncCompletedEvent):
    ui.show_notification(event.message)
    ui.refresh_resource_list()

event_bus.subscribe(SyncProgressEvent, on_progress)
event_bus.subscribe(SyncCompletedEvent, on_completed)

# 2. UI triggers sync
core_service = container.get(ICoreService)
await core_service.sync_sources(user_context)

# 3. Core service publishes events as it works
# 4. UI automatically updates via event handlers
```

### Thread Safety

The EventBus is thread-safe with lock-protected operations:

```python
# Safe to call from any thread
await event_bus.publish(event)  # Thread-safe
event_bus.subscribe(EventType, handler)  # Thread-safe
event_bus.unsubscribe(EventType, handler)  # Thread-safe
```

---

## Creating New Services

### Step 1: Define Interface

Always start with an ABC interface in `src/aisignal/core/interfaces.py`:

```python
from abc import ABC, abstractmethod
from aisignal.core.models import OperationResult

class IMyService(ABC):
    """Interface for my new service."""

    @abstractmethod
    async def my_operation(self, param: str) -> OperationResult[str]:
        """
        Performs my operation.

        Args:
            param: Description of parameter

        Returns:
            OperationResult containing the result string
        """
        pass
```

### Step 2: Implement Service

Create implementation in `src/aisignal/core/services/`:

```python
from aisignal.core.interfaces import IMyService, IOtherService
from aisignal.core.models import OperationResult, OperationStatus

class MyService(IMyService):
    """Implementation of IMyService."""

    def __init__(self, other_service: IOtherService):
        """
        Initialize MyService.

        Args:
            other_service: Dependency injected automatically
        """
        self.other_service = other_service

    async def my_operation(self, param: str) -> OperationResult[str]:
        """Implements my_operation."""
        # Input validation
        if not param:
            return OperationResult(
                status=OperationStatus.INVALID_INPUT,
                message="Parameter is required"
            )

        try:
            # Use dependencies
            other_result = await self.other_service.some_method()

            # Do work (async for I/O)
            result = await self._do_async_work(param)

            # Return success
            return OperationResult(
                status=OperationStatus.SUCCESS,
                data=result,
                message="Operation completed"
            )

        except Exception as e:
            return OperationResult(
                status=OperationStatus.ERROR,
                message=f"Operation failed: {str(e)}"
            )

    async def _do_async_work(self, param: str) -> str:
        """Private helper method."""
        # Implementation
        return f"Processed: {param}"
```

### Step 3: Register Service

Register in your application initialization:

```python
from aisignal.utils.advanced_service_container import ServiceContainer

container = ServiceContainer()
container.register_singleton(IMyService, MyService)
```

### Step 4: Create Tests

Create test file in `tests/test_my_service.py`:

```python
import pytest
from aisignal.core.interfaces import IMyService
from aisignal.core.models import OperationStatus
from tests.mocks import MockOtherService

@pytest.mark.asyncio
async def test_my_operation_success():
    """Test successful operation."""
    # Setup
    mock_other = MockOtherService()
    service = MyService(mock_other)

    # Execute
    result = await service.my_operation("test")

    # Assert
    assert result.is_success()
    assert result.data == "Processed: test"

@pytest.mark.asyncio
async def test_my_operation_invalid_input():
    """Test with invalid input."""
    service = MyService(MockOtherService())

    result = await service.my_operation("")

    assert result.status == OperationStatus.INVALID_INPUT
    assert "required" in result.message.lower()
```

---

## Testing Guide

### Test Structure

AI Signal uses pytest with comprehensive fixtures:

```
tests/
├── conftest.py              # Shared fixtures
├── mocks.py                 # Mock service implementations
├── test_storage_service.py  # Service unit tests
├── test_event_bus.py        # Event system tests
└── test_app.py              # Integration tests
```

### Available Fixtures

From `tests/conftest.py`:

```python
def test_with_container(container):
    """Use pre-configured container with all mocks."""
    storage = container.get(IStorageService)
    # Test with mocked services

def test_with_empty_container(empty_container):
    """Use empty container for custom setup."""
    empty_container.register_singleton(IMyService, MyTestService)

def test_with_sample_data(sample_resource, sample_resources):
    """Use pre-built test data."""
    resource = sample_resource()
    resources = sample_resources(count=5)
```

### Mock Services

Use mocks from `tests/mocks.py`:

```python
from tests.mocks import (
    MockStorageService,
    MockConfigService,
    MockContentService,
    MockEventBus,
    create_test_container
)

async def test_my_feature():
    mock_storage = MockStorageService()
    mock_storage.add_resource(sample_resource())

    # Test with mock
    result = await my_function(mock_storage)
    assert result.is_success()
```

### Writing Async Tests

Always use `@pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operations."""
    service = MyService()
    result = await service.async_method()
    assert result.is_success()
```

### Test Categories

Use markers to categorize tests:

```python
@pytest.mark.integration
async def test_full_sync_flow():
    """Integration test for complete sync."""
    pass

@pytest.mark.slow
async def test_large_dataset():
    """Slow-running test."""
    pass

@pytest.mark.performance
async def test_sync_performance():
    """Performance benchmark test."""
    pass
```

Run specific categories:

```bash
pytest -m "not slow"       # Skip slow tests
pytest -m integration      # Only integration tests
pytest -m performance      # Only performance tests
```

### Coverage

Maintain high test coverage:

```bash
# Run with coverage report
pytest --cov=src/aisignal --cov-report=html

# View coverage
open htmlcov/index.html

# Aim for >80% coverage on new code
```

---

## Best Practices

### 1. Always Use Interfaces

**Good:**
```python
def __init__(self, storage: IStorageService):
    self.storage = storage
```

**Bad:**
```python
def __init__(self, storage: StorageService):  # Concrete class
    self.storage = storage
```

### 2. Use Async/Await for I/O

**Good:**
```python
async def fetch_data(self):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

**Bad:**
```python
def fetch_data(self):
    return requests.get(url).text  # Blocks event loop!
```

### 3. Return OperationResult

**Good:**
```python
async def get_resource(self, id: str) -> OperationResult[Resource]:
    if not id:
        return OperationResult(
            status=OperationStatus.INVALID_INPUT,
            message="ID required"
        )
    # ...
    return OperationResult(status=OperationStatus.SUCCESS, data=resource)
```

**Bad:**
```python
async def get_resource(self, id: str) -> Resource:
    return resource  # No error handling context
```

### 4. Use Type Hints

**Good:**
```python
async def process(
    self,
    data: List[Resource],
    user: UserContext
) -> OperationResult[Dict[str, Any]]:
    pass
```

**Bad:**
```python
async def process(self, data, user):  # No type hints
    pass
```

### 5. Follow UserContext Pattern

**Good:**
```python
async def sync_sources(
    self,
    user_context: UserContext
) -> OperationResult:
    resources = await self.storage.get_all_resources(user_context)
```

**Bad:**
```python
async def sync_sources(self) -> OperationResult:
    resources = await self.storage.get_all_resources()  # No user context
```

### 6. Publish Events from Core Only

**Good:**
```python
# In Core service
await self.event_bus.publish(SyncProgressEvent(...))
```

**Bad:**
```python
# In UI component
await self.event_bus.publish(SyncProgressEvent(...))  # UI shouldn't publish
```

### 7. Use Dependency Injection

**Good:**
```python
class MyScreen:
    def __init__(self, core: ICoreService):
        self.core = core  # Injected
```

**Bad:**
```python
class MyScreen:
    def __init__(self):
        self.core = CoreService()  # Direct instantiation
```

---

## Common Patterns

### Pattern 1: Service Orchestration

When you need to coordinate multiple services:

```python
class MyOrchestratorService(IMyOrchestratorService):
    def __init__(
        self,
        storage: IStorageService,
        content: IContentService,
        event_bus: IEventBus
    ):
        self.storage = storage
        self.content = content
        self.event_bus = event_bus

    async def complex_operation(
        self,
        user_context: UserContext
    ) -> OperationResult:
        # Get data from storage
        resources_result = await self.storage.get_all_resources(user_context)
        if not resources_result.is_success():
            return resources_result

        # Process with content service
        for resource in resources_result.data:
            content_result = await self.content.analyze(resource)
            if content_result.is_success():
                # Update storage
                await self.storage.save_resource(resource, user_context)
                # Notify listeners
                await self.event_bus.publish(
                    ResourceUpdatedEvent(resource_id=resource.id)
                )

        return OperationResult(status=OperationStatus.SUCCESS)
```

### Pattern 2: Progress Tracking

Report progress for long-running operations:

```python
async def sync_sources(
    self,
    user_context: UserContext
) -> OperationResult:
    sources = await self._get_sources(user_context)
    total = len(sources)

    for idx, source in enumerate(sources):
        # Report progress
        await self.event_bus.publish(SyncProgressEvent(
            current=idx + 1,
            total=total,
            message=f"Syncing {source.name}"
        ))

        # Do work
        await self._sync_source(source, user_context)

    # Report completion
    await self.event_bus.publish(SyncCompletedEvent(
        success=True,
        message=f"Synced {total} sources"
    ))

    return OperationResult(status=OperationStatus.SUCCESS)
```

### Pattern 3: Error Handling Chain

Handle errors at appropriate levels:

```python
async def high_level_operation(self) -> OperationResult:
    # Call lower-level service
    result = await self.lower_service.operation()

    # Check result and transform if needed
    if not result.is_success():
        if result.status == OperationStatus.NOT_FOUND:
            # Handle specific error
            return OperationResult(
                status=OperationStatus.ERROR,
                message="Required data not found, cannot proceed"
            )
        else:
            # Propagate error
            return result

    # Continue with successful result
    return self._process_further(result.data)
```

### Pattern 4: Adapter Pattern

Wrap external dependencies:

```python
# Adapter wraps external library
class MyExternalAdapter:
    def __init__(self):
        self.client = ExternalLibrary()

    async def fetch_data(self, url: str) -> OperationResult[str]:
        try:
            data = await self.client.get(url)
            return OperationResult(
                status=OperationStatus.SUCCESS,
                data=data
            )
        except ExternalError as e:
            return OperationResult(
                status=OperationStatus.ERROR,
                message=f"External service error: {e}"
            )

# Service uses adapter
class MyService(IMyService):
    def __init__(self, adapter: MyExternalAdapter):
        self.adapter = adapter

    async def get_content(self, url: str) -> OperationResult[str]:
        return await self.adapter.fetch_data(url)
```

---

## Troubleshooting

### Import Errors After Adding Services

**Problem:** `ImportError` or circular import issues

**Solution:**
1. Use `from __future__ import annotations` at top of file
2. Check circular dependencies between services
3. Ensure service is registered in DI container

```python
from __future__ import annotations  # Enable forward references

from aisignal.core.interfaces import IMyService
```

### Event Handlers Not Firing

**Problem:** Events published but handlers not called

**Solution:**
1. Verify subscription happens before event publish
2. Check event type matches exactly (not subclass)
3. Ensure handler is async if using `await`

```python
# Subscribe BEFORE publishing
event_bus.subscribe(MyEvent, my_handler)

# Then trigger event
await event_bus.publish(MyEvent(...))
```

### Tests Failing with "Event Loop Closed"

**Problem:** `RuntimeError: Event loop is closed`

**Solution:**
1. Use `@pytest.mark.asyncio` decorator
2. Don't manually create event loops
3. Use fixtures from `conftest.py`

```python
@pytest.mark.asyncio  # Required for async tests
async def test_my_async_function():
    result = await my_async_function()
    assert result.is_success()
```

### Database Locked Errors

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:**
1. Ensure proper async/await usage
2. Don't mix sync and async database calls
3. Use `OperationResult` pattern for error handling

```python
# Good - async all the way
async def save_data(self):
    result = await self.storage.save_resource(resource, user_context)
    return result

# Bad - mixing sync and async
def save_data(self):
    result = asyncio.run(self.storage.save_resource(...))  # Don't do this
```

### Service Not Found in Container

**Problem:** `ServiceNotFoundError` when getting service

**Solution:**
1. Ensure service is registered before use
2. Use interface type, not concrete class
3. Check registration happens at startup

```python
# Register services at startup
container.register_singleton(IStorageService, StorageService)
container.register_singleton(IConfigService, ConfigService)

# Use interface type
storage = container.get(IStorageService)  # Correct
storage = container.get(StorageService)   # Wrong - use interface
```

---

## Additional Resources

### Documentation
- [Architecture Documentation](../architecture/) - Detailed architecture docs
- [Event System Guide](../architecture/event-bus.md) - Event system details
- [Event Catalog](../architecture/event-catalog.md) - Available events
- [Project Status](../../STATUS.md) - Current status and roadmap
- [Migration Plan](../archive/migration/01-migration-plan.md) - Architecture evolution

### Code Examples
- `src/aisignal/core/services/` - Service implementations
- `tests/test_*_service.py` - Service unit tests
- `tests/mocks.py` - Mock implementations

### External Links
- [Textual Documentation](https://textual.textualize.io/) - UI framework
- [Poetry Documentation](https://python-poetry.org/) - Dependency management
- [Pytest Documentation](https://docs.pytest.org/) - Testing framework

---

## Getting Help

If you encounter issues:

1. Check this guide and the troubleshooting section
2. Review the test suite for examples
3. Check existing service implementations
4. Open an issue on GitHub with:
   - Clear description of the problem
   - Code example if applicable
   - Error messages and stack traces
   - What you've already tried

---

**Happy coding!** 🚀

The AI Signal development team is committed to maintaining high code quality and developer experience. Follow these patterns and you'll be productive quickly.
