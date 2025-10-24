#!/usr/bin/env python3
"""
V2Ray GitHunter - Main Orchestrator
Searches GitHub for proxy configuration collectors and extracts relevant links
"""

import os
import sys
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.github_searcher import GitHubSearcher
from src.source_fetcher import SourceFetcher
from src.link_extractor import LinkExtractor
from src.output_generator import OutputGenerator


def main():
    """
    Main execution function
    """
    print("=== V2Ray GitHunter Started ===")
    print(f"Started at: {datetime.now().isoformat()}")

    # Get GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    try:
        # Step 1: Search GitHub repositories
        print("\n=== Step 1: Searching GitHub Repositories ===")
        searcher = GitHubSearcher(github_token)
        repositories = searcher.search_repositories(max_results_per_search=100)

        if not repositories:
            print("No repositories found")
            return

        print(f"Found {len(repositories)} repositories")

        # Step 2: Fetch repository sources
        print("\n=== Step 2: Fetching Repository Sources ===")
        fetcher = SourceFetcher()
        repos_with_sources = fetcher.fetch_and_save_all_sources(repositories)

        if not repos_with_sources:
            print("No sources fetched")
            return

        print(f"Fetched sources for {len(repos_with_sources)} repositories")

        # Step 3: Extract links from sources
        print("\n=== Step 3: Extracting Links ===")
        extractor = LinkExtractor()
        repos_with_links = extractor.extract_links_from_all_sources(repos_with_sources)

        if not repos_with_links:
            print("No links extracted")
            return

        print(f"Extracted links from {len(repos_with_links)} repositories")

        # Step 4: Generate outputs
        print("\n=== Step 4: Generating Outputs ===")
        generator = OutputGenerator()
        output_files = generator.generate_all_outputs(repos_with_links)

        if output_files:
            print(f"\nGenerated {len(output_files)} output files:")
            for file in output_files:
                print(f"  - {file}")
        else:
            print("No output files generated")

        # Step 5: Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_repositories_found': len(repositories),
            'sources_fetched': len(repos_with_sources),
            'links_extracted': len(repos_with_links),
            'output_files': output_files
        }

        summary_file = 'output/summary.json'
        os.makedirs('output', exist_ok=True)
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")
        print("\n=== V2Ray GitHunter Completed Successfully ===")

    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()