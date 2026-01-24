# AI Signal

![AI Signal Terminal](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/main.png)

Terminal-based AI curator that turns information noise into meaningful signal.

AI Signal is a powerful tool designed to help you regain control over your information diet in today's
overwhelming digital landscape. While existing platforms and algorithms decide what content reaches you,
AI Signal empowers you to define and implement your own content curation strategy.

By leveraging AI capabilities and your personal preferences, it transforms the constant
stream of information into meaningful, relevant insights that matter to you.
You define the categories, quality thresholds, and filtering criteria, ensuring that the content you consume
aligns with your interests and goals.

Think of it as your personal content curator that works tirelessly to surface valuable information
while filtering out noise, all running locally on your machine.
With AI Signal, you're not just consuming content – you're actively shaping how information reaches you,
making conscious choices about what deserves your attention.

## Features

- 🤖 AI-powered content analysis and categorization
- 🔍 Smart filtering based on customizable categories and quality thresholds
- 📊 Advanced sorting by date, ranking, or combined criteria
- 🔄 Automatic content synchronization from multiple sources
- 🌐 Support for various content sources (YouTube, Medium, Reddit, Hacker News, RSS feeds)
- 📱 Share curated content directly to social media
- 📝 Export to Obsidian vault with customizable templates
- ⌨️ Fully keyboard-driven interface
- 🎨 Beautiful terminal UI powered by Textual

## Installation

```bash
pip install ai-signal
```

or
```bash
pipx install ai-siganl
```
for global installation.


If using poetry:

```bash
poetry add ai-signal
poetry shell # enter the virtualenv
```

## Quick Start

1. Create a configuration file:
```bash
aisignal init
```
modify it, as described in the [configuration guide](docs/configuration.md):

2. Run AI Signal:
```bash
aisignal run
```

## Keyboard Shortcuts

### For all views
- `q`: Quit application
- `c`: Toggle configuration panel
- `s`: Force sync content
- `f`: Toggle filters sidebar
- `u`: Show usage and costs modal

### Within the items list
- `↑`/`↓`: Navigate items
- `enter`: Show item details
- `o`: Open in browser
- `t`: Share on Twitter
- `l`: Share on LinkedIn
- `e`: Export to Obsidian


## Screenshots

### Main Interface
![Main Interface](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/main.png)

### Configuration interface
![Configuration Interface](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/configuration.png)

### Resource detail interface
![Resource Detail Interface](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/detail.png)

### Sidebar hidden
![Sidebar hidden](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/sidebar_hidden.png)

### Tokens usage and costs
![Tokens modal](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/tokens_modal.png)

## Project Status

**Current Version:** 0.8.1 (Alpha)
**Status:** Active Development - RSS Integration Phase

AI Signal is a working prototype with core curation features implemented. The project is currently focused on adding native RSS/Atom feed support to reduce costs and improve performance.

**What Works:**
- ✅ Content fetching and analysis with AI (Jina AI + OpenAI)
- ✅ Customizable categories and quality thresholds
- ✅ Dual-threshold filtering system
- ✅ Terminal UI with keyboard-driven interface
- ✅ Export to Obsidian
- ✅ Token usage tracking and cost visibility

**In Development:**
- 🚧 RSS/Atom feed parsing (Issues #14-21)
- 🚧 Feed auto-discovery
- 🚧 Comprehensive test suite

**Coming Soon:**
- 📋 Resource notes and annotations
- 📊 Statistics dashboard
- 🤖 Multi-LLM support

As an open source initiative, contributors are welcome! See the [Contributing Guide](docs/CONTRIBUTING.md) and [VISION.md](VISION.md) for strategic direction.


### Development environment setup

```bash
# Clone the repository
git clone https://github.com/guglielmo/ai-signal.git
cd ai-signal


# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run the application in development mode
poetry run aisignal version
```

or, entering the virtualenv:

```bash
poetry shell
aisignal version
```


## Roadmap

See [VISION.md](VISION.md) for complete product vision and strategic direction.

### Current Focus: RSS Integration (Q4 2025)

Native RSS/Atom feed support to dramatically reduce costs and improve performance:

- [ ] **RSS Feed Parsing** - Direct parsing of RSS/Atom feeds (no API costs)
- [ ] **Auto-Discovery** - Automatically find feeds from blog URLs
- [ ] **Feed Metadata** - Track feed type, entry count, last update
- [ ] **Hybrid Approach** - RSS for feeds, Jina AI fallback for HTML pages
- [ ] **Comprehensive Testing** - Unit and integration tests with real feeds

**Why RSS First:** Reduces content fetching costs by 50-80% and improves performance 10-100×, enabling affordable AI features downstream.

**Status:** Milestone defined with 9 issues (#14-21). Estimated 16 hours implementation. [See detailed plan →](https://github.com/guglielmo/ai-signal/milestone/1)

### Phase 2: Core UX Improvements (Q1 2026)

- [ ] **Resource Notes** - Add personal notes and annotations to saved items
- [ ] **Statistics Dashboard** - Which sources and categories are most valuable?
- [ ] **Better Sorting** - Enhanced sort options (recency, category, source)
- [ ] **UI Polish** - Refinements based on real usage patterns

### Phase 3: AI Intelligence Features (Q2 2026)

- [ ] **Content Summarization** - Generate summaries and key takeaways
- [ ] **Wisdom Extraction** - Pull out actionable insights from content
- [ ] **Multi-LLM Support** - Choose from OpenAI, Claude, Gemini, or local models
- [ ] **Batch Optimization** - Efficient grouping of source analysis

### Phase 4: Learning & Personalization (Q3 2026+)

- [ ] **Feedback Loop** - Learn from your reading patterns and choices
- [ ] **Category Suggestions** - Discover new interests based on behavior
- [ ] **Source Recommendations** - Find relevant blogs and feeds
- [ ] **YouTube Videos** - Transcribe and analyze video content
- [ ] **Content Archiving** - Read/unread status, filtering, search

### Future Considerations

- [ ] Multi-user and team features
- [ ] Public curations and sharing
- [ ] Podcast and audio content support
- [ ] Browser extension for saving pages
- [ ] Mobile companion app

**Note:** The roadmap is intentionally sequenced - RSS integration enables cost-effective AI features, which in turn make learning features viable. See [technical analysis](docs/analysis-2025-10/ai_signal_tech_assessment.md) for detailed rationale.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

- **[VISION.md](VISION.md)** - Product vision and strategic direction
- **[Configuration Guide](docs/configuration.md)** - How to configure AI Signal
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[Technical Specification](docs/technical_specification.md)** - Architecture details
- **[Project Analysis](docs/analysis-2025-10/)** - Comprehensive analysis and roadmap rationale

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual)
- AI powered by OpenAI and Jina AI
- Inspired by Daniel Miessler's [Fabric](https://github.com/danielmiessler/fabric)

## Author

**Guglielmo Celata**
- GitHub: [@guglielmo](https://github.com/guglielmo)
- Mastodon: [@guille@mastodon.uno](https://mastodon.uno/@guille)
