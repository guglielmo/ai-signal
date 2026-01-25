# AI Signal Documentation

Welcome to the AI Signal documentation! This directory contains all technical documentation, guides, and reference materials.

## Quick Links

- **[Project Status](../STATUS.md)** - Current status, roadmap, and what's in development
- **[Vision](../VISION.md)** - Product vision and strategic direction
- **[Main README](../README.md)** - Project overview and getting started

## Active Documentation

### Getting Started

- **[Configuration Guide](configuration.md)** - Complete configuration reference
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project

### Developer Documentation

- **[Developer Guide](guides/developer-guide.md)** - Comprehensive guide for developers
  - Architecture overview
  - Core patterns and conventions
  - Testing strategies
  - Development workflow

### Architecture

- **[Event Bus Architecture](architecture/event-bus.md)** - Event-driven communication system
- **[Event Catalog](architecture/event-catalog.md)** - Complete event reference

## Archived Documentation

Historical documents preserved for reference. These may contain outdated information but provide valuable context for project evolution.

### Analysis & Planning (October 2025)

- **[2025-10 Analysis](archive/2025-10-analysis/)** - Project reactivation analysis
  - Technology assessment
  - Issue analysis
  - RSS integration planning

### Architecture Migration (Completed January 2026)

- **[Migration Plan](archive/migration/01-migration-plan.md)** - Multi-UI architecture migration
- **[Architecture Decisions](archive/migration/02-architecture-decisions.md)** - Design decisions
- **[Migration Utilities](archive/migration/migration-utilities.md)** - Migration tools
- **[Migration Issues](archive/migration-issues.md)** - GitHub issues for migration

### Legacy Documentation

- **[Technical Specification (Legacy)](archive/technical-spec-legacy.md)** - Pre-refactoring architecture
- **[Todo List (Legacy)](archive/todo-legacy.md)** - Superseded by STATUS.md
- **[RSS Integration Plan](archive/rss-integration-plan.md)** - Initial RSS planning (see STATUS.md for current status)

## Documentation Structure

```
docs/
├── README.md                      # This file - documentation index
├── CONTRIBUTING.md                # Contribution guidelines
├── configuration.md               # Configuration reference
├── guides/                        # Developer guides
│   └── developer-guide.md        # Main developer guide
├── architecture/                  # Architecture documentation
│   ├── event-bus.md              # Event system architecture
│   └── event-catalog.md          # Event reference
├── archive/                       # Historical documentation
│   ├── 2025-10-analysis/         # October 2025 analysis
│   ├── migration/                # Architecture migration docs
│   ├── migration-issues.md       # Migration planning
│   ├── technical-spec-legacy.md  # Legacy technical spec
│   ├── todo-legacy.md            # Legacy todo list
│   └── rss-integration-plan.md   # Initial RSS planning
└── images/                        # Screenshots and diagrams
```

## Contributing to Documentation

When adding or updating documentation:

1. **Active documentation** goes in the appropriate section (guides/, architecture/, etc.)
2. **Project status and roadmap** belong in STATUS.md in the project root (single source of truth)
3. **Outdated documentation** should be moved to archive/ with appropriate naming
4. **Update this README** when adding new documentation sections
5. **Use relative links** for cross-references within documentation

### Documentation Guidelines

- Use clear, concise language
- Include code examples where appropriate
- Keep documentation up-to-date with code changes
- Add screenshots for UI features
- Follow markdown best practices
- Use kebab-case for file names (e.g., `developer-guide.md`)

## Need Help?

- Check [STATUS.md](../STATUS.md) for current project status
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- See [developer-guide.md](guides/developer-guide.md) for technical details
- Open a GitHub issue for questions or clarifications
