"""
Output Generator Module
Generates categorized output and uploads to GitHub
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from src.proxy_filter import ProxyFilter


class OutputGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.proxy_filter = ProxyFilter()
        os.makedirs(output_dir, exist_ok=True)

    def generate_categorized_output(self, repos_with_links: List[Dict]) -> Dict[str, Any]:
        """
        Generate categorized output with project information and links
        """
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_repositories': len(repos_with_links),
                'total_links': 0,
                'proxy_protocol_links': 0,
                'merge_subscription_links': 0,
                'config_files': 0
            },
            'repositories': [],
            'summary': {
                'by_protocol': {},
                'by_domain': {},
                'high_priority_links': []
            }
        }

        all_links = []
        all_proxy_links = []

        for repo in repos_with_links:
            if 'links' not in repo:
                continue

            # Filter and categorize links for this repository
            categorized_links = self.proxy_filter.filter_links(repo['links'])
            high_priority = self.proxy_filter.get_high_priority_links(repo['links'])

            repo_data = {
                'name': repo['name'],
                'full_name': repo['full_name'],
                'owner': repo['owner'],
                'html_url': repo['html_url'],
                'description': repo.get('description', ''),
                'stars': repo.get('stars', 0),
                'forks': repo.get('forks', 0),
                'language': repo.get('language'),
                'updated_at': repo.get('updated_at'),
                'search_keyword': repo.get('search_keyword', ''),
                'links_count': len(repo['links']),
                'categorized_links': {
                    'proxy_protocol': [link['url'] for link in categorized_links['proxy_protocol']],
                    'merge_subscription': [link['url'] for link in categorized_links['merge_subscription']],
                    'config_file': [link['url'] for link in categorized_links['config_file']],
                    'raw_file': [link['url'] for link in categorized_links['raw_file']],
                    'other': [link['url'] for link in categorized_links['other']]
                },
                'high_priority_links': [link['url'] for link in high_priority],
                'high_priority_count': len(high_priority)
            }

            output_data['repositories'].append(repo_data)

            # Update metadata
            output_data['metadata']['total_links'] += len(repo['links'])
            output_data['metadata']['proxy_protocol_links'] += len(categorized_links['proxy_protocol'])
            output_data['metadata']['merge_subscription_links'] += len(categorized_links['merge_subscription'])
            output_data['metadata']['config_files'] += len(categorized_links['config_file'])

            # Collect all links for summary
            all_links.extend(repo['links'])
            all_proxy_links.extend([link['url'] for link in high_priority])

        # Generate summary statistics
        output_data['summary']['high_priority_links'] = list(set(all_proxy_links))

        # Group by protocol
        for link_info in self.proxy_filter.filter_links(all_links)['proxy_protocol']:
            protocol = link_info['protocol_type']
            if protocol not in output_data['summary']['by_protocol']:
                output_data['summary']['by_protocol'][protocol] = 0
            output_data['summary']['by_protocol'][protocol] += 1

        # Group by domain
        domains = self.proxy_filter.group_links_by_domain(
            [self.proxy_filter.categorize_link(link) for link in all_links]
        )
        for domain, links in domains.items():
            output_data['summary']['by_domain'][domain] = len(links)

        return output_data

    def save_json_output(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Save output as JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"v2ray_githunter_results_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"JSON output saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving JSON output: {e}")
            return ""

    def save_csv_output(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Save output as CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"v2ray_githunter_results_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                header = [
                    'Repository Name', 'Full Name', 'Owner', 'URL', 'Description',
                    'Stars', 'Forks', 'Language', 'Updated At', 'Search Keyword',
                    'Total Links', 'Proxy Protocol Links', 'Merge Subscription Links',
                    'Config Files', 'High Priority Links', 'High Priority Count'
                ]
                writer.writerow(header)

                # Write data
                for repo in data['repositories']:
                    row = [
                        repo['name'],
                        repo['full_name'],
                        repo['owner'],
                        repo['html_url'],
                        repo['description'],
                        repo['stars'],
                        repo['forks'],
                        repo['language'],
                        repo['updated_at'],
                        repo['search_keyword'],
                        repo['links_count'],
                        len(repo['categorized_links']['proxy_protocol']),
                        len(repo['categorized_links']['merge_subscription']),
                        len(repo['categorized_links']['config_file']),
                        '; '.join(repo['high_priority_links'][:5]),  # Limit to first 5 links
                        repo['high_priority_count']
                    ]
                    writer.writerow(row)

            print(f"CSV output saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving CSV output: {e}")
            return ""

    def save_links_only(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Save only the high priority links to a text file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"high_priority_links_{timestamp}.txt"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# V2Ray GitHunter - High Priority Proxy Links\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Total Links: {len(data['summary']['high_priority_links'])}\n\n")

                for link in data['summary']['high_priority_links']:
                    f.write(f"{link}\n")

            print(f"Links file saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving links file: {e}")
            return ""

    def generate_markdown_report(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate a markdown report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"v2ray_githunter_report_{timestamp}.md"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# V2Ray GitHunter Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Summary
                f.write("## Summary\n\n")
                f.write(f"- **Total Repositories:** {data['metadata']['total_repositories']}\n")
                f.write(f"- **Total Links:** {data['metadata']['total_links']}\n")
                f.write(f"- **Proxy Protocol Links:** {data['metadata']['proxy_protocol_links']}\n")
                f.write(f"- **Merge Subscription Links:** {data['metadata']['merge_subscription_links']}\n")
                f.write(f"- **Config Files:** {data['metadata']['config_files']}\n\n")

                # Protocol distribution
                if data['summary']['by_protocol']:
                    f.write("### Protocol Distribution\n\n")
                    for protocol, count in data['summary']['by_protocol'].items():
                        f.write(f"- **{protocol.upper()}:** {count}\n")
                    f.write("\n")

                # Top repositories
                f.write("## Top Repositories\n\n")
                top_repos = sorted(data['repositories'], key=lambda x: x['high_priority_count'], reverse=True)[:20]

                for repo in top_repos:
                    f.write(f"### [{repo['full_name']}]({repo['html_url']})\n\n")
                    f.write(f"**Stars:** {repo['stars']} | **Forks:** {repo['forks']} | **Language:** {repo.get('language', 'N/A')}\n\n")
                    if repo['description']:
                        f.write(f"{repo['description']}\n\n")
                    f.write(f"**High Priority Links:** {repo['high_priority_count']}\n\n")

                    if repo['high_priority_links']:
                        f.write("**Links:**\n")
                        for link in repo['high_priority_links'][:10]:  # Show first 10 links
                            f.write(f"- {link}\n")
                        if len(repo['high_priority_links']) > 10:
                            f.write(f"- ... and {len(repo['high_priority_links']) - 10} more\n")
                        f.write("\n")

                    f.write("---\n\n")

            print(f"Markdown report saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving markdown report: {e}")
            return ""

    def generate_all_outputs(self, repos_with_links: List[Dict]) -> List[str]:
        """
        Generate all output formats
        """
        data = self.generate_categorized_output(repos_with_links)

        files_created = []

        # Generate JSON
        json_file = self.save_json_output(data)
        if json_file:
            files_created.append(json_file)

        # Generate CSV
        csv_file = self.save_csv_output(data)
        if csv_file:
            files_created.append(csv_file)

        # Generate links only
        links_file = self.save_links_only(data)
        if links_file:
            files_created.append(links_file)

        # Generate markdown report
        md_file = self.generate_markdown_report(data)
        if md_file:
            files_created.append(md_file)

        return files_created