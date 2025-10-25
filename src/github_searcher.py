"""
GitHub Searcher Module
Searches GitHub for proxy configuration collector repositories
"""

import os
import time
import json
import hashlib
import re
from typing import List, Dict, Set
from github import Github
from github.Repository import Repository


class GitHubSearcher:
    def __init__(self, token: str, cache_dir: str = "cache", max_results_per_search: int = 100):
        self.github = Github(token)
        self.cache_dir = cache_dir
        self.max_results_per_search = max_results_per_search
        os.makedirs(cache_dir, exist_ok=True)

        self.search_keywords = [
            "config collector",
            "v2ray collector",
            "proxy collector",
            "shadowsocks collector",
            "vless collector",
            "vmess collector",
            "trojan collector",
            "ss collector",
            "hy2 collector",
            "proxy configs",
            "v2ray configs",
            "shadowsocks configs",
            "subscription",
            "sub merge",
            "config merge"
        ]

        self.proxy_protocols = [
            "ss", "shadowsocks", "vless", "vmess", "trojan", "hy2",
            "hysteria2", "v2ray", "proxy"
        ]

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for search query"""
        return hashlib.md5(query.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> List[Dict] or None:
        """Load search results from cache"""
        cache_file = os.path.join(self.cache_dir, f"search_{cache_key}.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    # Cache is valid for 24 hours
                    if time.time() - data.get('timestamp', 0) < 86400:
                        return data.get('results', [])
        except Exception as e:
            print(f"Error loading cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, results: List[Dict]):
        """Save search results to cache"""
        cache_file = os.path.join(self.cache_dir, f"search_{cache_key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'results': results
                }, f)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def search_repositories(self) -> List[Dict]:
        """
        Search GitHub for repositories containing proxy configuration collectors
        """
        all_repos = []
        seen_repos = set()

        for keyword in self.search_keywords:
            try:
                print(f"Searching for: {keyword}")

                # Search with different query combinations
                queries = [
                    f"{keyword} in:name,description,readme",
                    f"{keyword} in:name,description",
                    f"{keyword}"
                ]

                for query in queries:
                    cache_key = self._get_cache_key(query)

                    # Try to load from cache first
                    cached_results = self._load_from_cache(cache_key)
                    if cached_results:
                        print(f"Loaded {len(cached_results)} results from cache for: {query}")
                        query_repos = cached_results
                    else:
                        # Perform search
                        query_repos = []
                        try:
                            repos = self.github.search_repositories(
                                query=query,
                                sort="stars",
                                order="desc"
                            )

                            count = 0
                            for repo in repos:
                                if count >= self.max_results_per_search:
                                    break

                                repo_id = f"{repo.owner.login}/{repo.name}"
                                if repo_id not in seen_repos:
                                    seen_repos.add(repo_id)

                                    # Get repository README for about section
                                    about_text = ""
                                    try:
                                        readme = repo.get_readme()
                                        if readme:
                                            about_text = readme.decoded_content.decode('utf-8')[:500]  # First 500 chars
                                            # Remove markdown and HTML tags
                                            about_text = re.sub(r'<[^>]+>', '', about_text)
                                            about_text = re.sub(r'[#*`\[\]()_-]', '', about_text)
                                            about_text = ' '.join(about_text.split())[:200]  # First 200 words
                                    except:
                                        pass

                                    repo_info = {
                                        'name': repo.name,
                                        'full_name': repo.full_name,
                                        'owner': repo.owner.login,
                                        'description': repo.description or '',
                                        'about': about_text,
                                        'html_url': repo.html_url,
                                        'clone_url': repo.clone_url,
                                        'stars': repo.stargazers_count,
                                        'forks': repo.forks_count,
                                        'language': repo.language,
                                        'created_at': repo.created_at.isoformat() if repo.created_at else None,
                                        'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                                        'size': repo.size,
                                        'topics': list(repo.get_topics()) if repo.get_topics() else [],
                                        'search_keyword': keyword
                                    }

                                    query_repos.append(repo_info)
                                    count += 1

                            # Save to cache
                            self._save_to_cache(cache_key, query_repos)
                            print(f"Found {count} repositories for query: {query}")

                            # Rate limiting
                            time.sleep(1)

                        except Exception as e:
                            print(f"Error searching with query '{query}': {e}")
                            continue

                    all_repos.extend(query_repos)

            except Exception as e:
                print(f"Error searching for keyword '{keyword}': {e}")
                continue

        # Remove duplicates and sort by stars
        unique_repos = []
        seen = set()

        for repo in all_repos:
            repo_key = repo['full_name']
            if repo_key not in seen:
                seen.add(repo_key)
                unique_repos.append(repo)

        # Sort by stars (descending)
        unique_repos.sort(key=lambda x: x['stars'], reverse=True)

        print(f"Total unique repositories found: {len(unique_repos)}")
        return unique_repos

    def get_repository_readme(self, repo: Dict) -> str:
        """
        Get the README content of a repository
        """
        try:
            repo_obj = self.github.get_repo(repo['full_name'])

            # Try different README filenames
            readme_names = ['README.md', 'README.txt', 'README', 'readme.md', 'readme.txt', 'readme']

            for name in readme_names:
                try:
                    content = repo_obj.get_contents(name)
                    return content.decoded_content.decode('utf-8')
                except:
                    continue

            return ""

        except Exception as e:
            print(f"Error getting README for {repo['full_name']}: {e}")
            return ""

    def get_repository_files(self, repo: Dict, extensions: List[str] = None) -> List[Dict]:
        """
        Get list of files in repository with specific extensions
        """
        if extensions is None:
            extensions = ['.txt', '.md', '.yml', '.yaml', '.json', '.sub', '.conf']

        try:
            repo_obj = self.github.get_repo(repo['full_name'])
            files = []

            def get_files_recursive(contents, path=""):
                for content_file in contents:
                    if content_file.type == "dir":
                        try:
                            get_files_recursive(content_file.get_contents(""), content_file.path)
                        except:
                            continue
                    else:
                        if any(content_file.name.endswith(ext) for ext in extensions):
                            files.append({
                                'name': content_file.name,
                                'path': content_file.path,
                                'download_url': content_file.download_url,
                                'size': content_file.size
                            })

            try:
                get_files_recursive(repo_obj.get_contents(""))
            except:
                pass

            return files

        except Exception as e:
            print(f"Error getting files for {repo['full_name']}: {e}")
            return []
