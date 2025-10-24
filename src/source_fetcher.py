"""
Source Fetcher Module
Fetches and stores repository main page sources
"""

import os
import time
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class SourceFetcher:
    def __init__(self, sources_dir: str = "data/sources"):
        self.sources_dir = sources_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Create directories
        os.makedirs(sources_dir, exist_ok=True)

    def fetch_repository_source(self, repo: Dict) -> str:
        """
        Fetch the main page source of a repository
        """
        try:
            url = repo['html_url']
            print(f"Fetching source for: {repo['full_name']}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return response.text

        except Exception as e:
            print(f"Error fetching source for {repo['full_name']}: {e}")
            return ""

    def save_source(self, repo: Dict, source: str) -> str:
        """
        Save repository source to file
        """
        try:
            # Create safe filename
            safe_name = f"{repo['owner']}_{repo['name']}".replace("/", "_").replace("\\", "_")
            filename = f"{safe_name}.html"
            filepath = os.path.join(self.sources_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(source)

            return filepath

        except Exception as e:
            print(f"Error saving source for {repo['full_name']}: {e}")
            return ""

    def fetch_and_save_all_sources(self, repos: List[Dict]) -> List[Dict]:
        """
        Fetch and save sources for all repositories
        """
        results = []

        for i, repo in enumerate(repos):
            print(f"Processing repository {i+1}/{len(repos)}: {repo['full_name']}")

            # Fetch source
            source = self.fetch_repository_source(repo)

            if source:
                # Save source
                filepath = self.save_source(repo, source)

                if filepath:
                    result = repo.copy()
                    result['source_file'] = filepath
                    result['source_length'] = len(source)
                    results.append(result)

            # Rate limiting
            time.sleep(1)

        print(f"Successfully fetched and saved {len(results)} sources")
        return results

    def fetch_raw_file(self, url: str) -> str:
        """
        Fetch raw file content from URL
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"Error fetching raw file from {url}: {e}")
            return ""

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and accessible
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            # Try to make a HEAD request first
            response = self.session.head(url, timeout=10)
            return response.status_code == 200

        except:
            return False

    def get_file_size(self, url: str) -> int:
        """
        Get file size from URL
        """
        try:
            response = self.session.head(url, timeout=10)
            if response.status_code == 200:
                return int(response.headers.get('content-length', 0))
            return 0

        except:
            return 0