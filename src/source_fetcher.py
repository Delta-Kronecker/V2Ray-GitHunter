"""
Source Fetcher Module
Fetches and stores repository main page sources
"""

import os
import time
import requests
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class SourceFetcher:
    def __init__(self, sources_dir: str = "data/sources", cache_dir: str = "cache", max_workers: int = 10):
        self.sources_dir = sources_dir
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Create directories
        os.makedirs(sources_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> str or None:
        """Load source from cache"""
        cache_file = os.path.join(self.cache_dir, f"source_{cache_key}.html")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading source cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, content: str):
        """Save source to cache"""
        cache_file = os.path.join(self.cache_dir, f"source_{cache_key}.html")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving source cache: {e}")

    def fetch_repository_source(self, repo: Dict) -> str:
        """
        Fetch the main page source of a repository
        """
        try:
            url = repo['html_url']
            cache_key = self._get_cache_key(url)

            # Try cache first
            cached_content = self._load_from_cache(cache_key)
            if cached_content:
                return cached_content

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            content = response.text
            self._save_to_cache(cache_key, content)
            return content

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

    def _process_single_repo(self, repo: Dict) -> Dict:
        """Process a single repository"""
        try:
            # Fetch source
            source = self.fetch_repository_source(repo)

            if source:
                # Save source
                filepath = self.save_source(repo, source)

                if filepath:
                    result = repo.copy()
                    result['source_file'] = filepath
                    result['source_length'] = len(source)
                    return result

        except Exception as e:
            print(f"Error processing repository {repo['full_name']}: {e}")

        return None

    def fetch_and_save_all_sources(self, repos: List[Dict]) -> List[Dict]:
        """
        Fetch and save sources for all repositories using parallel processing
        """
        results = []

        print(f"Processing {len(repos)} repositories with {self.max_workers} workers")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_repo = {executor.submit(self._process_single_repo, repo): repo for repo in repos}

            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_repo)):
                repo = future_to_repo[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"Progress: {i+1}/{len(repos)} - Processed {repo['full_name']}")
                except Exception as e:
                    print(f"Error processing {repo['full_name']}: {e}")

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
