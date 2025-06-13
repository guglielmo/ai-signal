# Migration Utilities and Tools

## Overview

This document provides concrete utilities, scripts, and tools to support the AI Signal Core architecture migration. For the overall migration strategy and weekly plan, see `01-migration-plan.md`.

## Purpose

These utilities enable:
- **Safe Migration**: Tools to validate changes and detect regressions
- **Progress Tracking**: Scripts to monitor migration progress
- **Risk Mitigation**: Utilities to ensure behavioral parity between old and new implementations
- **Developer Productivity**: Helper scripts to accelerate migration tasks

## Migration Utilities

### 1. Adapter Factory Functions

Located in `src/aisignal/core/adapters/`:

```python
# Config adapter
from aisignal.core.adapters.config_adapter import create_config_adapter
config_service = create_config_adapter()  # Uses existing ConfigManager

# Resource adapter  
from aisignal.core.adapters.resource_adapter import create_resource_adapter
resource_service = create_resource_adapter()  # Uses existing ResourceManager

# Content adapter
from aisignal.core.adapters.content_adapter import create_content_adapter
content_service = create_content_adapter(...)  # Uses existing ContentService
```

### 2. Service Container Configuration

```python
from aisignal.utils.advanced_service_container import ServiceContainer
from aisignal.core.adapters.config_adapter import create_config_adapter
from aisignal.core.interfaces import IConfigManager

# Create container with adapters (Week 1)
container = ServiceContainer()
container.register_singleton(IConfigManager, lambda: create_config_adapter())

# Migrate to Core services (Week 2+)
from aisignal.core.services.config_service import ConfigService
container.register_singleton(IConfigManager, ConfigService)  # Replace adapter
```

### 3. Migration Validation Scripts

Create validation scripts to ensure Core services match legacy behavior:

```python
# tests/migration/test_behavior_parity.py
async def test_config_service_parity():
    """Ensure Core ConfigService matches legacy ConfigManager behavior"""
    legacy_config = ConfigManager()
    core_config = ConfigService()
    
    assert legacy_config.categories == core_config.categories
    assert legacy_config.sources == core_config.sources
    # ... more assertions
```

### 4. Feature Flags for Gradual Migration

```python
# Enable gradual migration with feature flags
USE_CORE_SERVICES = os.getenv("AISIGNAL_USE_CORE", "false").lower() == "true"

if USE_CORE_SERVICES:
    container.register_singleton(IConfigManager, CoreConfigService)
else:
    container.register_singleton(IConfigManager, lambda: create_config_adapter())
```

### 5. Migration Helper Scripts

#### a. Legacy Code Scanner

```python
# scripts/scan_legacy_dependencies.py
"""Scan codebase for direct dependencies on legacy classes"""

import ast
import os

def find_legacy_imports():
    """Find files that import legacy classes directly"""
    legacy_classes = ['ConfigManager', 'ResourceManager', 'ContentService']
    # Scan .py files for imports of legacy classes
    # Report files that need migration
```

#### b. Interface Compliance Validator

```python  
# scripts/validate_interface_compliance.py
"""Validate that all services implement required interfaces correctly"""

def validate_interface_implementation(service_class, interface_class):
    """Ensure service class implements all interface methods"""
    # Check method signatures match
    # Validate return types
    # Ensure no missing methods
```

#### c. Migration Progress Tracker

```python
# scripts/migration_progress.py
"""Track migration progress across the codebase"""

def analyze_migration_progress():
    """Report on migration status"""
    return {
        'legacy_dependencies': count_legacy_deps(),
        'core_service_coverage': measure_core_coverage(),
        'interface_compliance': check_compliance(),
        'test_coverage': measure_test_coverage()
    }
```

## Risk Mitigation Strategies

### 1. Parallel Implementation

- Run both legacy and Core implementations side-by-side
- Compare outputs to ensure behavioral parity
- Use adapters as fallback if Core services fail

### 2. Incremental Testing

- Unit tests for each adapter
- Integration tests for adapter + legacy combinations
- End-to-end tests through interfaces only

### 3. Rollback Plan

- Keep adapters until Core services proven 100% reliable
- Environment variables to switch implementations
- Automated tests to detect regressions

### 4. Validation Gates

Each migration phase has validation gates:

**Week 1 Gate**: 
- All adapters implement interfaces correctly
- DI container works with adapters
- Existing functionality unchanged

**Week 2 Gate**:
- Core services pass all legacy behavior tests
- Performance matches or exceeds legacy
- No regressions in functionality

**Week 3 Gate**:
- UI works correctly with Core services
- No direct legacy dependencies in UI
- Feature parity maintained

**Week 4-5 Gate**:
- Complete behavior validation
- Performance benchmarks passed
- Clean architecture achieved

## Usage During Migration

These utilities are designed to be used throughout the migration timeline. For the complete weekly schedule and tasks, see `01-migration-plan.md`.

### Key Integration Points

- **Week 1**: Use adapter factories and DI container setup
- **Week 2**: Apply behavior validation scripts for Core services  
- **Week 3**: Leverage legacy dependency scanner during UI refactoring
- **Week 4-5**: Run comprehensive validation and progress tracking

### Recommended Usage Pattern

1. **Before Changes**: Run legacy dependency scanner and progress tracker
2. **During Implementation**: Use validation scripts to ensure parity
3. **After Changes**: Validate with interface compliance checker
4. **Continuous**: Monitor progress with tracking utilities

## Integration with Existing Workflow

These utilities integrate with the project's existing testing and development workflow:

```bash
# Run migration analysis
poetry run python scripts/migration_helpers.py

# Validate interface compliance  
poetry run pytest tests/test_di_container_with_mocks.py::TestWeek1FridayDeliverables

# Check migration progress
poetry run python -c "from scripts.migration_helpers import MigrationAnalyzer; print(MigrationAnalyzer().generate_migration_report())"
```