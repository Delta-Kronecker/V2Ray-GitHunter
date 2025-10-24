# V2Ray GitHunter

A modular Python project that searches GitHub for proxy configuration collectors and extracts relevant links.

## Features

- **GitHub Repository Search**: Searches GitHub for proxy configuration collectors using multiple keywords
- **Source Fetching**: Downloads and stores repository main page sources
- **Link Extraction**: Extracts all links from repository sources
- **Proxy Filtering**: Filters and categorizes proxy protocol links
- **Multiple Output Formats**: Generates JSON, CSV, Markdown, and text file outputs
- **Automated Workflow**: Runs automatically via GitHub Actions

## Project Structure

```
V2Ray-GitHunter/
├── .github/
│   └── workflows/
│       └── main.yml                 # GitHub workflow
├── src/
│   ├── __init__.py
│   ├── github_searcher.py          # GitHub API search module
│   ├── source_fetcher.py           # Fetch and store sources
│   ├── link_extractor.py           # Extract links from sources
│   ├── proxy_filter.py             # Filter proxy protocol links
│   └── output_generator.py         # Generate categorized output
├── data/
│   ├── sources/                    # Stored source files
│   └── links/                      # Extracted links
├── output/                         # Generated output files
├── requirements.txt
├── README.md
└── main.py                         # Main orchestrator
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Delta-Kronecker/V2Ray-GitHunter.git
cd V2Ray-GitHunter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Execution

Set the GitHub token environment variable:
```bash
export GITHUB_TOKEN=your_github_token
python main.py
```

### GitHub Actions

The project is configured to run automatically via GitHub Actions:
- **Scheduled**: Daily at 2 AM UTC
- **Manual**: Can be triggered manually
- **On Push**: Runs when pushed to main branch

## Search Keywords

The tool searches for repositories containing:
- config collector
- v2ray collector
- proxy collector
- shadowsocks collector
- vless collector
- vmess collector
- trojan collector
- ss collector
- hy2 collector
- proxy configs
- v2ray configs
- shadowsocks configs
- subscription
- sub merge
- config merge

## Proxy Protocols Detected

- **SS** (Shadowsocks): `ss://`
- **VLESS**: `vless://`
- **VMess**: `vmess://`
- **Trojan**: `trojan://`
- **Hysteria2**: `hy2://`, `hysteria2://`
- **Hysteria**: `hysteria://`
- **V2Ray**: `v2ray://`

## Output Files

The tool generates multiple output formats:

1. **JSON**: Complete structured data with all repository information
2. **CSV**: Tabular format for easy analysis
3. **Markdown**: Human-readable report
4. **Text**: High priority links only

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (required)

### GitHub Secrets

For GitHub Actions, set the following secret:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and research purposes only. Users are responsible for complying with applicable laws and regulations.