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
    * the descriptive text, apart from the title, if any
    * three rankings, from 0 to 1, of how much this is interesting, according to:
      1. how much it fits the categories below
      2. how much it fits the profile you find below
      3. how much it is likely that it contains valid information and is not a clickbait

    Generate a list of items in markdown format, strictly following this syntax:

    # Top 10 Items
    1. **Title:** Squashing Django Migrations Easily
       **Source:** https://django-news.com
       **Link:** https://cur.at/3TNDN81?m=web  
       **Categories:** Django Programming
       **Summary:** Safely squash Django migrations in long-running projects to optimize performance and maintain migration history integrity using django-model-info
       **Rankings:** [0.74, 0.45, 0.77]

    2. **Title:** I built a Plugin System for DJ Press  
       **Source:** https://django-news.com
       **Link:** https://cur.at/R9ZJhRV?m=web  
       **Categories:** Django
       **Summary:** Inspired by Simon Willison's DjangoCon talk on building plugin systems, the project DJ Press now has its own system built from scratch.
       **Rankings:** [0.54, 0.41, 0.58]
    ...

    (In particular, the Source should only contain the URL, not the text)


    My profile
    ----------

    ### Professional Interests
    1. **Software Development**:
      - Proficient in Python, Django, JavaScript (including D3.js, Leaflet, and Vue.js).
      - Experienced in building web apps, dashboards, and APIs with Django and integrating with modern frontend frameworks.
      - Expertise in building and deploying web applications, with focus on efficiency and scalability.
      
    2. **DevOps & Cloud Infrastructure**:
      - Skilled in Docker, Docker Compose, and Kubernetes (learning but actively applying).
      - Experienced with CI/CD pipelines using GitLab, including advanced use cases like caching, Docker image building, and multi-environment deployments.
      - Familiar with DigitalOcean, AWS, Terraform, and tools like Traefik for load balancing and reverse proxying.

    3. **Data Science & Data Engineering**:
      - Advanced knowledge in pandas and DuckDB for data processing and analysis.
      - Experience with embedding models (e.g., OpenAI embeddings) and FAISS for vector-based search.
      - Interest in large-scale data visualization and reporting with tools like Wardley mapping.

    4. **Automation and Workflows**:
      - Deep interest in streamlining processes using tools like n8n, Playwright, and Obsidian for automation, note-taking, and content curation.
      - Developing AI-enhanced pipelines for processing various content types into actionable insights or markdown notes.

    ### Areas of Interest
    1. **Open Source Technologies**:
      - Interest in open-source tools for analytics, logging, and web hosting (e.g., ELK stack alternatives, Ollama, OpenTofu).

    2. **Content Processing & Knowledge Management**:
      - Systems to queue, process, and summarize digital content, especially URLs, documents, and media.
      - Structured note-taking with Obsidian, including plugin development and integration with cloud services.

    3. **Web Scraping & Automation**:
      - Scraping data from government and public transparency portals (e.g., "amministrazione trasparente").
      - Leveraging tools like Scrapy and BeautifulSoup for document retrieval and parsing.

    4. **Visualization & Mapping**:
      - Creation of interactive, data-driven visualizations using D3.js and TopoJSON.
      - Interest in visual tools for strategic planning, like Wardley mapping.

    5. **Collaborative Tools**:
      - Proficient in GitLab, GitHub, and collaborative DevOps pipelines.
      - Experimenting with SaaS solutions to enhance team productivity.

    ### Personal Preferences
    1. **Efficiency**:
      - Preference for lightweight, modular, and efficient systems.
      - Keen on reducing unnecessary overhead in workflows and deployments.

    2. **Practical AI**:
      - Focus on practical applications of AI/ML for automation, summarization, and insights.
      - Interested in conversational AI tools and integrating them into productivity workflows.

    3. **Well-Organized Notes**:
      - Passionate about well-structured digital notes with rich metadata for future reference.


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
  mastodon_template: '{title}


    {url}


    {tags}'
api_keys:
  jinaai: -Your JinaAI key-
  openai: -Your OpenAI key
```

