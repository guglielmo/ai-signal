# Migration Plan - GitHub Issues

Issues da creare su GitHub per completare il migration plan dell'architettura core.

---

## Issue 1: CoreService Orchestrator

**Title:** `feat(core): implement CoreService orchestrator`

**Labels:** `enhancement`, `architecture`

**Body:**
```markdown
## Description
Create the main CoreService that orchestrates Storage, Config, and Content services.

## Tasks
- [ ] Create `src/aisignal/core/services/core_service.py`
- [ ] Implement `ICoreService` interface methods
- [ ] Wire services together with DI container
- [ ] Add integration tests proving services work together

## Acceptance Criteria
- CoreService can be instantiated via DI container
- All service dependencies are correctly resolved
- Integration tests pass with real database

## Related
Part of core architecture migration (Week 2 completion)
```

---

## Issue 2: Event System

**Title:** `feat(core): implement event bus for Core-UI communication`

**Labels:** `enhancement`, `architecture`

**Body:**
```markdown
## Description
Add event-driven communication between Core services and UI layer.

## Tasks
- [ ] Create `src/aisignal/core/events.py` with simple pub/sub event bus
- [ ] Define essential events:
  - `SyncProgressEvent` - progress during content sync
  - `ResourceUpdatedEvent` - when resources change
  - `SyncCompletedEvent` - when sync finishes
- [ ] Implement event emission in Core services
- [ ] Integrate event bus with DI container

## Acceptance Criteria
- Event bus supports subscribe/publish pattern
- Core services emit events during operations
- Events are typed and documented

## Benefits
- Loose coupling between Core and UI
- Real-time UI updates without polling
- Better UX during long operations
```

---

## Issue 3: Textual UI Event Integration

**Title:** `feat(ui): subscribe Textual app to Core events`

**Labels:** `enhancement`, `ui`

**Body:**
```markdown
## Description
Make Textual UI react to Core events for real-time updates.

## Tasks
- [ ] Subscribe MainScreen to `SyncProgressEvent`
- [ ] Update sync modal with real-time progress
- [ ] Refresh resource list on `ResourceUpdatedEvent`
- [ ] Show notifications on `SyncCompletedEvent`

## Acceptance Criteria
- Sync progress shows real percentages
- Resource list updates automatically after sync
- No manual refresh needed

## Dependencies
Requires #[event-system-issue-number] to be completed first
```

---

## Issue 4: Multi-user Data Model Preparation

**Title:** `feat(core): prepare data models for multi-user support`

**Labels:** `enhancement`, `architecture`, `future`

**Body:**
```markdown
## Description
Prepare data models for future multi-user support without implementing full multi-user functionality.

## Tasks
- [ ] Add optional `user_id` field to Resource model (default: "default_user")
- [ ] Update StorageService to filter by user context
- [ ] Create database migration framework
- [ ] Document user context pattern for future implementation

## Acceptance Criteria
- Existing single-user functionality unchanged
- Data models ready for multi-user extension
- Migration path documented

## Note
This prepares the foundation only. Full multi-user implementation is deferred to a future milestone.
```

---

## Issue 5: FastAPI Skeleton

**Title:** `feat(api): create FastAPI project skeleton`

**Labels:** `enhancement`, `api`, `future`

**Body:**
```markdown
## Description
Create basic FastAPI project structure for future web API.

## Tasks
- [ ] Create `src/aisignal/api/` directory structure
- [ ] Design REST API endpoints around Core services
- [ ] Create basic FastAPI app skeleton (non-functional)
- [ ] Document API design and integration patterns

## Acceptance Criteria
- API structure documented
- FastAPI skeleton created
- Clear integration path with Core services

## Note
This is a skeleton only. Full API implementation is for a future milestone.
```

---

## Issue 6: Architecture Documentation

**Title:** `docs: complete architecture documentation`

**Labels:** `documentation`

**Body:**
```markdown
## Description
Document the completed core architecture for developers.

## Tasks
- [ ] Create developer guide for Core API usage
- [ ] Document DI container patterns
- [ ] Add architecture diagrams
- [ ] Update CLAUDE.md with final architecture state
- [ ] Remove or archive migration plan (completed)

## Acceptance Criteria
- New developers can understand the architecture
- Clear examples of extending the system
- All patterns documented
```

---

## Suggested Milestone

Create a milestone **"Core Architecture Completion"** with these issues.

**Description:**
> Complete the core architecture migration, adding event system and preparing foundation for multi-UI support.

**Due date:** Q1 2026

---

## Quick Create Commands

```bash
# Issue 1
gh issue create --title "feat(core): implement CoreService orchestrator" --label "enhancement,architecture" --body-file issue1.md

# Issue 2
gh issue create --title "feat(core): implement event bus for Core-UI communication" --label "enhancement,architecture" --body-file issue2.md

# Issue 3
gh issue create --title "feat(ui): subscribe Textual app to Core events" --label "enhancement,ui" --body-file issue3.md

# Issue 4
gh issue create --title "feat(core): prepare data models for multi-user support" --label "enhancement,architecture,future" --body-file issue4.md

# Issue 5
gh issue create --title "feat(api): create FastAPI project skeleton" --label "enhancement,api,future" --body-file issue5.md

# Issue 6
gh issue create --title "docs: complete architecture documentation" --label "documentation" --body-file issue6.md
```
