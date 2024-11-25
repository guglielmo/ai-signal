## Configuration

AI Signal can be configured via YAML file or through the TUI configuration panel. Main configuration options:

- AI keys
  - your working OpenAI API key, used in extracting, categorizing and rating items from the list
  - your working Jina AI API key, used to transform the sources pages into a markdown list (a-la fabric)

- Content
  - Sources to monitor
  - Sync interval, in hours
  - Categories of interest
  - Prompt for content extraction
  
- Filtering
  - Quality threshold
  - Category filters
  - Source filters
  
- Integration
  - Obsidian vault path
  - Obsidian templates
  - Social media templates
  

## Configuration initialization or update

### Via CLI
Right after installation `aisignal init` will open the `~/.config/aisignal/config.yaml` file, with a generic 
configuration. Add your API keys, to have the program work.

To upgrade the configuration, add URLs, change the prompt, add or remove categories: `aisignal config`

### Via TUI
[TODO]
It's the `c` key, once pressed it will open a configuration panel, where the config can be modified.

Please write the configuration as a `yaml` file, along these lines:

```yaml

sources:
- https://news.ycombinator.com
- https://django-news.com

prompts:
  content_extraction: |
    Please extract the top 10 news, articles, posts, whatever items compose this list.

    For each items, find or generate:
    * the title
    * the source (URL of the list source)
    * the original URL of the item, or _link_
    * the categories, among the available ones, listed below.

    Generate a list of items in markdown format, strictly following this syntax:

    # Top 10 Items

    1. **Title:** Announcing the 6.x Django Steering Council elections 🚀  
       **Source:** https://django-news.com  
       **Link:** https://cur.at/3TNDN81?m=web  
       **Categories:** Django

    2. **Title:** Django Channels 4.2.0 Release Notes  
       **Source:** https://django-news.com
       **Link:** https://cur.at/R9ZJhRV?m=web  
       **Categories:** Django
    ...
 
    In particular, the Source should only contain the URL.

categories:
- AI/ML
- Django
- Programming
- Security
- DevOps
- Docker
- Modern Data Stack

quality_threshold: 0.7
sync_interval: 24
obsidian:
  vault_path: '/~/Documents/Obsidian Vault'
  template_path: ''
social:
  twitter_template: '{title}


    {url}


    #AI #Content'
api_keys:
  jinaai: -Your JinaAI key-
  openai: -Your OpenAI key
```

