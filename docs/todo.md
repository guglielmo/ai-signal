# AI Signal Todo List

This document outlines the pending tasks and future enhancements for the AI Signal project, based on the current state of the codebase and the roadmap outlined in the project documentation.

## High Priority Tasks

1. **Complete TUI Configuration Interface**
   - Implement the configuration panel accessible via the 'c' key
   - Currently marked as [TODO] in the configuration.md documentation

2. **Fix CONTRIBUTING.md Template**
   - Update the placeholder "[Project Name]" in the CONTRIBUTING.md file
   - Customize the contributing guidelines for AI Signal specifically

3. **Implement Error Handling Improvements**
   - Add more robust error handling for API failures
   - Implement graceful degradation when services are unavailable

4. **Add Unit Tests**
   - Increase test coverage for core components
   - Add tests for UI components using Textual's testing utilities

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