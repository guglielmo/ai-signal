# AI Signal - Incremental Core Migration Plan (KISS Approach)

## Overview

This plan follows a **strict incremental approach** to migrate AI Signal 
from a monolithic Textual application to a clean core architecture. 
Each step adds **only** what's needed for the next step, following YAGNI and KISS principles.

**Duration**: 5 weeks (40-60 total hours)  
**Approach**: Incremental, no premature optimization  
**Quality**: Production-ready, no shortcuts

## Architecture Evolution

### Current State
- Monolithic Textual application
- Business logic mixed with UI code
- Single-user local deployment

### Target State (End of Week 5)
- Clean separation between Core business logic and UI
- Dependency injection for testability
- Foundation ready for future multi-user support (but not implemented)

---

## **Week 1: Foundation - Abstract What Exists** (8-12 hours)

**Objective**: Create interfaces that abstract current functionality without changing behavior

### Monday (4-6 hours): Interface Definition
**Goal**: Define contracts for existing components

**Tasks**:
- [x] Create `core/interfaces.py` with ABC definitions for existing services
- [x] Abstract `ResourceManager`, `ContentService`, `ConfigManager` as they exist today
- [x] Define basic result types for consistent error handling
- [x] Create simple `ServiceContainer` for dependency injection

**Deliverables**:
- [x] `src/aisignal/core/interfaces.py` - ABC definitions
- [x] `src/aisignal/core/models.py` - Clean existing models (no extensions)
- [x] `src/aisignal/utils/service_container.py` - Simple DI container

### Tuesday-Thursday (6 hours total): Foundation Setup
**Daily tasks (2 hours each)**:
- [x] Set up new directory structure
- [x] Create base test framework with mock implementations
- [x] Document architectural decisions for this phase

**Deliverables**:
- [x] New directory structure implemented
- [x] Basic test framework with mock services
- [x] `docs/02-architecture_decisions.md` contains implemented and adopted decisions in sprint 1

### Friday (4-6 hours): Integration Preparation
**Goal**: Prepare for actual implementation

**Tasks**:
- [x] Create adapter pattern examples
- [x] Design migration strategy for existing code
- [x] Test DI container with mock services

**Deliverables**:
- [x] Working DI container with mock services
- [x] Migration utilities and helpers
- [x] Clear implementation roadmap for Week 2

---

## **Week 2: Core Services Implementation** (8-12 hours)

**Objective**: Implement core services that wrap existing functionality

### Monday (4-6 hours): Storage Service
**Goal**: Create `IStorageService` extension that contains existing storage classes behaviour

**Tasks**:
- [x] Implement `StorageService` that unifies `MarkdownSourceStorage` + `ParsedItemStorage`
- [x] Keep existing database schema unchanged
- [x] Add basic error handling with `OperationResult` pattern
- [x] Create unit tests with mock database

**Deliverables**:
- [x] `src/aisignal/core/services/storage_service.py`
- [x] Unit tests for storage operations
- [x] No schema changes, only abstraction layer

### Tuesday-Thursday (6 hours total): Config & Content Services
**Daily tasks**:
- [x] Day 1: Implement `ConfigService` moving existing `ConfigManager`
- [x] Day 2: Implement `ContentService` moving existing content operations  
- [ ] Day 3: Integration testing and error handling refinement

**Deliverables**:
- [x] `src/aisignal/core/services/config_service.py`
- [x] `src/aisignal/core/services/content_service.py`
- [ ] Comprehensive unit test suite

### Friday (4-6 hours): Service Integration
**Goal**: Wire services together with DI

**Tasks**:
- [ ] Create main `CoreService` that orchestrates other services
- [ ] Implement service registration and dependency resolution
- [ ] Test complete service stack with existing data

**Deliverables**:
- [ ] `src/aisignal/core/services/core_service.py`
- [ ] Integration tests proving services work together
- [ ] Performance benchmark vs original implementation

---

## **Week 3: Textual App Refactoring** (8-12 hours)

**Objective**: Remove business logic from Textual app, use Core services instead

### Monday (4-6 hours): Main App Refactoring
**Goal**: Make `ContentCuratorApp` use Core services via DI

**Tasks**:
- [ ] Refactor `app.py` to inject Core services instead of creating them directly
- [ ] Remove business logic, keep only UI orchestration
- [ ] Maintain exact same user experience

**Deliverables**:
- [ ] `src/aisignal/interfaces/textual/app.py` - refactored to use Core
- [ ] Backward compatibility maintained
- [ ] All existing functionality working

### Tuesday-Thursday (6 hours total): Screen Refactoring
**Daily tasks**:
- [ ] Day 1: Refactor `MainScreen` to use Core services
- [ ] Day 2: Refactor `ResourceDetailScreen` and other screens
- [ ] Day 3: Remove all business logic from UI components

**Deliverables**:
- [ ] All screens use only Core services
- [ ] No direct database access from UI
- [ ] Clean separation of concerns achieved

### Friday (4-6 hours): Testing & Polish
**Goal**: Ensure refactored app works perfectly

**Tasks**:
- [ ] Comprehensive regression testing
- [ ] Performance testing vs original
- [ ] User experience validation
- [ ] Bug fixes and polish

**Deliverables**:
- [ ] Fully working refactored application
- [ ] Performance meets original benchmarks
- [ ] Complete test coverage for UI-Core integration

---

## **Week 4: Event System & Polish** (8-12 hours)

**Objective**: Add event-driven communication between Core and UI

### Monday (4-6 hours): Event System
**Goal**: Implement simple event bus for Core-UI communication

**Tasks**:
- [ ] Create simple event bus with pub/sub pattern
- [ ] Define essential events: `SyncProgressEvent`, `ResourceUpdatedEvent`
- [ ] Implement event emission in Core services

**Deliverables**:
- [ ] `src/aisignal/core/events.py` - Simple event system
- [ ] Core services emit relevant events
- [ ] Event bus integrated with DI container

### Tuesday-Thursday (6 hours total): UI Event Integration
**Daily tasks**:
- [ ] Day 1: Make Textual UI subscribe to Core events
- [ ] Day 2: Implement real-time progress updates during sync
- [ ] Day 3: Add event-driven resource list updates

**Deliverables**:
- [ ] Real-time UI updates without polling
- [ ] Better user experience during long operations
- [ ] Loose coupling between Core and UI

### Friday (4-6 hours): Documentation & Cleanup
**Goal**: Complete documentation and code cleanup

**Tasks**:
- [ ] Document the new architecture
- [ ] Create developer guide for the Core API
- [ ] Code cleanup and optimization

**Deliverables**:
- [ ] Complete architecture documentation
- [ ] Developer guide for Core usage
- [ ] Clean, well-documented codebase

---

## **Week 5: Foundation for Future Expansion** (8-12 hours)

**Objective**: Prepare foundation for multi-user without implementing it

### Monday (4-6 hours): Data Model Preparation
**Goal**: Prepare data models for future multi-user support

**Tasks**:
- [ ] Add optional `user_id` fields to data models (default: "default_user")
- [ ] Create migration scripts for future schema changes
- [ ] Design user context pattern (implement in Week 6+)

**Deliverables**:
- [ ] Data models ready for multi-user (but still single-user)
- [ ] Database migration framework
- [ ] User context design documented

### Tuesday-Thursday (6 hours total): API Foundation
**Daily tasks**:
- [ ] Day 1: Design REST API structure around Core services
- [ ] Day 2: Create basic FastAPI skeleton (non-functional)
- [ ] Day 3: Document API design and integration patterns

**Deliverables**:
- [ ] FastAPI project structure created
- [ ] API design documented
- [ ] Integration patterns defined

### Friday (4-6 hours): Final Integration & Validation
**Goal**: Validate complete migration success

**Tasks**:
- [ ] End-to-end testing of complete system
- [ ] Performance benchmarking vs original
- [ ] Create migration success report

**Deliverables**:
- [ ] Complete system validation
- [ ] Performance benchmark report
- [ ] Migration success documentation

---

## Success Criteria

### **End of Week 1**: ✅ Clean Architecture Foundation
- [ ] All existing functionality abstracted behind interfaces
- [ ] Simple DI container working with mock services
- [ ] Clear migration path defined

### **End of Week 2**: ✅ Core Services Implemented
- [ ] All business logic moved to Core services
- [ ] Existing functionality preserved
- [ ] Comprehensive test coverage

### **End of Week 3**: ✅ UI Refactored
- [ ] Textual app uses only Core services
- [ ] No business logic in UI components
- [ ] Same user experience maintained

### **End of Week 4**: ✅ Event-Driven Architecture
- [ ] Real-time UI updates via events
- [ ] Loose coupling between Core and UI
- [ ] Better UX during long operations

### **End of Week 5**: ✅ Future-Ready Foundation
- [ ] Data models prepared for multi-user
- [ ] API foundation created
- [ ] Clear expansion path documented

## Quality Assurance

- **Backward compatibility** tested every day
- **Performance regression** monitoring throughout
- **User experience** validation at each step
- **Code review** at end of each major task
- **No shortcuts** - proper implementation only

## Risk Mitigation

- **Small incremental steps** - easy to rollback
- **Preserve existing behavior** - no user-facing changes until Week 5
- **Comprehensive testing** at each step
- **Clear success criteria** for each week

---

## Future Expansion (Post-Week 5)

This migration creates the foundation for:
- **Week 6+**: Multi-user support implementation
- **Week 8+**: FastAPI web interface
- **Week 10+**: MCP Server integration
- **Future**: Mobile app, advanced analytics, plugin system

The key principle: **Each week builds only on the previous week's foundation**, no premature optimization or feature creep.