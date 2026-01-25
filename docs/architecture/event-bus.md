# Event Bus Architecture

## Overview

The Event Bus is a core architectural component of AI Signal that enables loose coupling between the Core services layer and the UI layer. It implements the **Publisher-Subscriber (Pub/Sub) pattern** to facilitate asynchronous communication and real-time updates.

## Motivation

### Problem Statement

Before the Event Bus implementation:
- UI layer had to poll Core services for updates
- Tight coupling between UI and Core made testing difficult
- No way to broadcast state changes to multiple UI components
- Progress updates during long-running operations were not possible

### Solution

The Event Bus provides:
- **Loose Coupling**: Core services don't need to know about UI components
- **Real-time Updates**: UI receives immediate notifications of state changes
- **Scalability**: Multiple subscribers can listen to the same events
- **Testability**: Easy to mock and test event flows
- **Progress Tracking**: Long-running operations can emit progress events

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         UI Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MainScreen   │  │ DetailScreen │  │ ConfigScreen │     │
│  │ (Subscriber) │  │ (Subscriber) │  │ (Subscriber) │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ subscribe()
                             │ handle events
┌────────────────────────────┼─────────────────────────────────┐
│                    ┌───────▼────────┐                        │
│                    │   Event Bus    │                        │
│                    │  (Orchestrator)│                        │
│                    └───────▲────────┘                        │
│                            │                                 │
│                            │ publish()                       │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                        Core Layer                            │
│  ┌──────────────┐  ┌──────┴───────┐  ┌──────────────┐      │
│  │CoreService   │  │StorageService│  │ContentService│      │
│  │ (Publisher)  │  │ (Publisher)  │  │ (Publisher)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User triggers action (e.g., "Sync sources")
   │
   ▼
2. UI calls CoreService.sync_sources()
   │
   ▼
3. CoreService executes sync operation
   │
   ├─── Emits: SyncProgressEvent (0%, "Starting...")
   │    │
   │    ├─→ EventBus receives event
   │    │
   │    └─→ EventBus notifies all SyncProgressEvent subscribers
   │         │
   │         └─→ MainScreen._handle_sync_progress() updates modal
   │
   ├─── Emits: SyncProgressEvent (33%, "Fetching 1/3...")
   │    └─→ ... (same flow)
   │
   ├─── Emits: ResourceUpdatedEvent (resource created)
   │    └─→ MainScreen._handle_resource_updated() refreshes list
   │
   └─── Emits: SyncCompletedEvent (success, 5 new items)
        └─→ MainScreen._handle_sync_completed() shows notification
```

## Event Types

All events inherit from `BaseEvent` and include:
- `timestamp`: When the event occurred
- `user_context`: User context for the event (for future multi-user support)

### 1. SyncProgressEvent

**Purpose**: Report progress during sync operations

**Attributes**:
```python
@dataclass
class SyncProgressEvent(BaseEvent):
    current: int = 0           # Current progress value
    total: int = 0             # Total items to process
    message: str = ""          # Human-readable progress message

    @property
    def percentage(self) -> float:  # Computed 0-100 percentage
        return (self.current / self.total) * 100 if self.total > 0 else 0.0
```

**When Emitted**:
- Start of sync operation
- After fetching each source
- During content analysis phase
- Throughout long-running operations

**Example**:
```python
SyncProgressEvent(
    current=2,
    total=5,
    message="Fetching content from https://example.com...",
    user_context=UserContext(user_id="default_user")
)
# percentage = 40.0
```

### 2. ResourceUpdatedEvent

**Purpose**: Notify when a resource is created, updated, or removed

**Attributes**:
```python
@dataclass
class ResourceUpdatedEvent(BaseEvent):
    resource_id: str = ""                  # ID of affected resource
    operation: str = "updated"             # 'created', 'updated', 'removed'
    resource: Optional[Resource] = None    # Full resource object (optional)
```

**When Emitted**:
- After creating a new resource
- After updating resource properties
- After marking a resource as removed

**Example**:
```python
ResourceUpdatedEvent(
    resource_id="abc123",
    operation="created",
    resource=Resource(...),
    user_context=UserContext(user_id="default_user")
)
```

### 3. SyncCompletedEvent

**Purpose**: Report completion of sync operations (success or failure)

**Attributes**:
```python
@dataclass
class SyncCompletedEvent(BaseEvent):
    success: bool = True                    # Whether sync succeeded
    total_resources: int = 0                # Total resources processed
    new_resources: int = 0                  # Number of new resources added
    updated_resources: int = 0              # Number of resources updated
    errors: List[str] = field(default_factory=list)  # Error messages (if any)
    message: str = ""                       # Summary message
```

**When Emitted**:
- At the end of successful sync operation
- When sync fails due to error

**Example**:
```python
# Success
SyncCompletedEvent(
    success=True,
    total_resources=10,
    new_resources=5,
    updated_resources=0,
    errors=[],
    message="Synced 3 sources, found 5 new items",
    user_context=UserContext(user_id="default_user")
)

# Failure
SyncCompletedEvent(
    success=False,
    total_resources=0,
    new_resources=0,
    updated_resources=0,
    errors=["Connection timeout", "Invalid API key"],
    message="Sync failed: Connection timeout",
    user_context=UserContext(user_id="default_user")
)
```

## Implementation Details

### EventBus Class

**Location**: `src/aisignal/core/services/event_bus.py`

**Thread Safety**: Uses `threading.Lock()` to ensure thread-safe access to subscriber list

**Key Methods**:

#### `subscribe(event_type, handler)`
```python
def subscribe(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]) -> None:
    """
    Subscribe to a specific event type.

    Args:
        event_type: The type of event to subscribe to
        handler: Callback function to handle the event
    """
```

**Usage**:
```python
def my_handler(event: SyncProgressEvent):
    print(f"Progress: {event.percentage}%")

event_bus.subscribe(SyncProgressEvent, my_handler)
```

#### `unsubscribe(event_type, handler)`
```python
def unsubscribe(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]) -> None:
    """
    Unsubscribe from a specific event type.

    Args:
        event_type: The type of event to unsubscribe from
        handler: The callback function to remove
    """
```

**Usage**:
```python
event_bus.unsubscribe(SyncProgressEvent, my_handler)
```

#### `publish(event)`
```python
def publish(self, event: BaseEvent) -> None:
    """
    Publish an event to all subscribers synchronously.

    Args:
        event: The event instance to publish
    """
```

**Usage**:
```python
event_bus.publish(SyncProgressEvent(current=1, total=5, message="Processing..."))
```

#### `publish_async(event)`
```python
async def publish_async(self, event: BaseEvent) -> None:
    """
    Publish an event to all subscribers asynchronously.
    Supports both sync and async handlers.

    Args:
        event: The event instance to publish
    """
```

**Usage**:
```python
await event_bus.publish_async(SyncProgressEvent(current=1, total=5, message="Processing..."))
```

### Error Handling

The EventBus implements **graceful error handling**:

```python
for handler in handlers:
    try:
        handler(event)
    except Exception as e:
        logger.error(f"Error in handler {handler.__name__}: {e}", exc_info=True)
        # Continue processing other handlers
```

**Key Points**:
- One failing handler doesn't break others
- Errors are logged with full stack trace
- Publishing continues even if some handlers fail

## Integration Guide

### For Core Services (Publishers)

1. **Inject EventBus** (optional dependency):
```python
class CoreService:
    def __init__(
        self,
        storage_service: IStorageService,
        config_manager: IConfigManager,
        content_service: IContentService,
        event_bus: Optional[IEventBus] = None,  # Optional!
    ):
        self.event_bus = event_bus
```

2. **Emit events** at key points:
```python
async def sync_sources(self, user_context: UserContext):
    if self.event_bus:
        self.event_bus.publish(SyncProgressEvent(
            user_context=user_context,
            current=0,
            total=5,
            message="Starting sync..."
        ))

    # ... perform sync ...

    if self.event_bus:
        self.event_bus.publish(SyncCompletedEvent(
            user_context=user_context,
            success=True,
            new_resources=3,
            message="Sync completed!"
        ))
```

### For UI Components (Subscribers)

1. **Subscribe in `on_mount()`**:
```python
def on_mount(self) -> None:
    if hasattr(self.app, "event_bus") and self.app.event_bus:
        self.app.event_bus.subscribe(SyncProgressEvent, self._handle_sync_progress)
        self.app.event_bus.subscribe(ResourceUpdatedEvent, self._handle_resource_updated)
        self.app.event_bus.subscribe(SyncCompletedEvent, self._handle_sync_completed)
```

2. **Implement event handlers**:
```python
def _handle_sync_progress(self, event: SyncProgressEvent) -> None:
    """Handle sync progress updates"""
    if self._sync_modal:
        self._sync_modal.update_progress(
            event.current,
            event.total,
            event.message
        )

def _handle_resource_updated(self, event: ResourceUpdatedEvent) -> None:
    """Handle resource updates"""
    # Refresh UI asynchronously to avoid blocking
    self.call_later(self.update_resource_list)

def _handle_sync_completed(self, event: SyncCompletedEvent) -> None:
    """Handle sync completion"""
    if event.success:
        self.notify(f"✅ {event.message}")
    else:
        self.notify(f"❌ Sync failed: {event.message}", severity="error")
```

3. **Unsubscribe in `on_unmount()`** to prevent memory leaks:
```python
def on_unmount(self) -> None:
    if hasattr(self.app, "event_bus") and self.app.event_bus:
        self.app.event_bus.unsubscribe(SyncProgressEvent, self._handle_sync_progress)
        self.app.event_bus.unsubscribe(ResourceUpdatedEvent, self._handle_resource_updated)
        self.app.event_bus.unsubscribe(SyncCompletedEvent, self._handle_sync_completed)
```

## Testing

### Unit Testing EventBus

```python
from aisignal.core.services.event_bus import EventBus
from aisignal.core.models import SyncProgressEvent

def test_publish_and_subscribe():
    event_bus = EventBus()
    received_events = []

    def handler(event):
        received_events.append(event)

    event_bus.subscribe(SyncProgressEvent, handler)
    event_bus.publish(SyncProgressEvent(current=1, total=5))

    assert len(received_events) == 1
    assert received_events[0].current == 1
```

### Integration Testing with Services

```python
from tests.mocks import MockEventBus

async def test_sync_emits_events():
    event_bus = MockEventBus()
    core_service = CoreService(
        storage_service=storage,
        config_manager=config,
        content_service=content,
        event_bus=event_bus
    )

    await core_service.sync_sources(user_context)

    # Check that progress events were emitted
    progress_events = event_bus.get_events_of_type(SyncProgressEvent)
    assert len(progress_events) > 0

    # Check that completion event was emitted
    completed_events = event_bus.get_events_of_type(SyncCompletedEvent)
    assert len(completed_events) == 1
    assert completed_events[0].success
```

### MockEventBus for Testing

The test suite includes `MockEventBus` for easy testing:

```python
class MockEventBus(IEventBus):
    def __init__(self):
        self.published_events = []

    def publish(self, event: BaseEvent):
        self.published_events.append(event)

    def get_events_of_type(self, event_type: Type[BaseEvent]) -> List[BaseEvent]:
        return [e for e in self.published_events if isinstance(e, event_type)]
```

## Performance Considerations

### Current Implementation

- **Time Complexity**: O(n) where n = number of subscribers for an event type
- **Space Complexity**: O(m) where m = total number of subscriptions
- **Thread Safety**: Synchronized using `threading.Lock()`
- **Handler Execution**: Synchronous by default, async supported via `publish_async()`

### Optimization Opportunities

1. **Event Batching**: Group multiple events and publish together
2. **Priority Queues**: Process critical events first
3. **Event Filtering**: Add predicate-based filtering to reduce handler calls
4. **Weak References**: Use weak references for subscribers to avoid memory leaks

### Current Limitations

- No built-in rate limiting
- No event replay/history mechanism
- No event persistence
- Handlers execute sequentially (not parallel)

## Future Enhancements

### Planned Features

1. **Event Replay**: Store event history for debugging
2. **Event Metrics**: Track event counts, timing, and errors
3. **Rate Limiting**: Prevent event flooding
4. **Event Middleware**: Add pre/post-processing hooks
5. **Dead Letter Queue**: Handle failed events
6. **Event Serialization**: Support for remote event buses

### Migration Path for Multi-User

The current event system is designed with multi-user support in mind:

```python
# All events include user_context
@dataclass
class BaseEvent:
    timestamp: datetime = field(default_factory=datetime.now)
    user_context: Optional[UserContext] = None  # Ready for multi-user!
```

When multi-user support is implemented:
1. Events will be filtered by `user_context`
2. UI will only receive events for the current user
3. EventBus may route events to user-specific channels

## Best Practices

### ✅ Do's

1. **Always unsubscribe** in `on_unmount()` to prevent memory leaks
2. **Use specific event types** instead of a generic "DataChanged" event
3. **Keep handlers fast** - offload heavy work to background tasks
4. **Check for EventBus presence** before emitting (it's optional)
5. **Include context** in events (user_context, timestamps, etc.)
6. **Log errors** in handlers for debugging

### ❌ Don'ts

1. **Don't block** in event handlers - use `call_later()` for UI updates
2. **Don't create** circular event chains (A→B→A)
3. **Don't store** event references long-term (can cause memory leaks)
4. **Don't assume** event order (events may arrive out of order)
5. **Don't emit** events in tight loops (can cause performance issues)

## Troubleshooting

### Events Not Received

**Symptom**: Handler not called when event is published

**Possible Causes**:
1. Handler not subscribed: Check `on_mount()` is called
2. Wrong event type: Verify event type matches subscription
3. EventBus not injected: Check DI container configuration
4. Unsubscribed too early: Verify `on_unmount()` timing

**Solution**:
```python
# Add debug logging
def _handle_sync_progress(self, event: SyncProgressEvent):
    logger.debug(f"Received progress event: {event}")
    # ... rest of handler
```

### Memory Leaks

**Symptom**: Memory usage grows over time

**Possible Causes**:
1. Missing `on_unmount()` cleanup
2. Lambda functions prevent garbage collection
3. Event handlers hold strong references

**Solution**:
```python
# Always cleanup in on_unmount
def on_unmount(self):
    if hasattr(self.app, "event_bus") and self.app.event_bus:
        # Unsubscribe from ALL events
        self.app.event_bus.unsubscribe(EventType, self.handler)
```

### Handler Errors

**Symptom**: Some handlers fail silently

**Cause**: EventBus catches all exceptions to prevent cascading failures

**Solution**: Check logs for error messages:
```
ERROR - Error in event handler _handle_sync_progress for SyncProgressEvent: ...
```

## References

- **Implementation**: `src/aisignal/core/services/event_bus.py`
- **Interfaces**: `src/aisignal/core/interfaces.py` (IEventBus)
- **Event Models**: `src/aisignal/core/models.py` (BaseEvent, SyncProgressEvent, etc.)
- **UI Integration**: `src/aisignal/ui/textual/screens/main.py`
- **Tests**: `tests/test_event_bus.py`, `tests/test_core_service_events.py`

## See Also

- [Core Services Architecture](./core-services.md)
- [Multi-UI Migration Plan](../multi-ui-migration/01-migration-plan.md)
- [Testing Guide](../CONTRIBUTING.md#testing)
