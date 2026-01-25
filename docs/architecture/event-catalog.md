# Event Catalog

This document provides a comprehensive catalog of all events in the AI Signal event system, including when they're emitted, what data they contain, and recommended handling strategies.

## Quick Reference

| Event Type | Category | Frequency | Priority |
|------------|----------|-----------|----------|
| [SyncProgressEvent](#syncprogressevent) | Progress | High (multiple per sync) | Medium |
| [ResourceUpdatedEvent](#resourceupdatedevent) | Data Change | Medium (per resource) | High |
| [SyncCompletedEvent](#synccompletedevent) | Completion | Low (once per sync) | High |

---

## Event Lifecycle

### Typical Sync Operation Flow

```
1. sync_sources() called
   │
   ├─→ SyncProgressEvent (current=0, "Starting sync...")
   │
   ├─→ SyncProgressEvent (current=1, "Fetching source 1/3...")
   │
   ├─→ SyncProgressEvent (current=2, "Fetching source 2/3...")
   │
   ├─→ SyncProgressEvent (current=3, "Fetching source 3/3...")
   │
   ├─→ SyncProgressEvent (current=3, "Analyzing content...")
   │
   ├─→ ResourceUpdatedEvent (operation="created", resource_id="abc123")
   ├─→ ResourceUpdatedEvent (operation="created", resource_id="def456")
   ├─→ ResourceUpdatedEvent (operation="created", resource_id="ghi789")
   │
   └─→ SyncCompletedEvent (success=True, new_resources=3)
```

### Typical Resource Update Flow

```
update_resource() called
   │
   └─→ ResourceUpdatedEvent (operation="updated", resource_id="abc123")
```

### Typical Resource Removal Flow

```
remove_resource() called
   │
   └─→ ResourceUpdatedEvent (operation="removed", resource_id="abc123")
```

---

## Event Details

### SyncProgressEvent

**Category**: Progress Tracking
**Source**: CoreService.sync_sources()
**Frequency**: Multiple times per sync operation
**Typical Count**: 5-20 events per sync

#### Purpose
Reports real-time progress during content synchronization operations, allowing UI to display progress bars, spinners, or status messages.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current` | int | ✅ | Current progress value (e.g., sources processed) |
| `total` | int | ✅ | Total items to process |
| `message` | str | ✅ | Human-readable progress message |
| `percentage` | float | ✅ | Computed property: `(current/total) * 100` |
| `timestamp` | datetime | ✅ | When event was created (from BaseEvent) |
| `user_context` | UserContext | ❌ | User context (from BaseEvent) |

#### Example Payloads

**Start of Sync**:
```python
SyncProgressEvent(
    current=0,
    total=3,
    message="Starting sync...",
    timestamp=datetime(2026, 1, 25, 10, 30, 0),
    user_context=UserContext(user_id="default_user")
)
# percentage = 0.0
```

**Fetching Source**:
```python
SyncProgressEvent(
    current=1,
    total=3,
    message="Fetching content from https://example.com/feed...",
    timestamp=datetime(2026, 1, 25, 10, 30, 5),
    user_context=UserContext(user_id="default_user")
)
# percentage = 33.33
```

**Analyzing Content**:
```python
SyncProgressEvent(
    current=3,
    total=3,
    message="Analyzing content with AI...",
    timestamp=datetime(2026, 1, 25, 10, 30, 15),
    user_context=UserContext(user_id="default_user")
)
# percentage = 100.0
```

#### When Emitted

| Trigger Point | current | total | message | Code Location |
|---------------|---------|-------|---------|---------------|
| Sync starts | 0 | num_sources | "Starting sync..." | core_service.py:244-252 |
| Source fetched | source_idx | num_sources | "Fetching content from {url}..." | core_service.py:258-266 |
| Analysis begins | num_sources | num_sources | "Analyzing content with AI..." | core_service.py:287-295 |

#### Recommended Handlers

**Progress Bar Update**:
```python
def _handle_sync_progress(self, event: SyncProgressEvent) -> None:
    """Update progress bar with current sync progress"""
    if self._progress_bar:
        self._progress_bar.update(
            total=event.total,
            completed=event.current
        )
        self._status_label.update(event.message)
```

**Spinner with Message**:
```python
def _handle_sync_progress(self, event: SyncProgressEvent) -> None:
    """Show spinner with progress message"""
    if event.current < event.total:
        self._spinner.show()
    self._status.update(f"{event.message} ({event.percentage:.0f}%)")
```

**Console Logging**:
```python
def _handle_sync_progress(self, event: SyncProgressEvent) -> None:
    """Log progress to console"""
    logger.info(f"[{event.current}/{event.total}] {event.message}")
```

---

### ResourceUpdatedEvent

**Category**: Data Change Notification
**Source**: CoreService (sync_sources, update_resource, remove_resource)
**Frequency**: Once per resource modification
**Typical Count**: 1-100 events per sync (depends on new content)

#### Purpose
Notifies subscribers when a resource is created, updated, or removed, allowing UI to refresh displays and maintain consistency.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resource_id` | str | ✅ | Unique identifier of the affected resource |
| `operation` | str | ✅ | Type of operation: "created", "updated", or "removed" |
| `resource` | Resource | ❌ | Full resource object (optional, provided for creates) |
| `timestamp` | datetime | ✅ | When event was created (from BaseEvent) |
| `user_context` | UserContext | ❌ | User context (from BaseEvent) |

#### Example Payloads

**Resource Created**:
```python
ResourceUpdatedEvent(
    resource_id="abc123",
    operation="created",
    resource=Resource(
        id="abc123",
        user_id="default_user",
        title="New Article",
        url="https://example.com/article",
        categories=["Tech"],
        ranking=85.0,
        summary="...",
        full_content="...",
        datetime=datetime.now(),
        source="https://example.com"
    ),
    timestamp=datetime(2026, 1, 25, 10, 30, 20),
    user_context=UserContext(user_id="default_user")
)
```

**Resource Updated**:
```python
ResourceUpdatedEvent(
    resource_id="abc123",
    operation="updated",
    resource=None,  # Not always included for updates
    timestamp=datetime(2026, 1, 25, 10, 35, 0),
    user_context=UserContext(user_id="default_user")
)
```

**Resource Removed**:
```python
ResourceUpdatedEvent(
    resource_id="abc123",
    operation="removed",
    resource=None,
    timestamp=datetime(2026, 1, 25, 10, 40, 0),
    user_context=UserContext(user_id="default_user")
)
```

#### When Emitted

| Trigger Point | operation | resource included? | Code Location |
|---------------|-----------|-------------------|---------------|
| Resource created during sync | "created" | ✅ Yes | core_service.py:333-342 |
| Resource updated via API | "updated" | ❌ No | core_service.py:149-157 |
| Resource removed | "removed" | ❌ No | core_service.py:183-191 |

#### Recommended Handlers

**Refresh Resource List**:
```python
def _handle_resource_updated(self, event: ResourceUpdatedEvent) -> None:
    """Refresh the resource list when any resource changes"""
    # Use call_later to avoid blocking the event loop
    self.call_later(self.update_resource_list)
```

**Update Single Row (Optimized)**:
```python
def _handle_resource_updated(self, event: ResourceUpdatedEvent) -> None:
    """Update only the affected resource in the table"""
    table = self.query_one(DataTable)

    if event.operation == "created" and event.resource:
        # Add new row
        table.add_row(
            event.resource.title,
            event.resource.ranking,
            event.resource.source,
            key=event.resource_id
        )
    elif event.operation == "updated":
        # Refresh specific row
        row_key = RowKey(event.resource_id)
        if table.is_valid_row_index(row_key):
            resource = await self.core_service.get_resource(
                self.user_context,
                event.resource_id
            )
            table.update_cell(row_key, "title", resource.title)
    elif event.operation == "removed":
        # Remove row
        row_key = RowKey(event.resource_id)
        if table.is_valid_row_index(row_key):
            table.remove_row(row_key)
```

**Show Notification**:
```python
def _handle_resource_updated(self, event: ResourceUpdatedEvent) -> None:
    """Show toast notification for resource changes"""
    if event.operation == "created":
        self.notify(f"✅ New resource added", timeout=2)
    elif event.operation == "updated":
        self.notify(f"📝 Resource updated", timeout=1)
    elif event.operation == "removed":
        self.notify(f"🗑️ Resource removed", timeout=2)
```

---

### SyncCompletedEvent

**Category**: Completion Notification
**Source**: CoreService.sync_sources()
**Frequency**: Once per sync operation
**Typical Count**: 1 event per sync

#### Purpose
Signals the end of a sync operation (success or failure), providing summary statistics and allowing UI to update status, hide progress indicators, and show notifications.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | bool | ✅ | Whether sync completed successfully |
| `total_resources` | int | ✅ | Total number of resources processed |
| `new_resources` | int | ✅ | Number of new resources added |
| `updated_resources` | int | ✅ | Number of resources updated |
| `errors` | List[str] | ✅ | List of error messages (empty if no errors) |
| `message` | str | ✅ | Human-readable summary message |
| `timestamp` | datetime | ✅ | When event was created (from BaseEvent) |
| `user_context` | UserContext | ❌ | User context (from BaseEvent) |

#### Example Payloads

**Successful Sync**:
```python
SyncCompletedEvent(
    success=True,
    total_resources=10,
    new_resources=5,
    updated_resources=0,
    errors=[],
    message="Synced 3 sources, found 5 new items",
    timestamp=datetime(2026, 1, 25, 10, 30, 30),
    user_context=UserContext(user_id="default_user")
)
```

**Failed Sync**:
```python
SyncCompletedEvent(
    success=False,
    total_resources=0,
    new_resources=0,
    updated_resources=0,
    errors=[
        "Failed to fetch https://example.com: Connection timeout",
        "Failed to fetch https://test.com: Invalid API key"
    ],
    message="Sync failed: Connection timeout",
    timestamp=datetime(2026, 1, 25, 10, 30, 30),
    user_context=UserContext(user_id="default_user")
)
```

**Partial Success**:
```python
SyncCompletedEvent(
    success=True,
    total_resources=8,
    new_resources=8,
    updated_resources=0,
    errors=[
        "Failed to fetch https://broken-feed.com: 404 Not Found"
    ],
    message="Synced 2/3 sources, found 8 new items",
    timestamp=datetime(2026, 1, 25, 10, 30, 30),
    user_context=UserContext(user_id="default_user")
)
```

#### When Emitted

| Trigger Point | success | Code Location |
|---------------|---------|---------------|
| Sync completes successfully | ✅ True | core_service.py:347-359 |
| Sync fails with exception | ❌ False | core_service.py:371-385 |

#### Recommended Handlers

**Hide Progress Modal**:
```python
def _handle_sync_completed(self, event: SyncCompletedEvent) -> None:
    """Hide progress modal and show completion notification"""
    # Dismiss modal
    if self._sync_modal:
        self.app.pop_screen()
        self._sync_modal = None

    # Show notification
    if event.success:
        self.notify(f"✅ {event.message}", timeout=3)
    else:
        self.notify(f"❌ {event.message}", severity="error", timeout=5)

    # Refresh resource list
    self.call_later(self.update_resource_list)
```

**Update Statistics Display**:
```python
def _handle_sync_completed(self, event: SyncCompletedEvent) -> None:
    """Update sync statistics in UI"""
    if event.success:
        self.stats_widget.update(
            total_resources=event.total_resources,
            new_resources=event.new_resources,
            last_sync=event.timestamp
        )
    else:
        self.stats_widget.update_status("Sync Failed", severity="error")
```

**Log Results**:
```python
def _handle_sync_completed(self, event: SyncCompletedEvent) -> None:
    """Log sync results"""
    if event.success:
        logger.info(
            f"Sync completed: {event.new_resources} new resources, "
            f"{event.total_resources} total"
        )
        if event.errors:
            logger.warning(f"Sync completed with errors: {event.errors}")
    else:
        logger.error(f"Sync failed: {event.message}, errors: {event.errors}")
```

---

## Event Handler Patterns

### Pattern 1: Progress Tracking

```python
class MyScreen(Screen):
    def on_mount(self) -> None:
        self.event_bus.subscribe(SyncProgressEvent, self._handle_progress)

    def _handle_progress(self, event: SyncProgressEvent) -> None:
        # Update progress bar
        self.progress_bar.update(total=event.total, completed=event.current)

        # Update status message
        self.status_label.update(event.message)

        # Update percentage display
        self.percentage_label.update(f"{event.percentage:.0f}%")
```

### Pattern 2: Optimistic UI Updates

```python
class ResourceListScreen(Screen):
    def on_mount(self) -> None:
        self.event_bus.subscribe(ResourceUpdatedEvent, self._handle_resource_update)

    def _handle_resource_update(self, event: ResourceUpdatedEvent) -> None:
        if event.operation == "created" and event.resource:
            # Optimistically add to UI immediately
            self._add_resource_to_list(event.resource)
        elif event.operation == "removed":
            # Optimistically remove from UI
            self._remove_resource_from_list(event.resource_id)
        else:
            # For updates, refresh from source
            self.call_later(self._refresh_resource, event.resource_id)
```

### Pattern 3: Error Aggregation

```python
class SyncMonitor:
    def __init__(self):
        self.sync_errors = []

    def on_mount(self) -> None:
        self.event_bus.subscribe(SyncProgressEvent, self._track_progress)
        self.event_bus.subscribe(SyncCompletedEvent, self._show_summary)

    def _track_progress(self, event: SyncProgressEvent) -> None:
        # Could collect errors from progress events if needed
        pass

    def _show_summary(self, event: SyncCompletedEvent) -> None:
        if event.errors:
            # Show aggregated errors
            error_modal = ErrorModal(errors=event.errors)
            self.app.push_screen(error_modal)
```

---

## Subscription Best Practices

### ✅ Subscribe in on_mount()

```python
def on_mount(self) -> None:
    """Subscribe when screen is mounted"""
    if hasattr(self.app, "event_bus") and self.app.event_bus:
        self.app.event_bus.subscribe(SyncProgressEvent, self._handle_progress)
        self.app.event_bus.subscribe(ResourceUpdatedEvent, self._handle_update)
        self.app.event_bus.subscribe(SyncCompletedEvent, self._handle_complete)
```

### ✅ Unsubscribe in on_unmount()

```python
def on_unmount(self) -> None:
    """Unsubscribe when screen is unmounted to prevent memory leaks"""
    if hasattr(self.app, "event_bus") and self.app.event_bus:
        self.app.event_bus.unsubscribe(SyncProgressEvent, self._handle_progress)
        self.app.event_bus.unsubscribe(ResourceUpdatedEvent, self._handle_update)
        self.app.event_bus.unsubscribe(SyncCompletedEvent, self._handle_complete)
```

### ✅ Use call_later() for UI Updates

```python
def _handle_resource_update(self, event: ResourceUpdatedEvent) -> None:
    """Handle resource updates without blocking"""
    # ✅ Good: Defer UI update to avoid blocking
    self.call_later(self.refresh_resource_list)

    # ❌ Bad: Direct UI manipulation can block
    # self.refresh_resource_list()  # Don't do this!
```

---

## Debugging Events

### Enable Event Logging

Add to your logger configuration:

```python
import logging

logging.getLogger("aisignal.core.services.event_bus").setLevel(logging.DEBUG)
```

Output:
```
DEBUG - Publishing SyncProgressEvent to 3 subscribers
DEBUG - Publishing (async) SyncCompletedEvent to 2 subscribers
```

### Track All Events

```python
class EventTracker:
    def __init__(self):
        self.all_events = []

    def on_mount(self) -> None:
        # Subscribe to all event types
        for event_type in [SyncProgressEvent, ResourceUpdatedEvent, SyncCompletedEvent]:
            self.event_bus.subscribe(event_type, self._track_event)

    def _track_event(self, event: BaseEvent) -> None:
        self.all_events.append({
            "type": type(event).__name__,
            "timestamp": event.timestamp,
            "data": event.__dict__
        })
        logger.debug(f"Event received: {type(event).__name__}")
```

---

## Future Events (Planned)

### ConfigUpdatedEvent

```python
@dataclass
class ConfigUpdatedEvent(BaseEvent):
    """Emitted when configuration changes"""
    config_key: str
    old_value: Any
    new_value: Any
```

### ErrorEvent

```python
@dataclass
class ErrorEvent(BaseEvent):
    """Emitted when an error occurs"""
    error_code: str
    error_message: str
    stack_trace: Optional[str] = None
    severity: str = "error"  # error, warning, critical
```

### SearchCompletedEvent

```python
@dataclass
class SearchCompletedEvent(BaseEvent):
    """Emitted when search operation completes"""
    query: str
    results_count: int
    search_time_ms: float
```

---

## See Also

- [Event Bus Architecture](./event-bus.md) - Detailed architecture documentation
- [Core Services](./core-services.md) - Core service layer documentation
- [Testing Events](../CONTRIBUTING.md#testing-events) - How to test event flows
