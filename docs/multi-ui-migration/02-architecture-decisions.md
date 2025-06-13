# AI Signal - Architecture Decisions Record (ADR)

## Overview

This document records the key architectural decisions made during the migration from a monolithic Textual application to a clean core architecture supporting multiple interfaces.

## Decision Records

### ADR-001: Core Architecture Pattern

**Status**: ✅ FOUNDATION IMPLEMENTED (Sprint 1)  
**Date**: 2025-06-13  
**Context**: Need to separate business logic from UI to enable multiple interfaces

**Decision**: Implement a clean architecture pattern with:
- **Core Layer**: Business logic, domain models, use cases
- **Abstraction Layer**: Interfaces defining contracts between Core and UI
- **Interface Layer**: UI implementations (Textual, FastAPI, etc.)

**Rationale**:
- Enables multiple UI types (CLI, Web, Mobile, MCP Server)
- Facilitates testing by allowing dependency injection
- Provides clear separation of concerns
- Supports multi-user scenarios

**Implementation Status**: ✅ FOUNDATION COMPLETE
- Interface contracts established for all core services
- Clean separation between core logic and UI implementations
- Directory structure supports multiple interface types

**Consequences**:
- Initial complexity increase during migration
- Long-term maintainability improvement
- Easier testing and mocking
- Multiple deployment options

---

### ADR-002: Dependency Injection Framework

**Status**: ✅ IMPLEMENTED (Sprint 1)  
**Date**: 2025-06-13  
**Context**: Need clean dependency management for testability and flexibility

**Decision**: Implement advanced DI container with ABC interfaces rather than using heavy frameworks like `dependency-injector`.

**Rationale**:
- Lightweight approach fits project scope
- No external dependencies
- Clear interface definitions with ABC for runtime validation
- Support for multiple service lifetimes (singleton, transient, scoped)
- Automatic dependency injection via constructor inspection

**Implementation**:
```python
# Advanced DI container implemented in Sprint 1
class ServiceContainer:
    def register_singleton(self, interface: type, implementation: type):
        """Register as singleton - same instance returned each time"""
        
    def register_transient(self, interface: type, implementation: type):
        """Register as transient - new instance each time"""
        
    def register_scoped(self, interface: type, implementation: type):
        """Register as scoped - same instance within scope"""
        
    def get(self, interface: type):
        """Get service with automatic dependency injection"""
```

**Implementation Status**: ✅ COMPLETE
- Automatic dependency resolution with multiple service lifetimes
- Comprehensive test coverage validates the architectural approach

**Consequences**:
- Automatic dependency resolution reduces boilerplate
- Strong type safety with ABC interfaces
- Easy testing with mock service swapping
- Foundation ready for complex service graphs

---

### ADR-003: Async/Await Pattern

**Status**: Adopted  
**Date**: 2026-01-XX  
**Context**: Need efficient I/O handling for API calls and database operations

**Decision**: Make all core interfaces async-first to support:
- Non-blocking API calls to Jina AI and OpenAI
- Concurrent content processing
- Responsive UI during long operations

**Rationale**:
- Better performance for I/O-bound operations
- Enables progress reporting during sync
- Prepares for web server deployment
- Textual already supports async operations

**Implementation Strategy**:
- All core service methods are `async`
- Use `asyncio.gather()` for concurrent operations
- Implement proper async context managers for resources

**Consequences**:
- Async/await required throughout codebase
- Better concurrency and responsiveness
- Slightly more complex error handling

---

### ADR-004: Multi-User Data Model

**Status**: Proposed  
**Date**:  
**Context**: Prepare for multi-user deployments without breaking single-user usage

**Decision**: Implement user context throughout core operations:
- Add `user_id` to all data tables
- Introduce `UserContext` dataclass for operations
- Maintain backward compatibility with single-user mode

**Database Schema Changes**:
```sql
-- Add user_id to existing tables
ALTER TABLE items ADD COLUMN user_id TEXT DEFAULT 'default_user';
ALTER TABLE sources ADD COLUMN user_id TEXT DEFAULT 'default_user';
ALTER TABLE token_usage ADD COLUMN user_id TEXT DEFAULT 'default_user';

-- Add indexes for performance
CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_sources_user_id ON sources(user_id);
```

**Rationale**:
- Enables multi-tenancy without breaking existing installations
- Gradual migration path from single to multi-user
- Clean data isolation between users

**Consequences**:
- All core operations require UserContext
- Database migration required
- Storage layer complexity increase

---

### ADR-005: Error Handling Strategy

**Status**: Proposed  
**Date**: 2025-06-09  
**Context**: Need consistent error handling across core and UI layers

**Decision**: Implement Result-type pattern with `OperationResult`:
- Core operations return `OperationResult` instead of throwing exceptions
- UI layers decide how to handle errors
- Preserve exception details for debugging

**Pattern**:
```python
@dataclass
class OperationResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
```

**Rationale**:
- Explicit error handling
- UI can choose error presentation strategy
- Better error recovery options
- Functional programming influence

**Consequences**:
- More verbose return handling
- Clearer error boundaries
- Better error recovery capabilities

---

### ADR-006: Event-Driven Communication

**Status**: Proposed  
**Date**: 2025-06-09  
**Context**: Need loose coupling between Core and UI for real-time updates

**Decision**: Implement simple event bus for Core-to-UI communication:
- Core emits events for state changes
- UI subscribes to relevant events
- No direct UI callbacks in Core

**Events**:
- `SyncProgressEvent`: Progress updates during sync
- `ResourceUpdatedEvent`: Resource changes
- `ConfigUpdatedEvent`: Configuration changes

**Rationale**:
- Loose coupling between Core and UI
- Multiple UI types can listen to same events
- Real-time updates without polling
- Clean separation of concerns

**Consequences**:
- Event handling complexity in UI
- Potential race conditions to manage
- Better modularity and testability

---

### ADR-007: Configuration Management

**Status**: Proposed  
**Date**: 2025-06-09  
**Context**: Support multiple configuration sources and user-specific settings

**Decision**: Implement layered configuration system:
1. **Default values** (in code)
2. **System config** (YAML files)
3. **User config** (database/files)
4. **Environment variables** (deployment)

**Priority**: Environment > User > System > Default

**Rationale**:
- Flexible deployment options
- User customization support
- Environment-specific overrides
- Backward compatibility with existing YAML config

**Implementation**:
- `IConfigService` abstracts configuration sources
- Hot-reload capability for development
- Validation at all layers

**Consequences**:
- Configuration complexity increase
- Better deployment flexibility
- User customization support

---

### ADR-008: Storage Abstraction

**Status**: Adopted  
**Date**: 2025-06-09  
**Context**: Support multiple database backends and prepare for cloud deployment

**Decision**: Abstract storage behind `IStorageService`:
- Start with SQLite for compatibility
- Prepare for PostgreSQL for multi-user deployment
- Repository pattern for data access

**Migration Path**:
1. Unify existing storage classes
2. Add user_id to all operations
3. Implement PostgreSQL adapter
4. Add cloud storage options

**Rationale**:
- Database flexibility for different deployment scenarios
- Clean separation of storage concerns
- Performance optimization opportunities
- Cloud-ready architecture

**Consequences**:
- Storage layer abstraction overhead
- Better deployment flexibility
- Easier testing with mock storage

---

### ADR-009: API Design for Multi-Interface Support

**Status**: Proposed  
**Date**: 2025-06-09  
**Context**: Core needs to support CLI, Web, Mobile, and MCP Server interfaces

**Decision**: Design Core API to be interface-agnostic:
- All operations accept `UserContext`
- Return structured data, not UI-specific formats
- Async operations with progress callbacks
- RESTful concepts (CRUD operations)

**Interface Types**:
- **Textual CLI**: Direct Core integration
- **FastAPI Web**: REST wrapper around Core
- **MCP Server**: Protocol adapter for AI assistants
- **Mobile**: JSON API consumption

**Rationale**:
- Single Core implementation serves all interfaces
- Consistent behavior across interfaces
- Easier maintenance and feature development
- Clear API boundaries

**Consequences**:
- Interface adapters required for each UI type
- Core API must be comprehensive
- Better consistency across interfaces

---

## Implementation Guidelines

### Code Organization
```
src/aisignal/
├── core/
│   ├── interfaces.py       # All ABC definitions (this sprint)
│   ├── models.py          # Extended data models (this sprint)
│   ├── services/          # Service implementations (sprints 2-3)
│   └── events.py          # Event system (sprint 4)
├── adapters/
│   ├── storage/           # Storage implementations (sprint 2)
│   ├── config/            # Config implementations (sprint 2)
│   ├── fetch/             # Fetch implementations (sprint 3)
│   └── analysis/          # Analysis implementations (sprint 3)
└── interfaces/
    ├── textual/           # Textual UI (sprint 4)
    ├── fastapi/           # Web API (sprint 5)
    └── mcp/               # MCP Server (future)
```

### Testing Strategy
- Unit tests for each service implementation
- Integration tests for Core API
- Mock implementations for testing interfaces
- Performance benchmarks for critical paths

### Migration Strategy
- Gradual migration maintaining backward compatibility
- Feature flags for new/old code paths
- Comprehensive testing at each step
- Clear rollback procedures

---

## Future Considerations

### Scalability
- Horizontal scaling for web deployment
- Caching strategies for frequently accessed data
- Rate limiting for API endpoints

### Security
- User authentication and authorization
- API key management and rotation
- Input validation and sanitization

### Monitoring
- Application metrics and logging
- Performance monitoring
- Error tracking and alerting

### Extensions
- Plugin system for custom analysis
- Webhook support for external integrations
- GraphQL API for flexible data queries