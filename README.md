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

This project is in its early development stages. 
I am not yet ready to provide a working prototype. As an open source initiative, I welcome contributors 
who can help advance the project. Please read the [Contributing Guide](CONTRIBUTING.md)


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
- [ ] Add support for more content sources (YT videos, podcasts, pdf)
- [ ] Add statistics on most used sources and categories 
  - which are the sources most interesting news come from?
  - which are the categories with most news
  - which are the trends
- [ ] Implement a double thresholds mechanism
  - all below minimal threshold is not even added to the datatable
  - all below maximum threshold is accepted as _interesting_
  - all in between must be further evaluated, by you, with your keyboard
    - y - accept
    - n - refuse
- [ ] Implement feedback loop, based on your selections
  - suggest other interests that you may have
  - highlight waning interests
- [ ] Implement custom AI models (Anthropic, Ollama, Gemini, ...)
- [ ] Add content archiving
  - read/unread items, filter by read/unread status
  - remove items
- [ ] Enable custom prompts for sources
- [ ] Enable custom filtering rules

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual)
- AI powered by OpenAI and Jina AI
- Inspired by Daniel Miessler's [Fabric](https://github.com/danielmiessler/fabric)

## Author

**Guglielmo Celata**
- GitHub: [@guglielmo](https://github.com/guglielmo)
- Mastodon: [@guille@mastodon.uno](https://mastodon.uno/@guille)