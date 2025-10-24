"""
Proxy Filter Module
Filters and categorizes proxy protocol links
"""

import re
import requests
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse


class ProxyFilter:
    def __init__(self):
        # Proxy protocols
        self.proxy_protocols = {
            'ss': ['ss://'],
            'shadowsocks': ['ss://', 'shadowsocks'],
            'vless': ['vless://'],
            'vmess': ['vmess://'],
            'trojan': ['trojan://'],
            'hy2': ['hy2://', 'hysteria2://'],
            'hysteria': ['hysteria://'],
            'v2ray': ['v2ray://']
        }

        # Keywords for merge/subscription files
        self.merge_keywords = [
            'all', 'merge', 'merged', 'subscription', 'sub', 'collection',
            'aggregate', 'combined', 'complete', 'total', 'full'
        ]

        # File extensions for config files
        self.config_extensions = ['.txt', '.sub', '.conf', '.yaml', '.yml', '.json']

        # Common patterns for proxy config URLs
        self.proxy_url_patterns = [
            r'.*/sub/.*\.txt$',
            r'.*/config.*\.txt$',
            r'.*/v2ray.*\.txt$',
            r'.*/ss.*\.txt$',
            r'.*/vmess.*\.txt$',
            r'.*/vless.*\.txt$',
            r'.*/trojan.*\.txt$',
            r'.*/hy2.*\.txt$',
            r'.*/shadowsocks.*\.txt$',
            r'.*/all.*\.txt$',
            r'.*/merge.*\.txt$',
            r'.*/merged.*\.txt$',
            r'.*/subscription.*\.txt$',
            r'.*/sub_.*\.txt$',
            r'.*All_Configs.*\.txt$',
            r'.*sub_merge.*\.txt$'
        ]

    def is_proxy_protocol_link(self, url: str) -> Tuple[bool, str]:
        """
        Check if URL contains proxy protocol
        Returns (is_proxy, protocol_type)
        """
        url_lower = url.lower()

        for protocol, patterns in self.proxy_protocols.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return True, protocol

        return False, ''

    def is_merge_subscription_link(self, url: str) -> bool:
        """
        Check if URL is a merge/subscription file
        """
        url_lower = url.lower()

        # Check for merge keywords
        for keyword in self.merge_keywords:
            if keyword in url_lower:
                return True

        # Check against URL patterns
        for pattern in self.proxy_url_patterns:
            if re.match(pattern, url_lower):
                return True

        return False

    def is_config_file(self, url: str) -> bool:
        """
        Check if URL points to a config file
        """
        url_lower = url.lower()

        # Check file extensions
        for ext in self.config_extensions:
            if url_lower.endswith(ext):
                return True

        # Check if it's a raw GitHub file with config-like name
        if 'raw.githubusercontent.com' in url_lower:
            filename = url_lower.split('/')[-1]
            for keyword in self.merge_keywords + ['config', 'proxy', 'node', 'list']:
                if keyword in filename:
                    return True

        return False

    def categorize_link(self, url: str) -> Dict:
        """
        Categorize a link based on its content
        """
        result = {
            'url': url,
            'is_proxy_protocol': False,
            'protocol_type': '',
            'is_merge_subscription': False,
            'is_config_file': False,
            'category': 'other'
        }

        url_lower = url.lower()

        # Check for proxy protocols
        is_proxy, protocol = self.is_proxy_protocol_link(url)
        if is_proxy:
            result['is_proxy_protocol'] = True
            result['protocol_type'] = protocol
            result['category'] = 'proxy_protocol'

        # Check for merge/subscription files
        if self.is_merge_subscription_link(url):
            result['is_merge_subscription'] = True
            if result['category'] == 'other':
                result['category'] = 'merge_subscription'

        # Check for config files
        if self.is_config_file(url):
            result['is_config_file'] = True
            if result['category'] == 'other':
                result['category'] = 'config_file'

        # Special categorization for raw GitHub files
        if 'raw.githubusercontent.com' in url_lower:
            if result['category'] == 'other':
                result['category'] = 'raw_file'

        return result

    def filter_links(self, links: List[str]) -> Dict[str, List[Dict]]:
        """
        Filter and categorize all links
        """
        categories = {
            'proxy_protocol': [],
            'merge_subscription': [],
            'config_file': [],
            'raw_file': [],
            'other': []
        }

        for link in links:
            categorized = self.categorize_link(link)
            categories[categorized['category']].append(categorized)

        return categories

    def get_high_priority_links(self, links: List[str]) -> List[Dict]:
        """
        Get high priority links (proxy protocols + merge/subscription files)
        """
        high_priority = []

        for link in links:
            categorized = self.categorize_link(link)
            if (categorized['is_proxy_protocol'] or
                categorized['is_merge_subscription'] or
                (categorized['is_config_file'] and categorized['is_merge_subscription'])):
                high_priority.append(categorized)

        # Sort by priority
        priority_order = ['proxy_protocol', 'merge_subscription', 'config_file']
        high_priority.sort(key=lambda x: (
            priority_order.index(x['category']) if x['category'] in priority_order else 99
        ))

        return high_priority

    def extract_proxy_configs_from_content(self, content: str) -> List[str]:
        """
        Extract proxy configuration strings from content
        """
        proxy_configs = []

        # Regex patterns for different proxy protocols
        patterns = [
            r'ss://[^\s<>"\'`]+',
            r'vmess://[^\s<>"\'`]+',
            r'vless://[^\s<>"\'`]+',
            r'trojan://[^\s<>"\'`]+',
            r'hy2://[^\s<>"\'`]+',
            r'hysteria2?://[^\s<>"\'`]+',
            r'v2ray://[^\s<>"\'`]+'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            proxy_configs.extend(matches)

        return list(set(proxy_configs))  # Remove duplicates

    def validate_proxy_config(self, config: str) -> bool:
        """
        Basic validation of proxy configuration
        """
        try:
            # Check if it's a valid URL format
            if '://' not in config:
                return False

            protocol = config.split('://')[0].lower()
            if protocol not in self.proxy_protocols:
                return False

            # Basic structure validation
            if len(config) < 10:  # Minimum reasonable length
                return False

            return True

        except:
            return False

    def get_domain_from_url(self, url: str) -> str:
        """
        Extract domain from URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ''

    def group_links_by_domain(self, links: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group links by domain
        """
        domains = {}

        for link_info in links:
            domain = self.get_domain_from_url(link_info['url'])
            if domain:
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(link_info)

        return domains