import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import sqlite3
import threading
import re
import time
from database_config import get_db_path
import urllib.parse
import json

from .url_mapping import get_crawler_method

class CustomHTTPAdapter(HTTPAdapter):
    def __init__(self, socket_options=None, *args, **kwargs):
        self.socket_options = socket_options
        super(CustomHTTPAdapter, self).__init__(*args, **kwargs)
        
    def init_poolmanager(self, *args, **kwargs):
        if self.socket_options:
            kwargs["socket_options"] = self.socket_options
        return super(CustomHTTPAdapter, self).init_poolmanager(*args, **kwargs)

class BaseCrawler:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path is not None else get_db_path()
        self.thread_local = threading.local()
        self.visited_URLs = set()
        self.results = []
        self.ostschweiz_locations = self.get_ostschweiz_locations()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.4',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
    
    
    def _get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.thread_local, 'connection'):
            self.thread_local.connection = sqlite3.connect(self.db_path)
        return self.thread_local.connection
    
    def _close_connection(self):
        """Close the thread-local connection if it exists"""
        if hasattr(self.thread_local, 'connection'):
            self.thread_local.connection.close()
            del self.thread_local.connection
        
    
    def crawl(self, start_url: str, keywords: list[str], max_pages: int = 30):
        all_content = []
        current_url = start_url
        page_count = 1

        print("\n" + "="*60)
        print(f"Starting crawler with keywords: {', '.join(keywords)}")
        print("="*60)

        while current_url and page_count <= max_pages:
            print(f"\nCrawling page {page_count}: {current_url}")

            try:
                # Get crawler method for URL
                crawler_method = get_crawler_method(current_url)
                if crawler_method:
                    page_content, next_url = crawler_method(self, current_url, keywords)
                    if page_content:
                        all_content.extend(page_content)

                    if next_url and next_url != current_url:
                        current_url = next_url
                        page_count += 1
                    else:
                        current_url = None
                else:
                    print(f"No crawler found for URL: {current_url}")
                    return None

            except Exception as e:
                print(f"Error during crawl: {e}")
                current_url = None
            finally:
                self._close_connection()

        print("\n" + "="*60)
        print(f"Crawling completed - Found {len(all_content)} matching jobs")
        print("="*60)

        if all_content:
            for i, job in enumerate(all_content, 1):
                print(f"\nJob {i}:")
                print("-"*30)
                print(f"Title:    {job['title']}")
                print(f"Company:  {job.get('company', 'Not specified')}")
                print(f"Location: {job.get('location', 'Not specified')}")
                print(f"Link:     {job['link']}")
        else:
            print("\nNo matching jobs found.")

        print("\n" + "="*60)
        print("End of results")
        print("="*60)

        return all_content
    
    
    def get_ostschweiz_locations(self):
        """Get all Ostschweiz municipalities from the database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT ortschaftsname, kanton FROM localities""")
            ostschweiz_locations = cursor.fetchall()
            return set([location[0].lower() for location in ostschweiz_locations])
        except Exception as e:
            print(f"Error during extraction: {e}")
            return set()
        
        
    def is_location_in_ostschweiz(self, location):
        """Check if a location is in Ostschweiz"""
        print(f"Checking location: {location}")
        location_lower = location.lower()
        for loc_name in self.ostschweiz_locations:
            if loc_name in location.lower():
                if loc_name in location_lower:
                    # Check if the matched municipality is a standalone word
                    if re.search(r'\b{}\b'.format(re.escape(loc_name)), location_lower):
                        print(f"Location {location} is in Ostschweiz")
                        return True
                    else:
                        print(f"Skipping partial match: {loc_name} in {location}")

        print(f"Location {location} is not in Ostschweiz")
        return False
    
        
    def is_it_job(self, title):
        """Check if a job title is an IT job"""
        it_keywords = [
            'informatik',
            'software',
            'entwickler',
            'developer',
            'programmierer',
            'engineer',
            'devops',
            'cloud',
            'network',
            'storage',
            'cyber',
            'application',
            'applikation',
            'ict',
            'systemadministrator',
            'system',
            'digital',
            'consult',
            'datenbank',
            'frontend',
            'backend',
            'fullstack',
            'consultant',
            'consulting',
            'it',
            'support',
        ]

        title_lower = title.lower()

        for keyword in it_keywords:
            if keyword == 'it':
                if re.search(r'\bit\b', title_lower):
                    return True
            else:
                if keyword in title_lower:
                    return True

        return False
    
    
    def __del__(self):
        """Cleanup when instance is destroyed"""
        self._close_connection()