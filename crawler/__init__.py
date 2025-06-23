"""
Crawler Package - Maintains backward compatibility
"""

from .base_crawler import BaseCrawler

### Backward compatibility - expose the BaseCrawler as Crawler
Crawler = BaseCrawler