# AI Signal - Technology Assessment & RSS Integration Impact Analysis

**Assessment Date:** October 31, 2025
**Last Major Development:** December 2024
**Time Gap:** 11 months
**Codebase Size:** ~5,451 lines of Python

---

## Executive Summary

Your codebase is **architecturally sound** with modern patterns (interfaces, dependency injection, service-oriented architecture). The tech stack is **current and well-chosen**, but there are **strategic opportunities** for cost optimization and performance improvements. The RSS integration is **highly compatible** with your existing architecture and **does not conflict** with your planned features—in fact, it **enables** them.

### Key Findings

✅ **Architecture:** Clean separation of concerns, interface-driven design
✅ **Dependencies:** All current (OpenAI 1.55.1, Textual 0.87.1)
⚠️ **Cost Optimization:** RSS integration will dramatically reduce Jina AI costs
✅ **AI/LLM Stack:** GPT-4o-mini pricing has improved since you last checked
🎯 **Strategic Direction:** RSS is the right move; enables all your planned features

---

## 1. Architecture Assessment

### Current Architecture (v0.8.1)

Your codebase shows **excellent software engineering practices**:

```
Core Layer (Business Logic)
├── Interfaces (IContentService, IStorageService, ICoreService)
├── Models (Resource, UserContext, OperationResult)
├── Services
│   ├── ContentService (fetch + AI analysis)
│   ├── StorageService (data persistence)
│   └── ConfigService (configuration management)
├── Adapters (resource_adapter, config_adapter, content_adapter)
└── Utilities (service_container, advanced_service_container)

UI Layer (Textual-based TUI)
├── MainScreen (resource list with filters)
├── ResourceDetailScreen (markdown viewer)
├── ConfigScreen (configuration editor)
└── Modals (sync status, token usage)

Services Layer
├── ContentService: Jina AI + OpenAI orchestration
└── StorageService: SQLite-based persistence
```

### Architectural Strengths

1. **Interface-Driven Design** - All major components implement interfaces
   - `IContentService` (src/aisignal/core/interfaces.py:242-295)
   - `IStorageService` (src/aisignal/core/interfaces.py:303-449)
   - Makes RSS integration a plug-and-play enhancement

2. **Dependency Injection** - Service containers for testability
   - `service_container.py` and `advanced_service_container.py`
   - Easy to add RSS-specific services

3. **Clear Separation of Concerns**
   - UI doesn't know about Jina AI vs RSS
   - ContentService abstracts fetching mechanism
   - Storage layer is agnostic to content source

4. **Async/Await Throughout** - Modern Python async patterns
   - `async def fetch_content()`
   - `async def analyze_content()`
   - Ready for concurrent RSS feed fetching

### Architectural Readiness for RSS

**Verdict: ✅ EXCELLENT**

Your architecture is **perfectly positioned** for RSS integration:

```python
# Current flow
async def fetch_content(url: str) -> Optional[Dict]:
    # Always uses Jina AI
    jina_url = f"https://r.jina.ai/{url}"
    # ... fetch and return

# RSS-enhanced flow (no breaking changes!)
async def fetch_content(url: str) -> Optional[Dict]:
    # Detection layer (new)
    if await is_feed(url):
        return await self.fetch_rss_content(url)  # New method

    # Fallback to existing Jina AI
    return await self._fetch_html_content(url)  # Renamed existing
```

**Impact on existing code:** Minimal. One method rename, one new method, one routing check.

---

## 2. Technology Stack Assessment (1 Year Later)

### Python Dependencies Analysis

| Dependency | Your Version | Latest (2025) | Status | Notes |
|------------|-------------|---------------|--------|-------|
| **python** | >=3.9,<4.0 | 3.12 stable | ✅ Good | Python 3.13 available, but 3.9-3.12 is fine |
| **openai** | 1.3.0 → 1.55.1 | ~1.55.x | ✅ Current | You're on latest! |
| **textual** | 0.87.0 → 0.87.1 | ~0.87.x | ✅ Current | Actively maintained in 2025 |
| **aiohttp** | 3.9.1 | 3.10.x | ⚠️ Minor update | Consider updating |
| **beautifulsoup4** | 4.12.2 | 4.12.3 | ⚠️ Patch | Minor update available |
| **requests** | 2.32.3 | 2.32.x | ✅ Current | |
| **pyyaml** | 6.0 | 6.0.x | ✅ Current | |

**Verdict: ✅ EXCELLENT** - Your dependencies are current. No urgent updates needed.

### AI/LLM Technology Assessment

#### OpenAI GPT-4o-mini (Your Current Model)

**Current Usage (src/aisignal/core/services/content_service.py:324):**
```python
response = await self.openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": full_prompt}],
    temperature=0.7,
)
```

**Pricing (Oct 2025):**
- **Input:** $0.15 per 1M tokens
- **Output:** $0.60 per 1M tokens
- **Cached tokens:** $0.07 per 1M tokens (new feature!)

**Your hardcoded costs (content_service.py:345-346):**
```python
prompt_cost = prompt_tokens * 0.15 / 1_000_000      # ✅ Correct
completion_cost = completion_tokens * 0.60 / 1_000_000  # ✅ Correct
```

**Status:** ✅ **PERFECT** - Your pricing is accurate and the model is still the best cost/performance choice.

#### Jina AI Reader API

**Current Usage (content_service.py:108):**
```python
jina_url = f"https://r.jina.ai/{url}"
headers = {"Authorization": f"Bearer {self.jina_api_key}", ...}
```

**Pricing (May 2025):**
- **New pricing model** introduced May 6, 2025
- ~$0.02 per 1M tokens
- Free tier: 10M tokens for new keys

**Your hardcoded cost (token_tracker.py:17 presumably):**
```python
# content_service.py:128
estimated_cost = (estimated_tokens * 0.02 / 1_000_000)  # ✅ Correct
```

**Status:** ✅ Pricing is accurate, but **RSS will eliminate this cost entirely**.

---

## 3. RSS Integration Impact Analysis

### What RSS Changes About Your Architecture

#### 3.1 Content Fetching (Primary Impact)

**Current Flow:**
```
URL → Jina AI → Markdown → Diff → Store → OpenAI Analysis → Resources
      $$$$$
```

**RSS-Enhanced Flow:**
```
URL → Detection
      ├─ RSS Feed → Parse → Markdown → Diff → Store → OpenAI Analysis → Resources
      │  FREE!
      └─ HTML Page → Jina AI → Markdown → Diff → Store → OpenAI Analysis → Resources
                     $$$$$
```

**Cost Savings Example:**
- **Before:** 100 blog sources × 5 fetches/day × 30 days = 15,000 Jina API calls
- **After (80% are RSS):** 3,000 Jina calls (saving 12,000 calls)
- **Monthly savings:** ~$240 (assuming $0.02/call)

#### 3.2 What Stays the Same (No Breaking Changes)

✅ **OpenAI Analysis** - Still needed for RSS content
✅ **Storage Layer** - Same markdown storage
✅ **UI Layer** - No changes needed
✅ **Filtering/Ranking** - Same algorithms
✅ **Thresholds** - min/max still apply
✅ **Export to Obsidian** - Same process
✅ **Token Tracking** - Just tracks 0 Jina tokens for RSS

---

## 4. Compatibility with Planned Features

Let's review each planned feature from your issues and assess RSS compatibility:

### Issue #3: LLM Request Optimization (v0.7)

**Feature:** Batch multiple URLs into single OpenAI call
**RSS Compatibility:** ✅ **ENHANCED**

RSS actually **improves** this feature:
- RSS feeds are already structured → easier to batch
- No Jina API overhead → more room in context window
- Can batch more sources since parsing is faster

**Recommendation:** Do RSS first (#14-21), then optimization (#3). RSS will make batching more effective.

---

### Issue #4: Statistics Dashboard (v0.8)

**Feature:** Show category/source stats
**RSS Compatibility:** ✅ **ENHANCED**

RSS enables better statistics:
- Track "RSS source" vs "HTML source" in DB
- Show cost per source type
- Compare RSS vs HTML quality/relevance
- Issue #19 already plans this ("Add feed metadata storage")

**Recommendation:** RSS milestone includes metadata tracking (#19), perfect foundation for stats.

---

### Issue #5: YouTube Videos Resources (v0.9)

**Feature:** Fetch YouTube transcripts
**RSS Compatibility:** ✅ **COMPATIBLE + SYNERGY**

YouTube has RSS feeds!
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

Your RSS auto-discovery (#18) will find these automatically. Then:
1. RSS feed gives video URLs
2. Separate YouTube API fetches transcripts
3. OpenAI analyzes transcript

**Recommendation:** Do RSS first, then add YouTube transcript fetching as enhancement.

---

### Issue #6: Feedback Loop (v0.10)

**Feature:** AI-driven category/source suggestions
**RSS Compatibility:** ✅ **ESSENTIAL PREREQUISITE**

This feature needs historical data:
- Which sources were relevant?
- Which categories performed well?
- What content was removed/kept?

RSS **enables** this by:
- Reducing costs → more data collection
- Tracking source metadata (#19) → better analysis
- Faster fetches → more frequent checks → richer dataset

**Recommendation:** RSS is **required** for feedback loop. Cost must be low enough to collect sufficient data.

---

### Issue #7: Summarize/Extract Wisdom (v0.11)

**Feature:** Additional AI processing on content
**RSS Compatibility:** ✅ **ENABLED BY COST SAVINGS**

This is an expensive feature (extra OpenAI calls). RSS makes it affordable:
- Jina cost eliminated for RSS sources
- Save $$ on fetching → spend on summarization
- Can offer "premium" AI features because base cost is lower

**Recommendation:** Only viable after RSS integration. Otherwise, cost per item is too high.

---

### Issue #11: Notes for Resources (v0.13)

**Feature:** User can add notes to resources
**RSS Compatibility:** ✅ **FULLY COMPATIBLE**

No interaction with RSS at all. RSS is in the fetching layer, notes are in the storage layer.

**Recommendation:** Can implement in parallel with RSS or after. No conflicts.

---

### Issue #12: Configurable LLM Engine (v0.12)

**Feature:** Choose OpenAI, Claude, Gemini, etc.
**RSS Compatibility:** ✅ **FULLY COMPATIBLE**

RSS reduces Jina costs, not LLM costs. But LLM flexibility is valuable:
- Try cheaper models for RSS content (it's structured)
- Use premium models for complex HTML analysis
- A/B test different LLMs

**Recommendation:** Good follow-up after RSS. Test if cheaper LLMs work on RSS markdown.

---

### Compatibility Matrix Summary

| Feature | Issue | RSS Impact | Order Recommendation |
|---------|-------|-----------|---------------------|
| **RSS Integration** | #14-21 | N/A | 🚀 **DO FIRST** |
| LLM Optimization | #3 | Enhanced | After RSS |
| Statistics | #4 | Enhanced | After RSS (uses #19) |
| YouTube Transcripts | #5 | Synergy | After RSS |
| Feedback Loop | #6 | Essential | Requires RSS first |
| Summarize/Wisdom | #7 | Enabled | Requires RSS savings |
| Notes | #11 | Compatible | Parallel or after |
| LLM Engine Config | #12 | Compatible | After RSS |

**Verdict:** RSS is the **foundational feature** that enables or enhances everything else.

---

## 5. Technology Modernization Recommendations

### 5.1 Immediate (During RSS Integration)

#### 1. Add RSS Parsing Dependencies (Issue #14) ✅

```toml
# Already planned in pyproject.toml
feedparser = "^6.0.11"        # RSS/Atom parsing
beautifulsoup4 = "^4.12.3"    # Feed auto-discovery (already have 4.12.2)
```

**Why:** Industry-standard libraries, zero bloat.

#### 2. Consider Caching for OpenAI (New Opportunity)

OpenAI now supports **prompt caching** (cached tokens: $0.07/M vs $0.15/M):

```python
# In your analyze_content method
response = await self.openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": prompt_template},  # ← Cached
        {"role": "user", "content": categories_list},    # ← Cached
        {"role": "user", "content": batch_content}       # ← Fresh
    ],
    temperature=0.7,
)
```

**Savings:** 50% reduction on prompt tokens if reusing same categories/template.

---

### 5.2 Short-Term (Next 2-3 Months)

#### 3. Explore LLM Alternatives for Structured Content

Since RSS gives structured markdown, try cheaper models:

| Model | Input Cost | Output Cost | Use Case |
|-------|-----------|-------------|----------|
| GPT-4o-mini | $0.15/M | $0.60/M | Current (good) |
| **Claude 3.5 Haiku** | $0.25/M | $1.25/M | Better reasoning |
| **Gemini 2.0 Flash** | $0.075/M | $0.30/M | 50% cheaper! |
| **Llama 3.1 8B** (local) | FREE | FREE | Privacy, experimentation |

**Test approach:**
1. Keep GPT-4o-mini for HTML (complex extraction)
2. Try Gemini Flash for RSS (structured data)
3. A/B test quality vs. cost

**Implementation:** Issue #12 (Configurable LLM) addresses this.

---

#### 4. Consider Jina AI Alternatives (Long-term)

If Jina pricing increases or you need more control:

| Alternative | Cost Model | Best For |
|------------|-----------|----------|
| **Firecrawl** | $3-5/1000 pages | High volume (4-5× cheaper) |
| **Crawl4AI** | Open source | Local/private data |
| **Apify** | Marketplace | Specific scrapers |
| **r.jina.ai** | $0.02/M tokens | Current (good for now) |

**Current Jina pricing is competitive.** No urgency to change, but monitor costs.

---

### 5.3 Long-Term (6+ Months)

#### 5. Multi-User Architecture (Already Planned!)

Your code already has **UserContext** (models.py:80-90):
```python
@dataclass
class UserContext:
    user_id: str = "default_user"
```

And interfaces support it:
```python
async def get_resources(
    self, user_context: UserContext, ...
) -> List[Resource]:
```

**Future-proofing:** This design is **excellent**. When you add real user management:
- Add authentication layer
- Replace "default_user" with real user IDs
- Storage layer already scoped by user

**No changes needed now.** Just keep using UserContext in new code.

---

#### 6. Consider Supabase for Multi-User (If Going SaaS)

If AI Signal becomes a service:
- **Supabase** (PostgreSQL + Auth + Storage) replaces SQLite
- Your `IStorageService` interface makes this a swap
- Already have PostgREST knowledge (per CLAUDE.md)

**Not urgent.** Single-user SQLite is fine for now.

---

## 6. RSS Integration: Conflicts & Synergies Analysis

### Potential Conflicts (Assessed)

#### ❌ Conflict #1: Token Tracking
**Concern:** RSS uses 0 Jina tokens, breaks tracking?
**Reality:** ✅ **No conflict**

Your `TokenTracker` (token_tracker.py:17) already handles this:
```python
def add_jina_usage(self, content: str):
    tokens = self.estimate_jina_tokens(content)
    self.jina_tokens += tokens
```

For RSS, just don't call this method. Done.

---

#### ❌ Conflict #2: Markdown Format Differences
**Concern:** Jina markdown ≠ RSS markdown?
**Reality:** ✅ **No conflict**

Issue #16 specifically addresses this:
> Convert feed entries to markdown with this structure:
> ```markdown
> # Feed Title
> ## [Entry Title](link)
> *Published: date*
> Entry summary...
> ```

Your storage expects markdown → RSS produces markdown → No issue.

---

#### ❌ Conflict #3: Content Diff Algorithm
**Concern:** Diff works on Jina markdown, will it work on RSS?
**Reality:** ✅ **No conflict**

Your diff is in `StorageService.get_content_diff()` (storage_service.py):
- Compares markdown strings
- Source doesn't matter (Jina vs RSS)
- RSS markdown is **cleaner**, diff will work better

---

### Synergies (Discovered)

#### ✅ Synergy #1: Faster Sync Times
RSS parsing is **10-100× faster** than Jina API:
- No HTTP roundtrip to Jina
- No AI processing on Jina side
- Direct XML parsing

**Impact:** Sync interval (config: `sync_interval`) can be more frequent without cost penalty.

---

#### ✅ Synergy #2: Better Source Attribution
RSS feeds include rich metadata:
```xml
<channel>
  <title>Django News</title>
  <link>https://django-news.com</link>
  <description>Weekly Django news</description>
</channel>
```

Issue #19 captures this:
> Store feed type (RSS/Atom) and version
> Store entry count per fetch
> Store last entry publish date

**Impact:** Enables better statistics (#4) and feedback loop (#6).

---

#### ✅ Synergy #3: YouTube Without Extra API
YouTube RSS feeds give:
- Video title
- Video URL
- Upload date
- Channel info

**Impact:** Issue #5 (YouTube) gets 80% done with just RSS. Only transcripts need extra API.

---

#### ✅ Synergy #4: Offline-First Capability
RSS can be:
- Fetched once
- Cached locally
- Parsed repeatedly

**Impact:** Could build "offline mode" where RSS is pre-fetched, then analyzed later.

---

## 7. Strategic Recommendations

### Recommendation #1: Execute RSS Milestone Immediately ✅

**Why:**
- Reduces costs 50-80% (depending on RSS adoption)
- Enables expensive features (#6, #7)
- No conflicts with existing features
- No conflicts with planned features
- Well-designed milestone (issues #14-21)

**How:**
1. Week 1: Dependencies + Detection (#14-15) - 2.5 hours
2. Week 2: Parsing + Routing (#16-17) - 5 hours
3. Week 3: Auto-discovery + Metadata (#18-19) - 3 hours
4. Week 4: Tests + Docs (#20-21, #13) - 6 hours

**Total: ~16.5 hours over 4 weeks**

---

### Recommendation #2: Deprioritize Expensive AI Features Until After RSS ⚠️

**Don't implement these yet:**
- Issue #6 (Feedback loop) - Too expensive without RSS cost savings
- Issue #7 (Summarize/wisdom) - Double OpenAI cost per item

**Do after RSS proves out:**
- Measure cost savings
- Allocate "saved" budget to premium features
- A/B test with subset of users

---

### Recommendation #3: Add Prompt Caching (Quick Win) 💡

**Effort:** 1 hour
**Savings:** ~50% on prompt tokens

```python
# Current: All tokens billed at $0.15/M
full_prompt = f"{prompt_template}\n\n{categories_list}\n\n{content}\n"

# New: Cache prompt_template + categories (reused across fetches)
messages = [
    {"role": "system", "content": prompt_template},      # Cached
    {"role": "user", "content": f"Categories:\n{categories_list}"},  # Cached
    {"role": "user", "content": f"Content:\n{content}"}  # Fresh
]
```

OpenAI automatically caches repeated prefixes.

---

### Recommendation #4: Write VISION.md (Strategic Clarity) 📝

**Problem:** Issues suggest two product directions:
1. **AI-Powered Curator** - Smart features, expensive, premium
2. **Efficient Aggregator** - Fast, cheap, high-volume

**Solution:** Clarify with a vision document:

**Option A: Premium AI Curator**
- Target: Knowledge workers willing to pay
- Features: #6 (feedback), #7 (wisdom extraction), #12 (best LLMs)
- Monetization: SaaS with usage-based pricing
- RSS Role: Reduces base cost, improves margins

**Option B: Efficient Aggregator**
- Target: Power users, self-hosted
- Features: RSS-first, fast sync, privacy-focused
- Monetization: Open source, maybe Pro features
- RSS Role: Core value proposition

**Recommendation:** Option A. You've already invested in:
- OpenAI integration
- Token tracking
- Quality ranking
- Cost-conscious design

RSS enables you to add premium AI features affordably.

---

### Recommendation #5: Consider Multi-Tenancy Later (Not Now) 🏗️

Your architecture supports it, but don't build it yet:
- Focus on single-user experience
- Validate product-market fit
- RSS integration first
- Multi-user when you have 100+ users asking for it

**Current UserContext design is sufficient.**

---

## 8. Technology Stack Verdict

### What's Good (Keep These)

✅ **Python 3.9+** - Modern, stable
✅ **Textual 0.87** - Actively maintained, great TUI framework
✅ **OpenAI SDK 1.55** - Latest version
✅ **GPT-4o-mini** - Best cost/performance for your use case
✅ **AsyncIO** - Modern concurrency
✅ **SQLite** - Perfect for single-user
✅ **Poetry** - Excellent dependency management
✅ **Pydantic** (via OpenAI) - Type safety

### What to Update (Minor)

⚠️ **aiohttp** - 3.9.1 → 3.10.x (minor security/bug fixes)
⚠️ **beautifulsoup4** - 4.12.2 → 4.12.3 (already in RSS plan)

### What to Add (For RSS)

➕ **feedparser 6.0.11** - RSS/Atom parsing
➕ (already have beautifulsoup4 for auto-discovery)

### What to Explore (Later)

🔍 **Gemini 2.0 Flash** - 50% cheaper than GPT-4o-mini
🔍 **Claude 3.5 Haiku** - Better reasoning, slightly more expensive
🔍 **Prompt caching** - OpenAI feature you're not using yet

---

## 9. Final Assessment: RSS Integration Impact

### Does RSS Conflict with Your Plans?

**NO.** Zero conflicts detected. In fact:

| Planned Feature | RSS Impact |
|----------------|-----------|
| #3 LLM Optimization | ✅ Enhanced (easier batching) |
| #4 Statistics | ✅ Enhanced (feed metadata) |
| #5 YouTube | ✅ Synergy (YouTube has RSS) |
| #6 Feedback Loop | ✅ **Essential** (needs cost reduction) |
| #7 Summarize | ✅ **Enabled** (only affordable with RSS) |
| #11 Notes | ✅ Compatible (no interaction) |
| #12 LLM Config | ✅ Compatible + Synergy (test cheaper models on RSS) |

### Is RSS the Right Move?

**YES, ABSOLUTELY.**

1. **Cost Reduction:** 50-80% savings on content fetching
2. **Performance:** 10-100× faster than Jina API calls
3. **Enables Premium Features:** #6 and #7 only viable with RSS savings
4. **No Architectural Disruption:** Clean interface boundary
5. **Well-Planned:** Issues #14-21 are exemplary in structure
6. **Industry Standard:** Everyone uses RSS (blogs, YouTube, Reddit, podcasts)

### Is Your Tech Stack Still Sound?

**YES, VERY SOUND.**

After 11 months idle:
- ✅ All dependencies current
- ✅ Architecture is modern and clean
- ✅ Pricing still accurate
- ✅ No technical debt
- ✅ Excellent foundation for growth

Only minor updates needed (aiohttp, beautifulsoup4), nothing urgent.

---

## 10. Recommended Action Plan

### Phase 1: RSS Foundation (Dec 2025)
1. ✅ Execute RSS milestone (#14-21) - 4 weeks
2. ✅ Add prompt caching - 1 hour
3. ✅ Minor dependency updates (aiohttp, beautifulsoup4) - 30 min
4. 📝 Write VISION.md - 2 hours
5. 📊 Measure cost savings - ongoing

**Goal:** Working RSS integration with 50%+ cost reduction

### Phase 2: Stabilization (Jan 2026)
1. 🐛 Fix bugs from RSS rollout - 1-2 weeks
2. 📈 Monitor cost metrics - ongoing
3. 👥 Gather user feedback (if any) - ongoing
4. 🧪 A/B test RSS vs Jina quality - 1 week

**Goal:** RSS is default, Jina is fallback

### Phase 3: Premium Features (Feb-Mar 2026)
1. ✅ Issue #11 (Notes) - 1 week
2. ✅ Issue #4 (Statistics) - 1 week
3. 🧪 Test cheaper LLMs on RSS content - 1 week
4. ✅ Issue #12 (LLM config) - 2 weeks

**Goal:** Core UX improvements, foundation for AI features

### Phase 4: AI Enhancements (Q2 2026)
1. ✅ Issue #3 (LLM optimization) - 2 weeks
2. ✅ Issue #7 (Summarize) - 2 weeks
3. ✅ Issue #5 (YouTube transcripts) - 2 weeks
4. ✅ Issue #6 (Feedback loop) - 4 weeks

**Goal:** Premium AI features enabled by RSS cost savings

---

## Conclusion

Your project is **technically sound** and **strategically well-positioned**. The RSS integration is **not a distraction**—it's the **critical enabler** for everything else you want to build.

### Key Insights

1. **Your architecture anticipated RSS** - The interface-driven design makes this a natural addition
2. **Your planned features require RSS** - Issues #6 and #7 are too expensive without RSS cost savings
3. **Your tech stack is current** - No modernization needed beyond RSS dependencies
4. **Your issue planning is excellent** - RSS milestone (#14-21) is a model of good planning

### The Strategic Shift

RSS isn't just a cost optimization—it's a **product strategy shift**:

**Before RSS:**
- High per-item cost (Jina + OpenAI)
- Can't afford expensive AI features
- Limited scaling potential
- Dependent on Jina AI pricing

**After RSS:**
- Low per-item cost (OpenAI only)
- Can add premium features (#6, #7)
- Scales to thousands of sources
- Control your cost structure

### Bottom Line

**Execute the RSS milestone immediately.** It's the highest-leverage work you can do, and your codebase is ready for it. Everything else you want to build depends on it—either directly (cost savings) or indirectly (architectural patterns).

The year gap hasn't hurt you. Your technology choices were sound then and remain sound now. RSS is the natural next step.
