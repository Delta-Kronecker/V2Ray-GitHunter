"""
Link Extractor Module
Extracts all links from repository sources
"""

import os
import re
from typing import List, Dict, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class LinkExtractor:
    def __init__(self, links_dir: str = "data/links"):
        self.links_dir = links_dir
        os.makedirs(links_dir, exist_ok=True)

        # Patterns for different types of links
        self.url_patterns = [
            r'https?://[^\s<>"\'`]+',
            r'www\.[^\s<>"\'`]+',
            r'raw\.githubusercontent\.com/[^\s<>"\'`]+',
            r'github\.com/[^\s<>"\'`]+/raw/[^\s<>"\'`]+',
            r'gitlab\.com/[^\s<>"\'`]+/raw/[^\s<>"\'`]+',
        ]

        # File extensions that might contain proxy configs
        self.config_extensions = [
            '.txt', '.sub', '.conf', '.yaml', '.yml', '.json', '.ini'
        ]

        # Keywords that indicate proxy/subscription files
        self.proxy_keywords = [
            'sub', 'subscription', 'config', 'proxy', 'v2ray', 'ss',
            'shadowsocks', 'vless', 'vmess', 'trojan', 'hy2', 'hysteria',
            'all', 'merge', 'merged', 'node', 'list', 'collection'
        ]

    def extract_links_from_html(self, html_content: str, base_url: str = "") -> List[str]:
        """
        Extract all links from HTML content
        """
        links = set()

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract from anchor tags
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                if href and not href.startswith('#'):
                    # Convert relative URLs to absolute
                    if base_url and not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    links.add(href)

            # Extract from other tags that might contain URLs
            for tag in soup.find_all(['script', 'link', 'img', 'source']):
                for attr in ['src', 'href', 'data-src', 'content']:
                    if tag.has_attr(attr):
                        url = tag[attr].strip()
                        if url and not url.startswith('#'):
                            if base_url and not url.startswith(('http://', 'https://')):
                                url = urljoin(base_url, url)
                            links.add(url)

        except Exception as e:
            print(f"Error parsing HTML: {e}")

        # Extract URLs using regex patterns
        for pattern in self.url_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Clean up the URL
                url = match.rstrip('.,;:!?)\'"')
                if url.startswith('www.'):
                    url = 'https://' + url
                links.add(url)

        return list(links)

    def extract_links_from_text(self, text_content: str) -> List[str]:
        """
        Extract links from plain text content
        """
        links = set()

        for pattern in self.url_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                # Clean up the URL
                url = match.rstrip('.,;:!?)\'"')
                if url.startswith('www.'):
                    url = 'https://' + url
                links.add(url)

        return list(links)

    def extract_links_from_source_file(self, source_file: str) -> List[str]:
        """
        Extract links from a source file
        """
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Determine if it's HTML or text
            if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
                return self.extract_links_from_html(content)
            else:
                return self.extract_links_from_text(content)

        except Exception as e:
            print(f"Error reading source file {source_file}: {e}")
            return []

    def extract_links_from_all_sources(self, repos_with_sources: List[Dict]) -> List[Dict]:
        """
        Extract links from all repository sources
        """
        results = []

        for repo in repos_with_sources:
            print(f"Extracting links from: {repo['full_name']}")

            if 'source_file' not in repo:
                continue

            links = self.extract_links_from_source_file(repo['source_file'])

            # Save links to file
            safe_name = f"{repo['owner']}_{repo['name']}".replace("/", "_").replace("\\", "_")
            links_file = os.path.join(self.links_dir, f"{safe_name}_links.txt")

            try:
                with open(links_file, 'w', encoding='utf-8') as f:
                    for link in links:
                        f.write(f"{link}\n")

                result = repo.copy()
                result['links_file'] = links_file
                result['links_count'] = len(links)
                result['links'] = links
                results.append(result)

                print(f"Extracted {len(links)} links from {repo['full_name']}")

            except Exception as e:
                print(f"Error saving links for {repo['full_name']}: {e}")

        return results

    def filter_relevant_links(self, links: List[str]) -> Dict[str, List[str]]:
        """
        Filter links into categories based on relevance
        """
        categories = {
            'proxy_configs': [],
            'raw_files': [],
            'github_files': [],
            'subscription_files': [],
            'other': []
        }

        for link in links:
            link_lower = link.lower()

            # Check for proxy protocol indicators
            has_proxy_protocol = any(protocol in link_lower for protocol in [
                'ss://', 'vmess://', 'vless://', 'trojan://', 'hy2://',
                'shadowsocks', 'vless', 'vmess', 'trojan', 'hy2', 'hysteria'
            ])

            # Check for subscription/config indicators
            has_config_keywords = any(keyword in link_lower for keyword in self.proxy_keywords)

            # Check for raw file URLs
            is_raw_file = 'raw.githubusercontent.com' in link or '/raw/' in link

            # Check for GitHub URLs
            is_github = 'github.com' in link

            # Check for config file extensions
            has_config_extension = any(link_lower.endswith(ext) for ext in self.config_extensions)

            # Categorize the link
            if has_proxy_protocol or (has_config_keywords and has_config_extension):
                categories['proxy_configs'].append(link)
            elif is_raw_file:
                categories['raw_files'].append(link)
            elif is_github:
                categories['github_files'].append(link)
            elif has_config_keywords:
                categories['subscription_files'].append(link)
            else:
                categories['other'].append(link)

        return categories

    def get_all_unique_links(self, repos_with_links: List[Dict]) -> Set[str]:
        """
        Get all unique links from all repositories
        """
        all_links = set()

        for repo in repos_with_links:
            if 'links' in repo:
                all_links.update(repo['links'])

        return all_links