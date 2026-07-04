# AI Signal - Product Vision

**Version:** 0.11.0
**Last Updated:** July 2026
**Status:** Active Development - Core Architecture Complete
**Scope:** Single-user, local-only prototype (see Non-Goals below)

---

## The Problem We're Solving

In today's digital landscape, we face a paradox: **infinite information, but finite attention**.

Existing solutions fail us in different ways:
- **Social media algorithms** optimize for engagement, not value
- **RSS readers** dump everything without intelligence
- **Content aggregators** use generic popularity metrics
- **AI tools** require constant prompting and lack personalization

**The result:** Information overload, decision fatigue, and valuable content lost in noise.

## Our Vision

**AI Signal is your personal content curator that combines the power of AI with your unique preferences to transform information noise into meaningful signal.**

We believe:
1. **You should control your information diet**, not algorithms optimizing for ad revenue
2. **AI should augment your judgment**, not replace it
3. **Quality > Quantity** - seeing 10 relevant articles beats 1000 random ones
4. **Privacy matters** - your data, your machine, your control
5. **Cost efficiency enables exploration** - affordable AI means you can experiment

## What We're Building

### Core Value Proposition

AI Signal is a **terminal-based intelligent content curator** that:
1. **Monitors** your chosen sources (blogs, feeds, newsletters)
2. **Analyzes** content with AI against your categories and preferences
3. **Ranks** items by relevance and quality
4. **Surfaces** only what matters, filtered by your thresholds
5. **Learns** from your choices to improve over time

Think of it as: **"If Feedly and ChatGPT had a baby, raised by Unix philosophy"**

### Who It's For

**Primary Audience:** Knowledge workers who:
- Read 50-200+ sources regularly
- Value deep thinking over quick takes
- Prefer keyboard interfaces and local tools
- Are willing to invest time in better curation
- Care about AI costs and transparency

**Examples:**
- Software developers tracking technology trends
- Researchers monitoring their field
- Writers curating inspiration sources
- Product managers following industry news
- Indie hackers learning from peers

**Not for:** Casual readers who just want headlines from 5 sources. (Use an RSS reader instead.)

## Product Philosophy

### 1. **Intelligent Defaults, Full Control**

Start with zero configuration, but allow deep customization:
- Default categories cover common interests
- Pre-tuned thresholds work for most users
- But you can tune every parameter

### 2. **Cost-Conscious AI**

AI is powerful but can be expensive. We optimize aggressively:
- **RSS-first architecture** - Parse feeds directly (free) before falling back to AI scraping
- **Batch processing** - Group multiple sources in one LLM call
- **Prompt caching** - Reuse expensive prompt components
- **Token tracking** - Always show costs so you can make informed choices

**Target:** <$10/month for 100 sources with daily checks

### 3. **Terminal-Only, By Design**

- **Only interface:** Beautiful TUI (Textual framework), single-user, runs locally
- No web UI, no hosted version, no headless/API mode is planned for this project — see [Non-Goals](#non-goals-what-we-wont-do)

### 4. **Local-Only**

- SQLite, runs entirely on your machine — no server, no sync, no cloud dependency
- **Always:** Your data is portable (plain text, standard formats)

### 5. **Open Source, No Monetization Plans**

- **Core curation:** Open source, always free
- No premium tier, no cloud service, no monetization roadmap — if that ever happens, it would be a separate product, not paid tiers bolted onto this local tool

## Strategic Direction (2025-2026)

### Current Focus: Foundation (Q4 2025)

**Milestone:** RSS Integration
- Direct RSS/Atom parsing (eliminates 50-80% of AI scraping costs)
- Auto-discovery (paste blog URLs, we find the feed)
- Feed metadata tracking (know what's RSS vs HTML)
- Comprehensive testing

**Why this matters:** RSS integration is the **foundation** for everything else. It:
- Reduces costs enough to make premium AI features affordable
- Improves performance (10-100× faster than API scraping)
- Enables higher sync frequency
- Makes the product financially sustainable

### Phase 2: Core UX (Q1 2026)

**Focus:** Make daily usage delightful
- **Notes** - Add personal notes to resources
- **Statistics** - Which sources/categories are most valuable?
- **Better sorting** - More sort options (recency, category, source)
- **UI polish** - Refinements from real usage

**Goal:** Users check AI Signal daily, trust its recommendations

### Phase 3: Intelligence (Q2 2026)

**Focus:** AI features enabled by RSS cost savings
- **Summarization** - Generate summaries and key takeaways
- **Wisdom extraction** - Pull out actionable insights
- **LLM flexibility** - Choose your model (OpenAI, Claude, Gemini, local)
- **Batch optimization** - Group sources efficiently

**Goal:** Premium AI features that justify the cost

### Phase 4: Learning (Q3 2026)

**Focus:** Feedback loops and personalization
- **Implicit signals** - Track what you read, skip, save, remove
- **Explicit feedback** - Mark items as great/bad
- **Category suggestions** - "Based on what you read, try these categories"
- **Source recommendations** - "You might like these blogs"

**Goal:** AI Signal gets smarter the more you use it

### Future Horizons (2027+)

**Possible directions for AI Signal itself** (not committed):
- **Podcast/Video** - Transcribe and analyze audio/video content

Multi-user/teams, public curations, a browser extension, a mobile companion, and an API marketplace have been intentionally moved **out of scope** for this project (see [Non-Goals](#non-goals-what-we-wont-do)). They may be explored later in a separate project that reuses AI Signal's core abstractions, but that is not part of this roadmap.

## Technical Strategy

### Architecture Status

**Core Architecture Migration: Complete (v0.10.0)**

The codebase has been refactored to a clean architecture with:
- Interface-driven services (Storage, Config, Content)
- Dependency injection container
- Clear separation between Core business logic and UI
- Comprehensive test suite (140+ tests)
- CI/CD pipeline with automated testing

The Core business logic is decoupled from the UI via interfaces — this keeps the codebase testable and maintainable, though AI Signal itself remains a single TUI application (see [Non-Goals](#non-goals-what-we-wont-do)).

### Architecture Principles

1. **Interface-driven design** - All core components implement interfaces
2. **Dependency injection** - Services are composable and testable
3. **Async-first** - Built on asyncio for concurrent operations
4. **Storage abstraction** - SQLite by design choice (local-first); the interface could technically be swapped for a different backend, though no such change is planned for this project

### Technology Choices

**Core Stack:**
- **Python 3.9+** - Modern, async-capable, great ecosystem
- **Textual** - Best-in-class TUI framework
- **SQLite** - Perfect for single-user, portable
- **OpenAI GPT-4o-mini** - Best cost/performance for content analysis
- **Jina AI Reader** - Fallback for HTML scraping (when RSS unavailable)

**Future Explorations:**
- **Gemini 2.0 Flash** - 50% cheaper than GPT-4o-mini for structured content
- **Claude 3.5 Haiku** - Better reasoning for complex extraction
- **Local LLMs** - Llama, Mistral for privacy and zero cost

### Design Patterns We Love

- **Strategy Pattern** - Different fetchers (RSS vs HTML scraping)
- **Adapter Pattern** - Unify different AI APIs
- **Repository Pattern** - Abstract storage operations
- **Service Container** - Manage dependencies cleanly

### Quality Standards

- **Test coverage:** >80% for new code
- **Type hints:** All public APIs
- **Documentation:** Docstrings for all classes/methods
- **Code quality:** Black, isort, flake8
- **Performance:** <2s to fetch/parse an RSS feed

## Success Metrics

### Product Metrics

**Engagement (Daily Active Users):**
- **Launch:** 10 power users (me + early testers)
- **6 months:** 100 daily users
- **1 year:** 1,000+ users

**Retention:**
- **Week 1:** 60% return
- **Month 1:** 40% still active
- **Month 3:** 25% power users (our core)

**Usage Patterns:**
- Average sources tracked: 50-150
- Daily sync frequency: 2-4 times
- Items read per day: 10-20
- Export to Obsidian: 2-5 items/day

### Technical Metrics

**Cost Efficiency:**
- <$5/month average per user (API costs)
- <$10/month for heavy users (200+ sources)
- 70%+ of content via RSS (not Jina scraping)

**Performance:**
- <2s per RSS feed fetch
- <5s for HTML scraping (Jina)
- <10s for AI analysis (batch of 10 sources)
- <30s full sync of 100 sources

**Reliability:**
- 99% successful feed parses
- <1% sync failures
- Zero data loss

### Community Metrics (Future)

**Open Source Health:**
- 100+ GitHub stars (1 year)
- 10+ contributors
- Active community discussions

## Non-Goals (What We Won't Do)

To stay focused, here's what AI Signal is **not**:

❌ **Not a social network** - No feeds, likes, or follows
❌ **Not a read-it-later app** - Use Pocket/Instapaper for that
❌ **Not a bookmarking tool** - Export to Obsidian for long-term storage
❌ **Not a browser extension** - Terminal-only, single interface
❌ **Not for casual users** - Requires setup and tuning
❌ **Not enterprise software** - Individual knowledge workers first
❌ **Not a content recommendation engine** - You define categories, not us
❌ **Not a multi-user or web product** - Single-user, local-only, by design (see [Out of Scope work](STATUS.md#out-of-scope) for what was explicitly cut)

## Competitive Landscape

### How We're Different

| Tool | Strength | Limitation | AI Signal's Approach |
|------|----------|-----------|---------------------|
| **Feedly** | Massive feed support | No AI filtering, generic | AI + personal categories |
| **Inoreader** | Power features | Expensive ($50/year) | Open source, cost-conscious |
| **NewsBlur** | Social features | No AI intelligence | Focus on AI, skip social |
| **ChatGPT** | Powerful AI | Manual prompting | Automated, continuous |
| **Pocket** | Read-later | No curation | Curation first |
| **RSS readers** | Simple, free | No intelligence | Add AI layer |

### Our Unique Value

1. **AI-powered but user-controlled** - Not a black box
2. **Cost-transparent** - Always show token usage
3. **Terminal-native** - Keyboard-driven, fast, local
4. **RSS-first architecture** - Efficient by design
5. **Open source core** - Inspect, modify, self-host

## Roadmap Principles

### How We Prioritize

1. **Does it reduce costs?** (RSS integration, batching)
2. **Does it improve daily UX?** (notes, stats, sorting)
3. **Does it enable learning?** (feedback loops, signals)
4. **Is the foundation ready?** (RSS before expensive features)
5. **Can we build it well?** (avoid half-baked features)

### Feature Sequencing Logic

```
Foundation (RSS) → Core UX (notes, stats) → Intelligence (AI features) → Learning (feedback)
```

**Why this order:**
- RSS reduces costs → makes everything else affordable
- Core UX ensures adoption → creates usage data
- Intelligence adds value → justifies premium tier
- Learning compounds → creates moat

### What Gets Deferred

- **Multi-user features** - Out of scope for this project (see [Non-Goals](#non-goals-what-we-wont-do))
- **Complex AI features** - Until RSS proves cost savings
- **Mobile/web clients** - Out of scope for this project (see [Non-Goals](#non-goals-what-we-wont-do))
- **Video/podcast** - Until text sources are perfected
- **Enterprise features** - Out of scope for this project

## Risks & Mitigations

### Risk 1: AI Costs Spiral

**Threat:** Users add 500 sources, costs become unsustainable

**Mitigation:**
- RSS-first architecture (free parsing)
- Clear cost warnings in UI
- Configurable sync frequency
- Batch optimization (#3)
- Rate limiting options

### Risk 2: RSS Feeds Aren't Enough

**Threat:** Most valuable content is behind paywalls or no RSS

**Mitigation:**
- Keep Jina AI as fallback for HTML
- Support manual paste/import of content directly in the TUI
- Partner with content APIs (future)
- Focus on sources that **do** have RSS (still thousands)

### Risk 3: Users Don't Configure Properly

**Threat:** Bad categories → bad results → abandonment

**Mitigation:**
- Excellent defaults (common interest categories)
- Interactive onboarding (suggest categories from sources)
- Example configurations in docs
- Community-shared configs

### Risk 4: LLM Quality Degrades

**Threat:** GPT-4o-mini gets worse or retired

**Mitigation:**
- Multi-LLM support (Issue #12)
- Test suite with known-good extractions
- Fallback models
- Local LLM support (future)

### Risk 5: Market Is Too Niche

**Threat:** Not enough users to sustain development

**Mitigation:**
- Start as open source (no revenue pressure)
- Focus on super-users (willing to tinker)
- Clear documentation (reduce friction)
- Premium features later (if product-market fit proven)

## Values & Culture

### Development Values

1. **User sovereignty** - Your data, your rules
2. **Transparency** - Open source, visible costs
3. **Craftsmanship** - Quality over speed
4. **Pragmatism** - Perfect is the enemy of good
5. **Community** - Welcome contributors, share learnings

### Decision Framework

When choosing between options, we ask:
1. Does it serve knowledge workers?
2. Does it respect user control?
3. Is it cost-efficient?
4. Can we maintain it?
5. Does it align with our vision?

## Call to Action

### For Users

If you're drowning in information and want to regain control:
1. Try AI Signal with your top 20 sources
2. Tune your categories and thresholds
3. Give feedback on what works/doesn't
4. Share your configuration strategies

### For Contributors

If you believe in this vision:
1. Check the RSS Integration milestone (Issues #14-21)
2. Pick an issue, submit a PR
3. Share ideas in GitHub Discussions
4. Help with documentation and examples

### For Supporters

If you want this to succeed:
1. Star the repo
2. Share with your network
3. Write about your experience
4. Suggest it to others fighting information overload

---

## Conclusion

AI Signal exists because **information abundance requires intelligent curation**. The tools we have—RSS readers, social algorithms, read-it-later apps—solve parts of the problem but miss the core insight:

**The right content at the right time, filtered by your unique perspective, is far more valuable than all the content all the time.**

We're building the tool we wish existed. A tool that:
- Respects your time
- Respects your intelligence
- Respects your budget
- Respects your privacy

**Join us in turning noise into signal.**

---

## Questions This Vision Answers

**Q: Is AI Signal a business or a hobby project?**
A: A personal open-source prototype. There's no premium tier or monetization roadmap for this project.

**Q: Why not just use ChatGPT?**
A: ChatGPT requires manual prompting. AI Signal runs continuously, learns your preferences, and integrates with your workflow.

**Q: Why terminal-based?**
A: Terminals are fast, keyboard-driven, and scriptable. Perfect for power users. This project is terminal-only by design — see [Non-Goals](#non-goals-what-we-wont-do).

**Q: Can I self-host?**
A: Absolutely. It runs entirely on your machine with your API keys.

**Q: Will you support [X feature]?**
A: Check the roadmap. If it aligns with the vision and enough users want it, yes. Open an issue to discuss.

**Q: What if OpenAI raises prices?**
A: Multi-LLM support (Issue #12) and local models are planned. We're not locked in.

**Q: Is my data safe?**
A: Your data never leaves your machine except API calls to OpenAI/Jina. All storage is local SQLite.

---

**Next Steps:** See [docs/archive/2025-10-analysis/ai_signal_tech_assessment.md](docs/archive/2025-10-analysis/ai_signal_tech_assessment.md) for technical analysis and [README.md](README.md) for getting started.
