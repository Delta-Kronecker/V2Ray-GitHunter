#!/usr/bin/env python3
"""
V2Ray GitHunter - Main Orchestrator
Searches GitHub for proxy configuration collectors and extracts relevant links
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.github_searcher import GitHubSearcher
from src.source_fetcher import SourceFetcher
from src.link_extractor import LinkExtractor
from src.output_generator import OutputGenerator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='V2Ray GitHunter - GitHub Proxy Configuration Collector')

    parser.add_argument('--max-results', type=int, default=100,
                       help='Maximum results per search query (default: 100)')
    parser.add_argument('--max-workers', type=int, default=10,
                       help='Maximum number of parallel workers (default: 10)')
    parser.add_argument('--cache-dir', type=str, default='cache',
                       help='Cache directory (default: cache)')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with limited results')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous run if available')

    return parser.parse_args()


def load_progress(cache_dir: str) -> Dict:
    """Load progress from previous run"""
    progress_file = os.path.join(cache_dir, 'progress.json')
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading progress: {e}")
    return {}


def save_progress(cache_dir: str, progress: Dict):
    """Save progress to file"""
    progress_file = os.path.join(cache_dir, 'progress.json')
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress, f)
    except Exception as e:
        print(f"Error saving progress: {e}")


def main():
    """
    Main execution function
    """
    # Parse arguments
    args = parse_arguments()

    # Test mode configuration
    if args.test_mode:
        args.max_results = 20
        args.max_workers = 3
        print("=== RUNNING IN TEST MODE ===")

    print("=== V2Ray GitHunter Started ===")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Configuration: max_results={args.max_results}, max_workers={args.max_workers}")

    # Get GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    try:
        # Load previous progress if resuming
        progress = {}
        if args.resume:
            progress = load_progress(args.cache_dir)
            print(f"Loaded previous progress: {progress}")

        # Step 1: Search GitHub repositories
        print("\n=== Step 1: Searching GitHub Repositories ===")
        searcher = GitHubSearcher(
            github_token,
            cache_dir=args.cache_dir,
            max_results_per_search=args.max_results
        )

        repositories = searcher.search_repositories()

        if not repositories:
            print("No repositories found")
            return

        print(f"Found {len(repositories)} repositories")

        # Step 2: Fetch repository sources
        print("\n=== Step 2: Fetching Repository Sources ===")
        fetcher = SourceFetcher(
            sources_dir="data/sources",
            cache_dir=args.cache_dir,
            max_workers=args.max_workers
        )

        repos_with_sources = fetcher.fetch_and_save_all_sources(repositories)

        if not repos_with_sources:
            print("No sources fetched")
            return

        print(f"Fetched sources for {len(repos_with_sources)} repositories")

        # Step 3: Extract links from sources
        print("\n=== Step 3: Extracting Links ===")
        extractor = LinkExtractor(links_dir="data/links")
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
            'configuration': {
                'max_results': args.max_results,
                'max_workers': args.max_workers,
                'test_mode': args.test_mode
            },
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

        # Save progress
        save_progress(args.cache_dir, {
            'last_run': datetime.now().isoformat(),
            'summary': summary
        })

        print("\n=== V2Ray GitHunter Completed Successfully ===")

        # Performance summary
        end_time = datetime.now()
        print(f"Total execution time: {end_time - datetime.fromisoformat(summary['timestamp'])}")

    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
