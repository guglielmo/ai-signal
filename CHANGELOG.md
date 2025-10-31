# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-10-31

### Added
- Core architecture layer with ABC interfaces (IStorageService, IConfigService, IContentService)
- Advanced dependency injection container with singleton, transient, and scoped service lifetimes
- Comprehensive test suite (140 tests covering unit, integration, and error recovery scenarios)
- CLAUDE.md with architectural guidance for Claude Code
- VISION.md with product vision and strategic roadmap
- Migration documentation and architecture decisions
- Project analysis documents
- Mock services for testing
- Adapter pattern implementations for external dependencies
- User ID support in models for future multi-user capability

### Changed
- Restructured UI layer from `src/aisignal/` to `src/aisignal/ui/textual/` for multi-interface support
- Refactored ConfigService from core/config.py to core/services/config_service.py
- Refactored ContentService to implement IContentService interface
- Moved storage logic to unified StorageService in core/services/storage_service.py
- Updated README with current project status and enhanced roadmap
- Improved error handling with OperationResult pattern in core services

### Removed
- Legacy storage.py (420 lines) - replaced by storage_service.py with cleaner interface
- CLAUDE.md from .gitignore (now tracked in repository)

### Technical
- Completed Week 1-2 of 5-week architecture migration plan
- All existing functionality preserved with backward compatibility
- Foundation ready for Web API, Mobile, and MCP Server interfaces

## [0.8.1] - 2025-06-06

### Added
- Github actions workflow to automatically publish to PyPi whenever a new release is created

### Changed
- Enhanced configuration editor UI, using a Text componentto change the config file conten in the app
- Refactored sync widget into modal screen for improved UX
- Replaced sync widget with modal and enhanced sync progress logic
- Added sync tracking, exceptions, and UI improvements
- Updated contributing documentation

## [0.7.0] - 2024-12-16

### Changed
- Refactored content analysis and fetching mechanisms
- Enhanced sync process with resource deduping
- Improved content analysis logging

## [0.6.1] - 2024-12-03

### Removed
- ResourceMarkdownScreen

### Changed
- Updated resource actions

## [0.6.0] - 2024-12-02

### Changed
- Improved resource management and UI updates
- Refactored screens and split into different files under the screens package for better readability

## [0.5.4] - 2024-12-01

### Added
- Filter reset feature
- Double thresholds mechanism (documented in README)

### Changed
- Updated UI behaviors
- Updated key binding for token usage
- Updated README instructions
- Added tokens usage and costs section with image to README

## [0.5.3] - 2024-11-30

### Added
- Implemented detailed token tracking with costs

## [0.5.2] - 2024-11-30

### Added
- Implemented detailed token tracking with costs

## [0.5.1] - 2024-11-30

### Fixed
- Bug on item shown when enter is pressed on ResourceDetailScreen

## [0.5.0] - 2024-11-30

### Added
- Token tracking feature for session and total usage

## [0.4.1] - 2024-11-30

### Added
- Ranking field to item storage and processing

## [0.4.0] - Initial release

[Unreleased]: https://github.com/guglielmo/ai-signal/compare/0.7.0...HEAD
[0.7.0]: https://github.com/guglielmo/ai-signal/compare/0.6.1...0.7.0
[0.6.1]: https://github.com/guglielmo/ai-signal/compare/0.6...0.6.1
[0.6.0]: https://github.com/guglielmo/ai-signal/compare/0.5.4...0.6
[0.5.4]: https://github.com/guglielmo/ai-signal/compare/0.5.1...0.5.4
[0.5.3]: https://github.com/guglielmo/ai-signal/compare/0.5.2...0.5.3
[0.5.2]: https://github.com/guglielmo/ai-signal/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/guglielmo/ai-signal/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/guglielmo/ai-signal/compare/0.4.1...0.5.0
[0.4.1]: https://github.com/guglielmo/ai-signal/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/guglielmo/ai-signal/releases/tag/0.4.0