# AI Signal

![AI Signal Terminal](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/ai-signal-terminal.png)

Terminal-based AI curator that turns information noise into meaningful signal.

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

Or with poetry:

```bash
poetry add ai-signal
```

## Quick Start

1. Create a configuration file:
```bash
aisignal init
```

2. Edit your `~/.config/aisignal/config.yaml`:
```yaml
urls:
  - https://news.ycombinator.com
  - https://medium.com/tag/artificial-intelligence
  - https://redis.com/blog

categories:
  - AI/ML
  - Programming
  - Security
  - DevOps

quality_threshold: 0.7
sync_interval: 24  # hours
```

3. Run AI Signal:
```bash
aisignal
```

## Keyboard Shortcuts

- `q`: Quit application
- `c`: Toggle configuration panel
- `s`: Force sync content
- `f`: Toggle filters
- `↑`/`↓`: Navigate items
- `enter`: Show item details
- `o`: Open in browser
- `t`: Share on Twitter
- `l`: Share on LinkedIn
- `e`: Export to Obsidian

## Configuration

AI Signal can be configured via YAML file or through the TUI configuration panel. Main configuration options:

- Content Sources
  - URLs to monitor
  - Sync interval
  - Categories of interest
  
- Filtering
  - Quality threshold
  - Category filters
  - Source filters
  
- Integration
  - Obsidian vault path
  - Obsidian templates
  - Social media templates
  
See the [configuration guide](docs/configuration.md) for detailed options.

## Screenshots

### Main Interface
![Main Interface](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/main.png)

### Content Details
![Content Details](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/details.png)

### Configuration Panel
![Configuration](https://raw.githubusercontent.com/guglielmo/ai-signal/main/docs/images/config.png)

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

### Development Setup

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

- [ ] Add support for more content sources
- [ ] Implement custom AI models
- [ ] Add content archiving
- [ ] Enable custom filtering rules
- [ ] Add data export/import
- [ ] Implement plugin system

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual)
- AI powered by OpenAI
- Inspired by Daniel Miessler's [Fabric](https://github.com/danielmiessler/fabric)

## Author

**Guglielmo Celata**
- GitHub: [@guglielmo](https://github.com/guglielmo)
- Twitter: [@guglio](https://twitter.com/guglio)