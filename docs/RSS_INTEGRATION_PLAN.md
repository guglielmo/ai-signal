# AI Signal - RSS Integration Implementation Plan

**Milestone:** RSS Integration (Issues #14-21)
**Status:** IN PROGRESS (3/8 completed)
**Last Updated:** January 25, 2026
**Priority:** 🔥 CRITICAL - Reduces costs by 50-80%

---

## Executive Summary

RSS integration is the **critical next step** for AI Signal's product viability. By parsing RSS/Atom feeds directly instead of using Jina AI for HTML scraping, we can:

- **Reduce costs by 50-80%** (most blogs offer RSS feeds)
- **Improve performance 10-100×** (RSS parsing is much faster than API calls)
- **Enable higher sync frequency** (affordable to check sources more often)
- **Make premium AI features affordable** (cost savings fund other AI operations)

---

## Overall Progress

| Issue | Title | Status | Effort | Completion Date |
|-------|-------|--------|--------|-----------------|
| #14 | Add RSS parsing dependencies | ✅ CLOSED | 0.5h | Completed |
| #15 | Create RSS feed detection utility | ✅ CLOSED | 2h | Completed |
| #16 | Implement RSS feed parsing | ✅ CLOSED | 3h | Completed |
| #17 | Add routing logic | 🚧 OPEN | 2h | TBD |
| #18 | HTML feed auto-discovery | ⏳ OPEN | 2h | TBD |
| #19 | Feed metadata storage | ⏳ OPEN | 1h | TBD |
| #20 | Unit tests for RSS | ⏳ OPEN | 3h | TBD |
| #21 | Integration tests | ⏳ OPEN | 2h | TBD |

**Total Effort:** 15.5 hours
**Completed:** 5.5 hours (35%)
**Remaining:** 10 hours (65%)

---

## Phase 1: Core RSS Support ✅ COMPLETE

### Issue #14: Add RSS Parsing Dependencies ✅

**Status:** CLOSED
**Effort:** 0.5 hours
**Completion:** Completed

**What was done:**
- Added `feedparser ^6.0.11` to dependencies
- Added `beautifulsoup4 ^4.12.3` to dependencies
- Updated `poetry.lock`
- Verified installation

**Files modified:**
- `pyproject.toml`
- `poetry.lock`

---

### Issue #15: Create RSS Feed Detection Utility ✅

**Status:** CLOSED
**Effort:** 2 hours
**Completion:** Completed

**What was done:**
- Created `src/aisignal/core/utils/feed_detector.py`
- Implemented `is_feed(url: str) -> bool` function
- Implemented `get_feed_type(url: str) -> Optional[str]` function
- Added error handling for network failures
- Added comprehensive docstrings

**Key functions:**
```python
async def is_feed(url: str) -> bool:
    """Check if URL points to an RSS/Atom feed."""

async def get_feed_type(url: str) -> Optional[str]:
    """Determine feed type ('rss', 'atom', or None)."""
```

**Files created:**
- `src/aisignal/core/utils/feed_detector.py`

---

### Issue #16: Implement RSS Feed Parsing ✅

**Status:** CLOSED
**Effort:** 3 hours
**Completion:** Completed

**What was done:**
- Added `fetch_rss_content(url: str)` method to ContentService
- Implemented `_feed_to_markdown(feed)` helper method
- Feed entries converted to markdown format
- HTML entities cleaned from feed summaries
- Integrated with content diff system
- Token tracking (RSS feeds = 0 Jina tokens)
- Progress tracking integration

**Key features:**
- RSS feeds parsed with feedparser
- Markdown format matches existing content structure
- No Jina API costs for RSS feeds
- Progress events published during parsing

**Files modified:**
- `src/aisignal/core/services/content_service.py`

---

## Phase 2: Routing & Auto-Discovery 🚧 IN PROGRESS

### Issue #17: Add Routing Logic 🚧

**Status:** OPEN - NEXT TO IMPLEMENT
**Effort:** 2 hours
**Priority:** HIGH

**Objective:** Automatically detect feed type and route to appropriate handler (RSS parser or Jina AI).

**Tasks:**
- [ ] Rename existing `fetch_content` to `_fetch_html_content`
- [ ] Create new `fetch_content` that routes based on URL type
- [ ] Add feed type detection at fetch time
- [ ] Implement fallback to Jina AI for non-feed URLs
- [ ] Add logging for feed type detection
- [ ] Update sync_progress messages to indicate source type

**Implementation approach:**
```python
async def fetch_content(self, url: str) -> Optional[Dict]:
    """Fetch content from URL, auto-detecting RSS vs HTML."""

    # Check if it's a feed
    if await is_feed(url):
        self.logger.info(f"Detected RSS/Atom feed: {url}")
        return await self.fetch_rss_content(url)

    # Fall back to Jina AI for HTML pages
    self.logger.info(f"Using Jina AI for HTML page: {url}")
    return await self._fetch_html_content(url)
```

**Acceptance criteria:**
- ✅ RSS/Atom feeds use `fetch_rss_content()`
- ✅ HTML pages use `_fetch_html_content()` (Jina AI)
- ✅ Detection happens automatically without config changes
- ✅ Fallback to Jina works when feed detection fails
- ✅ Logs indicate which handler was used
- ✅ All existing HTML sources continue working

**Files to modify:**
- `src/aisignal/core/services/content_service.py` (around line 94-151)

**Estimated completion:** 2 hours after start

---

### Issue #18: HTML Feed Auto-Discovery ⏳

**Status:** OPEN - BLOCKED BY #17
**Effort:** 2 hours
**Priority:** MEDIUM

**Objective:** Automatically discover RSS/Atom feeds from HTML pages, allowing users to add blog homepages instead of feed URLs.

**Tasks:**
- [ ] Add `discover_feeds(url: str) -> List[str]` function to feed_detector.py
- [ ] Parse HTML for `<link rel="alternate">` tags
- [ ] Support both `application/rss+xml` and `application/atom+xml` types
- [ ] Handle relative and absolute feed URLs
- [ ] Integrate discovery into fetch routing logic
- [ ] Add preference for first discovered feed
- [ ] Add logging for discovered feeds

**Implementation approach:**
```python
async def discover_feeds(url: str) -> List[str]:
    """Discover RSS/Atom feeds from HTML page."""
    # Fetch HTML
    # Parse for <link rel="alternate" type="application/rss+xml">
    # Handle relative/absolute URLs
    # Return list of discovered feeds

# Update routing logic:
async def fetch_content(self, url: str) -> Optional[Dict]:
    if await is_feed(url):
        return await self.fetch_rss_content(url)

    # Try to discover feeds if not a direct feed
    discovered_feeds = await discover_feeds(url)
    if discovered_feeds:
        self.logger.info(f"Auto-discovered feed: {discovered_feeds[0]}")
        return await self.fetch_rss_content(discovered_feeds[0])

    # Fall back to Jina AI
    return await self._fetch_html_content(url)
```

**Acceptance criteria:**
- ✅ Discovers RSS feeds from HTML pages
- ✅ Handles relative URLs correctly (e.g., `/feed.xml`)
- ✅ Handles absolute URLs correctly
- ✅ Returns feeds in priority order
- ✅ Works with WordPress, Ghost, etc.
- ✅ User can add `https://blog.example.com` and system finds feed

**Files to modify:**
- `src/aisignal/core/utils/feed_detector.py`
- `src/aisignal/core/services/content_service.py`

**Estimated completion:** 2 hours after #17

---

### Issue #19: Feed Metadata Storage ⏳

**Status:** OPEN - BLOCKED BY #18
**Effort:** 1 hour
**Priority:** LOW

**Objective:** Track feed-specific metadata for better monitoring and debugging.

**Tasks:**
- [ ] Add optional feed_metadata field to content storage
- [ ] Store feed type (RSS/Atom) and version
- [ ] Store entry count per fetch
- [ ] Store last entry publish date
- [ ] Update UI to show source type indicator ([RSS], [Atom], [HTML])
- [ ] Add feed stats to sync progress display

**Database schema changes:**
```sql
ALTER TABLE sources ADD COLUMN source_type TEXT;
ALTER TABLE sources ADD COLUMN feed_entry_count INTEGER;
ALTER TABLE sources ADD COLUMN last_publish_date TIMESTAMP;
```

**UI enhancement:**
```
┌─ Source: django-news.com [RSS] ─────────┐
│ 15 new items                            │
│ Last updated: 2 hours ago               │
└─────────────────────────────────────────┘
```

**Acceptance criteria:**
- ✅ Feed metadata persisted in SQLite
- ✅ Source type visible in UI
- ✅ Sync progress shows "Fetching RSS feed" vs "Fetching page"
- ✅ Entry count displayed after sync
- ✅ Feed metadata queryable for debugging

**Files to modify:**
- `src/aisignal/core/services/storage_service.py`
- `src/aisignal/ui/textual/screens/main_screen.py`
- Database schema (migration needed)

**Estimated completion:** 1 hour after #18

---

## Phase 3: Testing & Polish ⏳ PENDING

### Issue #20: Unit Tests for RSS Functionality ⏳

**Status:** OPEN - BLOCKED BY #19
**Effort:** 3 hours
**Priority:** HIGH

**Objective:** Comprehensive unit tests for RSS detection, parsing, auto-discovery, and markdown conversion.

**Tasks:**
- [ ] Create `tests/test_feed_detector.py`
- [ ] Test `is_feed()` with various feed types
- [ ] Test `is_feed()` with non-feed content
- [ ] Test `get_feed_type()` RSS vs Atom detection
- [ ] Test `discover_feeds()` with sample HTML
- [ ] Test `_feed_to_markdown()` conversion
- [ ] Test error handling (malformed feeds, network errors)
- [ ] Mock feedparser responses
- [ ] Achieve >80% code coverage for new code

**Test cases:**

1. **Feed Detection**
   - Valid RSS 2.0 feed → True
   - Valid Atom feed → True
   - HTML page → False
   - Malformed XML → False

2. **Feed Type Detection**
   - RSS 2.0 → "rss"
   - Atom 1.0 → "atom"
   - HTML → None

3. **Auto-Discovery**
   - HTML with RSS link → [feed_url]
   - HTML with multiple feeds → [feed1, feed2]
   - HTML without feeds → []
   - Relative URLs → converted to absolute

4. **Markdown Conversion**
   - Feed with 3 entries → proper markdown
   - Entry with HTML entities → cleaned
   - Entry without summary → handled gracefully

**Acceptance criteria:**
- ✅ All unit tests pass
- ✅ Code coverage >80% for feed_detector.py
- ✅ Tests run in <2 seconds
- ✅ Tests use fixtures for sample feeds
- ✅ Mock external HTTP calls

**Files to create:**
- `tests/test_feed_detector.py`
- `tests/test_content_service_rss.py`
- `tests/fixtures/sample_feeds.py`

**Estimated completion:** 3 hours after #19

---

### Issue #21: Integration Tests with Real RSS Feeds ⏳

**Status:** OPEN - BLOCKED BY #20
**Effort:** 2 hours
**Priority:** MEDIUM

**Objective:** Validate end-to-end functionality with real-world RSS feeds.

**Tasks:**
- [ ] Create `tests/integration/test_rss_integration.py`
- [ ] Test with real Hacker News RSS feed
- [ ] Test with real blog feed (WordPress/Ghost)
- [ ] Test with YouTube channel RSS
- [ ] Test with Reddit subreddit RSS
- [ ] Test mixed source list (HTML + RSS)
- [ ] Verify token usage (RSS should use 0 Jina tokens)
- [ ] Test content diff with RSS feeds
- [ ] Test full sync workflow with RSS sources

**Test feeds:**
```python
TEST_FEEDS = {
    "hacker_news": "https://news.ycombinator.com/rss",
    "lobsters": "https://lobste.rs/rss",
    "python_blog": "https://blog.python.org/feeds/posts/default",
}
```

**Acceptance criteria:**
- ✅ All integration tests pass
- ✅ RSS feeds fetch successfully
- ✅ Content is properly stored
- ✅ No Jina tokens consumed for RSS feeds
- ✅ Sync progress updates correctly
- ✅ Mixed HTML/RSS sources work together

**Performance validation:**
- RSS feed fetch <2 seconds
- Markdown conversion <100ms
- Memory usage reasonable for 100+ entries

**Files to create:**
- `tests/integration/test_rss_integration.py`

**Estimated completion:** 2 hours after #20

---

## Success Metrics

### Cost Reduction
**Target:** 50-80% reduction in Jina AI costs

**Measurement:**
- Before: 100% of sources use Jina AI
- After: 70%+ of sources use RSS (free), 30% use Jina AI
- Cost per sync: Reduced from $X to $0.2-0.5X

### Performance Improvement
**Target:** 10-100× faster for RSS sources

**Measurement:**
- RSS feed fetch: <2 seconds (vs 5-10s for Jina AI)
- Markdown conversion: <100ms
- Full sync (100 sources, 70% RSS): ~5 minutes (vs 10-15 minutes)

### Feature Enablement
**Goal:** Make AI features affordable

**Impact:**
- Saved costs can fund AI summarization
- Saved costs can fund wisdom extraction
- Higher sync frequency becomes viable (hourly vs daily)

---

## Implementation Strategy

### Incremental Approach

1. **Phase 1** ✅ COMPLETE: Core RSS support (Issues #14-16)
   - Add dependencies
   - Implement basic RSS parsing
   - Convert feeds to markdown

2. **Phase 2** 🚧 IN PROGRESS: Routing & Discovery (Issues #17-19)
   - Auto-detect feed vs HTML
   - Auto-discover feeds from blog URLs
   - Track feed metadata

3. **Phase 3** ⏳ PENDING: Testing & Polish (Issues #20-21)
   - Comprehensive unit tests
   - Integration tests with real feeds
   - Performance validation

### Quality Gates

Each issue must meet these criteria before closing:

- ✅ **Functionality:** All tasks completed
- ✅ **Code Quality:** Passes black, isort, flake8
- ✅ **Tests:** Unit tests written and passing
- ✅ **Documentation:** Docstrings and inline comments
- ✅ **Integration:** Works with existing features
- ✅ **Performance:** Meets performance targets

### Risk Mitigation

**Risk:** RSS feeds don't have full content
**Mitigation:** Hybrid approach - RSS where available, Jina AI fallback

**Risk:** Feed formats vary widely
**Mitigation:** Extensive testing with real-world feeds (Issue #21)

**Risk:** Breaking existing HTML sources
**Mitigation:** Routing logic with fallback, regression testing

---

## Next Steps

### Immediate (This Session)

1. ✅ Review all issue details
2. ✅ Create implementation plan (this document)
3. 🚧 Implement Issue #17: Routing logic
4. ⏳ Implement Issue #18: Auto-discovery
5. ⏳ Implement Issue #19: Feed metadata
6. ⏳ Implement Issue #20: Unit tests
7. ⏳ Implement Issue #21: Integration tests

### After Completion

1. Update VISION.md milestone status
2. Create release notes for v0.11.0
3. Update README with RSS capabilities
4. Document cost savings for users
5. Plan next milestone (Core UX improvements)

---

## Architecture Integration

### How RSS Fits Into Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ ContentService                                      │    │
│  │  - fetch_content() [NEW: Auto-routing]             │    │
│  │  - fetch_rss_content() [NEW: RSS handler]          │    │
│  │  - _fetch_html_content() [Renamed from fetch_content]│  │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Utils                                               │    │
│  │  - feed_detector.py [NEW]                          │    │
│  │    - is_feed()                                     │    │
│  │    - get_feed_type()                               │    │
│  │    - discover_feeds() [NEW in #18]                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│  - feedparser library (RSS/Atom parsing)                    │
│  - beautifulsoup4 (HTML parsing for auto-discovery)         │
│  - Jina AI Reader API (fallback for HTML pages)             │
└─────────────────────────────────────────────────────────────┘
```

### Service Flow

```
User triggers sync
     ↓
CoreService.sync_sources()
     ↓
ContentService.fetch_content(url)
     ↓
   [Auto-detect]
     ├─→ is_feed(url)?
     │   ├─ Yes → fetch_rss_content() → 0 Jina tokens
     │   └─ No → discover_feeds(url)?
     │          ├─ Found → fetch_rss_content(feed_url) → 0 tokens
     │          └─ None → _fetch_html_content() → Jina tokens
     ↓
Convert to markdown
     ↓
Store in database (StorageService)
     ↓
Publish ResourceUpdatedEvent
     ↓
UI updates in real-time
```

---

## References

- **Vision Document:** `/home/user/ai-signal/VISION.md`
- **Project Status:** `/home/user/ai-signal/STATUS.md`
- **Developer Guide:** `/home/user/ai-signal/docs/DEVELOPER_GUIDE.md`
- **GitHub Milestone:** RSS Integration (Issues #14-21)
- **Related Files:**
  - `src/aisignal/core/services/content_service.py`
  - `src/aisignal/core/utils/feed_detector.py` (new)
  - `tests/test_feed_detector.py` (new)

---

**Document Prepared By:** AI Signal Development Team
**Next Review:** After Issue #17 completion
**Questions/Feedback:** Open an issue on GitHub
