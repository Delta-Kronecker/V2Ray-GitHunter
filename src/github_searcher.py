"""
GitHub Searcher Module
Searches GitHub for proxy configuration collector repositories
"""

import os
import time
from typing import List, Dict, Set
from github import Github
from github.Repository import Repository


class GitHubSearcher:
    def __init__(self, token: str):
        self.github = Github(token)
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

    def search_repositories(self, max_results_per_search: int = 3) -> List[Dict]:
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
                    try:
                        repos = self.github.search_repositories(
                            query=query,
                            sort="stars",
                            order="desc"
                        )

                        count = 0
                        for repo in repos:
                            if count >= max_results_per_search:
                                break

                            repo_id = f"{repo.owner.login}/{repo.name}"
                            if repo_id not in seen_repos:
                                seen_repos.add(repo_id)

                                repo_info = {
                                    'name': repo.name,
                                    'full_name': repo.full_name,
                                    'owner': repo.owner.login,
                                    'description': repo.description or '',
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

                                all_repos.append(repo_info)
                                count += 1

                        print(f"Found {count} repositories for query: {query}")

                        # Rate limiting
                        time.sleep(2)

                    except Exception as e:
                        print(f"Error searching with query '{query}': {e}")
                        continue

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
