# AI Signal Todo List

This document outlines the pending tasks and future enhancements for the AI Signal project, based on the current state of the codebase and the roadmap outlined in the project documentation.

## High Priority Tasks

 1. Complete TUI Configuration Interface
    - [x] Implement a new ConfigScreen class in src/aisignal/screens/config.py based on Textual's text component
    - [x] Connect the screen to the existing key binding 'c' in the main app
    - [x] Update the config manager to handle saving changes from the UI
  2. Fix CONTRIBUTING.md Template
    - [x] Simple text replacement of "[Project Name]" with "AI Signal"
    - [x] Review and customize the contributing guidelines to match project conventions
  3. [ ] Re-engineer the app according to the `architecture_reengineering.md`, so that it can be a multi-ui, service-based app
  4. Implement Error Handling Improvements
    - [ ] Create a dedicated error handling module in src/aisignal/core/error_handler.py
    - [ ] Implement specific error types for different failure scenarios (API failures, network issues, etc.)
    - [ ] Add retry mechanisms for API calls with exponential backoff
    - [ ] Update the UI to show meaningful error messages and recovery options
  5. Add Unit Tests
    - [ ] Focus on core functionality first:
      - [ ] Create tests for ConfigManager and configuration validation
      - [ ] Add tests for ResourceManager filtering and sorting
      - [ ]Add tests for ContentService processing logic
    - [ ] For UI components:
    - [ ] Use Textual's pilot testing utilities to simulate user interactions
      - [ ] Create snapshot tests for UI components
      - [ ] Test keyboard navigation and event handling

## Feature Enhancements

### Content Sources

1. **Add Support for Additional Content Types**
   - YouTube videos
   - Podcasts
   - PDF documents

### Analytics and Insights

1. **Implement Statistics Dashboard**
   - Add statistics on most used sources
   - Add statistics on most frequent categories
   - Implement trend analysis for content interests

### Content Filtering

1. **Implement Double Threshold Mechanism**
   - Items below minimal threshold are not added to the datatable
   - Items below maximum threshold are accepted as "interesting"
   - Items between thresholds require user evaluation (accept/refuse)

2. **Implement Feedback Loop**
   - Based on user selections, suggest other potential interests
   - Highlight waning interests
   - Improve content ranking based on user feedback

### AI Integration

1. **Support Additional AI Models**
   - Anthropic
   - Ollama
   - Gemini
   - Custom local models

### Content Management

1. **Implement Content Archiving**
   - Add read/unread status tracking
   - Add filtering by read/unread status
   - Implement content removal functionality

### Customization

1. **Enable Custom Prompts for Sources**
   - Allow users to define source-specific prompts
   - Implement prompt template management

2. **Enable Custom Filtering Rules**
   - Allow users to define complex filtering rules
   - Implement rule-based filtering engine

## Technical Debt

1. **Code Refactoring**
   - Improve error handling throughout the codebase
   - Standardize async/await usage patterns
   - Optimize database queries

2. **Documentation**
   - Add inline code documentation where missing
   - Create developer documentation for contributing
   - Add API documentation for core components

3. **Performance Optimization**
   - Optimize content fetching for large sources
   - Implement caching for frequently accessed resources
   - Reduce memory usage for large datasets

## UI Improvements

1. **Enhance Keyboard Navigation**
   - Add more keyboard shortcuts for common actions
   - Improve focus management between UI components

2. **Improve Visual Feedback**
   - Add more visual cues for loading states
   - Enhance error message presentation
   - Implement theme customization

## Release Planning

1. **Prepare for Next Release**
   - Update version numbers
   - Generate changelog
   - Update documentation for new features
   - Create release notes