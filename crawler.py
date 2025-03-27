import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from bs4 import Tag
import sqlite3
import threading
import re
import time
from database_config import get_db_path
import urllib.parse
import json


class CustomHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        # Remove the 'br' encoding from Accept-Encoding
        if 'Accept-Encoding' in request.headers:
            request.headers['Accept-Encoding'] = 'gzip, deflate'
        return super().send(request, **kwargs)


class Crawler:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path is not None else get_db_path()
        self.thread_local = threading.local()
        self.visited_URLs = set()
        self.results = []
        self.ostschweiz_locations = self.get_ostschweiz_locations()
        
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
        """Main crawl function that handles multiple pages"""
        all_content = []
        current_url = start_url
        page_count = 1
        
        print("\n" + "="*60)
        print(f"Starting crawler with keywords: {', '.join(keywords)}")
        print("="*60)
        
        while current_url and page_count <= max_pages:
            print(f"\nCrawling page {page_count}: {current_url}")
            
            try:
                ### Debug prints to see which condition is matched
                print("Checking URL")
                ### Crawl current page
                if "benedict.ch" in current_url:
                    print(f"benendict.ch: {'benedict.ch' in current_url}")
                    page_content, next_url = self.crawl_benedict(current_url, keywords)
                elif "vantage.ch" in current_url:
                    print(f"vantage.ch: {'vantage.ch' in current_url}")
                    page_content, next_url = self.crawl_vantage(current_url, keywords)
                elif "bzwu.ch" in current_url:
                    print(f"bzwu.ch: {'bzwu.ch' in current_url}")
                    page_content, next_url = self.crawl_bzwu(current_url, keywords)
                elif "ffhs.ch" in current_url:
                    print(f"ffhs.ch: {'ffhs.ch' in current_url}")
                    page_content, next_url = self.crawl_ffhs(current_url, keywords)
                elif "fhgr.ch" in current_url:
                    print(f"fhgr.ch: {'fhgr.ch' in current_url}")
                    page_content, next_url = self.crawl_fhgr(current_url, keywords)
                elif any(string in current_url for string in ['arbeitgeber-kanton-stgallen', 'umantis.com']):
                    print(f"gbssg: {any(string in current_url for string in ['arbeitgeber-kanton-stgallen', 'umantis.com'])}")
                    page_content, next_url = self.crawl_gbssg(current_url, keywords)
                elif "ipso.ch" in current_url:
                    print(f"ipso.ch: {'ipso.ch' in current_url}")
                    page_content, next_url = self.crawl_ipso(current_url, keywords)
                elif "phsg.ch" in current_url:
                    print(f"phsg.ch: {'phsg.ch' in current_url}")
                    page_content, next_url = self.crawl_phsg(current_url, keywords)
                elif "jobs-ost.ch" in current_url:
                    print(f"jobs-ost.ch: {'jobs-ost.ch' in current_url}")
                    page_content, next_url = self.crawl_ost(current_url, keywords)
                elif "swissengineering.ch" in current_url:
                    print(f"swissengineering.ch: {'swissengineering.ch' in current_url}")
                    page_content, next_url = self.crawl_swissengineering(current_url, keywords)
                elif "startfeld" in current_url:
                    print(f"innovationspark-ost.ch: {'startfeld' in current_url}")
                    page_content, next_url = self.crawl_innovationspark(current_url, keywords)
                elif "rheintalcom" in current_url:
                    print(f"rheintal.com: {'rheintalcom' in current_url}")
                    page_content, next_url = self.crawl_rheintal(current_url, keywords)
                elif "digitalliechtenstein" in current_url:
                    print(f"digitalliechtenstein.com: {'digitalliechtenstein' in current_url}")
                    page_content, next_url = self.crawl_digitalliechtenstein(current_url, keywords)
                elif "eastdigital" in current_url:
                    print(f"eastdigital: {'eastdigital' in current_url}")
                    page_content, next_url = self.crawl_eastdigital(current_url, keywords)
                elif "inside-it.ch" in current_url:
                    print(f"inside-it.ch: {'inside-it' in current_url}")
                    page_content, next_url = self.crawl_inside_it(current_url, keywords)
                elif "abacus" in current_url:
                    print(f"Abacus.ch: {'abacus' in current_url}")
                    page_content, next_url = self.crawl_abacus(current_url, keywords)
                elif "STSG" in current_url:
                    print(f"STSG.ch: {'STSG' in current_url}")
                    page_content, next_url = self.crawl_STSG(current_url, keywords)
                elif "valantic" in current_url:
                    print(f"valantic.ch: {'valantic' in current_url}")
                    page_content, next_url = self.crawl_valantic(current_url, keywords)
                elif 'abraxas' in current_url:
                    print(f"abraxas.ch: {'abraxas' in current_url}")
                    page_content, next_url = self.crawl_abraxas(current_url, keywords)
                elif 'buhlergroup' in current_url:
                    print(f"buhlergroup.com: {'buhlergroup' in current_url}")
                    page_content, next_url = self.crawl_buehler(current_url, keywords)
                elif 'dualoo' in current_url:
                    print(f"egeli-informatik.ch: {'egeli' in current_url}")
                    page_content, next_url = self.crawl_egeli(current_url, keywords)
                elif 'h-och.ch' in current_url:
                    print(f"h-och.ch: {'h-och' in current_url}")
                    page_content, next_url = self.crawl_hoch(current_url, keywords, page_count)
                elif 'inventx' in current_url:
                    print(f"inventx.ch: {'inventx' in current_url}")
                    page_content, next_url = self.crawl_inventx(current_url, keywords)
                elif 'kms-ag' in current_url:
                    print(f"kms-ag.ch: {'kms-ag' in current_url}")
                    page_content, next_url = self.crawl_kms(current_url, keywords)
                elif 'hexagon.com' in current_url:
                    print(f"hexagon.com: {'hexagon.com' in current_url}")
                    page_content, next_url = self.crawl_hexagon(current_url, keywords)
                elif 'ohws.prospective.ch' in current_url:
                    print(f"API von Raiffeisen Schweiz: {'ohws.prospective.ch' in current_url}")
                    page_content, next_url = self.crawl_raiffeisen(current_url, keywords)
                elif 'join.sfs.com' in current_url:
                    print(f"SFS Group: {'join.sfs.com' in current_url}")
                    page_content, next_url = self.crawl_sfs(current_url, keywords)
                elif 'umantis.com' in current_url:
                    print(f"Umantis: {'umantis.com' in current_url}")
                    page_content, next_url = self.crawl_umantis(current_url, keywords)
                elif 'acreo.ch' in current_url:
                    print(f"acreo consulting: {'acreo consulting' in current_url}")
                    page_content, next_url = self.crawl_acreo(current_url, keywords)
                elif 'all-consulting.ch' in current_url:
                    print(f"All Consulting: {'all-consulting.ch' in current_url}")
                    page_content, next_url = self.crawl_allconsulting(current_url, keywords)
                elif 'aproda.ch' in current_url:
                    print(f"Aproda: {'aproda.ch' in current_url}")
                    page_content, next_url = self.crawl_aproda(current_url, keywords)
                elif 'zootsolutions' in current_url:
                    print(f"Zoot Solutions: {'zootsolutions' in current_url}")
                    page_content, next_url = self.crawl_zoot(current_url, keywords)
                else:
                    print(f"Unknown URL: {current_url}")
                    return
                    
                all_content.extend(page_content)
                
                ### Prepare for next page
                if next_url and next_url != current_url:
                    current_url = next_url
                    page_count += 1
                else:
                    current_url = None
        
            except Exception as e:
                print(f"Error druing crawl: {e}")
                current_url = None
            finally:
                self._close_connection()
                
        
        ### Print final result nicely formatted
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
            'digital',
            'consult',
        ]
        return any(keyword.lower() in title.lower() for keyword in it_keywords)
    
    
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
    
    
    def crawl_benedict(self, url, keywords):
        """Crawl function for Benedict"""
        print(f"Crawling Benedict URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
        
            ### Then find all H2 elements in the div
            ### Extract parent element of listed jobs
            if soup:
                job_rows = soup.select('div#city4 h2.h3')
                print(f"Found {len(job_rows)} job listings")
                
                ### Extract title, link, company and location from each job row
                content = []
                for row in job_rows:
                    try:
                        ### Extract title and link
                        job_element = row.find('a')
                        if job_element and isinstance(job_element, Tag):
                            title = job_element.text.strip()
                            if job_element.has_attr('href'):
                                link = job_element.attrs['href']
                            link = job_element.get('href')

                        ### Check if any keyword is in the title
                        if any(keyword.lower() in title.lower() for keyword in keywords):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': 'Benedict',
                                'location': 'St. Gallen'
                            })
                            print(f"Found job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                    except Exception as e:
                        print(f"Error during extraction: {e}")

                print(content)
                # Extract next URL
                next_url = None
                print(f"Found {len(content)} jobs")
                return content or [], next_url or None
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_vantage(self, url, keywords):
        """Crawl function for Vantage"""
        print(f"Crawling Vantage URL: {url}")
        
        try:
            ### Crawl the URL
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            if soup:
                job_rows = soup.find_all('div', class_='infos')
                print(f"Found {len(job_rows)} job listings")
                
                ### Extract title, link, company and location from each job row
                content = []
                for row in job_rows:
                    try:
                        ### Extract title and link
                        title_element = row.find('span', class_='d-block w-100 border-bottom pb-3 mb-3')
                        title = title_element.text.strip()
                        link_element = row.find('a')
                        link = link_element['href'] if link_element else url
                        
                        bold_elements = row.find_all('b')
                        company = bold_elements[0].text.strip() if len(bold_elements) > 0 else 'Not specified'
                        location = bold_elements[2].text.strip() if len(bold_elements) > 2 else 'Not specified'

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                    
                    except Exception as e:
                        print(f"Error during extraction: {e}")

                print(content)
                # Extract next URL
                next_url = None
                print(f"Found {len(content)} jobs")
                return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_bzwu(self, url, keywords):
        """Crawl function for BZWU"""
        print(f"Crawling BZWU URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            advertisment = soup.find_all('div', class_='panel')
            print(f"Found {len(advertisment)} job advertisments")
            
            content = []
            ### Iterate through each advertisment
            for ad in advertisment:
                try:
                    ### job elements
                    job_rows = ad.find_all('a')
                    print(f"Found {len(job_rows)} job listings")

                    ### Extract title, link, company and location from each job row
                    for row in job_rows:
                        try:
                            ### Extract title and link
                            title = row.text.strip() if row else 'Not specified'
                            link = row['href'] if row else url
                            
                            ### Check if any keyword is in the title
                            if any(keyword.lower() in title.lower() for keyword in keywords):
                                content.append({
                                    'title': title,
                                    'link': link,
                                    'company': 'BZWU',
                                    'location': 'Wil-Uzwil'
                                })
                                print(f"Found matching job: {title}")
                            else:
                                print(f"Skipping non-matching job: {title}")

                        except Exception as e:
                            print(f"Error during extraction: {e}")
                    print(content)
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            ### Extract next URL
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_ffhs(self, url, keywords):
        """Crawl function for FFHS"""
        print(f"Crawling FFHS URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='panel panel-default')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Print each job element for debugging
                    #print("\nJob element found:")
                    #print(row.prettify())
                    
                    ### Extract title
                    title = row.find('h3', class_='panel-title').text.strip()
                    #print(f"Title: {title}")
                    ### Extract location
                    location = ""
                    description = row.find('div', class_='panel-body')
                    if description:
                        ### Look for a location in the description that is in Ostschweiz
                        for p in description.find_all('p'):
                            for loc_name in self.ostschweiz_locations:
                                if loc_name in p.text.lower():
                                    location = loc_name
                    
                    ### Check if any keyword is in the title and location contains a municipality in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': url,
                            'company': 'FFHS',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                                                          
    
    def crawl_fhgr(self, url, keywords):
        """Crawl function for FHGR"""
        print(f"Crawling FHGR URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Print each job element for debugging
                    #print("\nJob element found:")
                    #print(row.prettify())
                    
                    ### Extract title, link and location
                    title_element = row.find('a', class_='HSTableLinkSubTitle')
                    title = title_element.get('aria-label')
                    print(f"Title: {title}")
                    
                    link_element = title_element['href'] if title_element else url
                    link = "https://jobs.fhgr.ch" + link_element
                    
                    location_element = row.find('span', class_='tableaslist_subtitle tableaslist_element_1152495')
                    location = location_element.text.replace('|', '').strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'FHGR',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                    
    
    def crawl_gbssg(self, url, keywords):
        """Crawl function for gbssg"""
        print(f"Crawling gbssg URL: {url}")
        try:
            response = requests.get(url)
            
            ### Get the actual URL from the response
            actual_url = response.url
            print(f"Actual URL: {actual_url}")
            
            ### Check if we're being redirected back to page 1
            if 'tc1152481=p1' in actual_url and 'tc1152481=p1' not in url:
                print(f"Redirected back to page 1. Stopping the crawl.")
                return [], None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title, link, company and location
                    title_element = row.find('a', class_='HSTableLinkSubTitle')
                    title = title_element.get('aria-label')
                    print(f"Title: {title}")
                    
                    link_element = title_element['href'] if title_element else url
                    link = "https://recruitingapp-2800.umantis.com" + link_element
                    
                    location_element = row.find('span', class_='tableaslist_subtitle tableaslist_element_1152495')
                    location = location_element.text.replace('|', '').strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'Kanton St.Gallen',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### Check if next page is available
            current_page_match = re.search(r'tc1152481=p(\d+)', url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
                ### Construct next page URL
                next_page = current_page + 1
                base_url = url.split('tc1152481=')[0] ### Get the base URL
                token = url.split('_search_token1152481=')[1].split('#')[0] ### Get the token
                next_url = f"{base_url}tc1152481=p{next_page}&_search_token1152481={token}#connectortable_1152481" ### Construct the next URL
                print(f"Moving to page {next_page}")
            else:
                next_url = None
                print("No page number found in URL")

            print(f"Found {len(content)} jobs")
            return content, next_url
            

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_ipso(self, url, keywords):
        """Crawl function for ipso"""
        print(f"Crawling ipso URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='beg-job-block node')
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title, link and location
                    title = row.find('p', class_='beg-job-block__title').text.strip()
                    link = row['href']
                    location = row.find('span', class_='beg-job-block__city').text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'ipso',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    
    def crawl_phsg(self, url, keywords):
        """Crawl function for Pädagogische Hochschule St. Gallen"""
        print(f"Crawling PHSG URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify()[:500])

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('tr', class_='alternative_1')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Get the first column (td with class real_table_col1)
                    col = row.find('td', class_='real_table_col1')
                    if col:
                        ### Extract title and link
                        title = col.find('div', id='job_311').text.strip()
                        link_element = col.find('a')
                        link = link_element['href'] if link_element else url
                        
                        ### Check if any keyword is in the title
                        if any(keyword.lower() in title.lower() for keyword in keywords):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': 'Pädagogische Hochschule St. Gallen',
                                'location': 'St. Gallen'
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")

            print(content)
            # Extract next URL
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    def crawl_ost(self, url, keywords):
        """Crawl function for jobs-ost.ch"""
        print(f"Crawling jobs-ost URL: {url}")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='joboffer_container')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Extract title and link
                    title_element = row.find('a', target='_self')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    link = title_element['href'] if title_element else url
                    
                    ### Extract location
                    location_element = row.find('div', class_='joboffer_informations joboffer_box')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'OST',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")

            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    def crawl_swissengineering(self, url, keywords):
        """method to crawl swissengineering.ch"""
        print(f"Crawling swissengineering URL: {url}")
        try:
            response = requests.get(url)
            data = response.json() ### get the whole json data
            job_rows = data.get('jobs', []) ### get the jobs array safely
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    title = job.get('title', '')
                    link = "https://www.swissengineering.ch" + job.get('link', '')
                    
                    ### Extract location
                    location = job.get('worklocation', '')
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'SwissEngineering',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue

            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_innovationspark(self, url, keywords):
        """Crawl function for innovationspark-ost.ch"""
        print(f"Crawling innovationspark-ost URL: {url}")
        try:
            ### Set up headers to mimic a browser
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
            }
            
            ### Make a request to the URL
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print("Initial response status:", response.status_code)
            #print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href'] if link_element else url
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    def crawl_rheintal(self, url, keywords):
        """Crawl function for rheintal.com"""
        print(f"Crawling rheintal.com URL: {url}")
        try:
            ### Set up headers to mimic a browser
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
            }
            
            ### request to the URL
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print("Initial response status:", response.status_code)
            #print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href'] if link_element else url
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if(any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title)):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_digitalliechtenstein(self, url, keywords):
        """Crawl function for digitalliechtenstein.ch"""
        print(f"Crawling digitalliechtenstein URL: {url}")
        try:
            ### Set up headers to mimic a browser
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip()
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip()
                    
                    ### Extract Company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    def crawl_eastdigital(self, url, keywords):
        """Crawl function for eastdigital.ch"""
        print(f"Crawling eastdigital URL: {url}")
        try:
            ### Set up headers to mimic a browser
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            print("Initial response status:", response.status_code)
            print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip()
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip()
                    
                    ### Extract Company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_inside_it(self, url, keywords):
        """Crawl function for inside-it.ch"""
        print(f"Crawling inside-it URL: {url}")
        try:
            
            ### Set up a session with retries
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = CustomHTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            ### Set up headers to mimic a browser
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
            }
            
            time.sleep(2)
           
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status() ### Raise an exception for bad status codes
            
            response.encoding = 'utf-8' ### Force the encoding to utf-8

            ### Debug info
            #print("Response headers:", response.headers)
            #print("Content type:", response.headers.get('content-type'))
            #print("Content encoding:", response.headers.get('content-encoding'))

            
            ### parse with lxml
            soup = BeautifulSoup(response.content, 'lxml')
            #print(soup.prettify()[:500])
            
            ### Extract parent element of listed jobs
            list = soup.find('ul', class_='job_listings list-classic')
            if not list:
                print("No job listings container found")
                return [], None
            
            if isinstance(list, Tag):
                job_rows = list.find_all('li', class_='job_listing') ### get all job listings from the list container
            else:
                job_rows = []
                print("No job listings container found")
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('h3', class_='job-listing-loop-job__title')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('div', class_='job-location location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract Company
                    company_element = row.find('div', class_='job-listing-company company')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find('a', class_='next page-numbers')
            next_url = next_page_element['href'] if next_page_element and isinstance(next_page_element, Tag) else None
            print("Found next page element:", next_url)
            
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_abacus(self, url, keywords):
        """Crawl function for Abacus API"""
        print(f"Crawling Abacus API URL: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            ### Make the API request
            response = requests.get(url, headers=headers)

            ### Parse the response as a dictionary
            response_data = response.json()

            ### Check if 'html' key exists in the response
            if 'html' not in response_data:
                print("No HTML content found in the response")
                return [], None

            ### Parse the HTML content
            soup = BeautifulSoup(response_data['html'], 'html.parser')

            ### Look for job advertisement table or elements
            job_elements = soup.find_all('job-advertisement-table')

            content = []
            for job_element in job_elements:
                try:
                    ### Try to extract job data from the element's attributes
                    job_value = job_element.get('value', '')

                    ### URL decode the value
                    decoded_job_data = urllib.parse.unquote(job_value)

                    ### Parse the decoded job data
                    try:
                        jobs = json.loads(decoded_job_data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse job data: {decoded_job_data[:500]}")
                        continue

                    ### Process each job
                    for job in jobs:
                        title = job.get('JobTitle', 'No title')
                        location = job.get('u_b_jobs_xxx__userfield1', 'No location')
                        link = job.get('PublicationUrlAbacusJobPortal', '#')

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if (any(keyword.lower() in title.lower() for keyword in keywords) and 
                            self.is_location_in_ostschweiz(location)):

                            job_entry = {
                                'title': title,
                                'link': link,
                                'company': 'Abacus',
                                'location': location,
                            }

                            content.append(job_entry)
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                except Exception as e:
                    print(f"Error processing job element: {e}")

            ### No pagination for this specific API
            next_url = None

            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None

                    
                    
    def crawl_STSG (self, url, keywords):
        """Crawl Function for Stadt St. Gallen"""
        print(f'Crawling Stadt St. Gallen API URL: {url}')
        
        try:            
            ### Make the API request
            response = requests.get(url)
            
            ### Parse the response using utf-8-sig encoding to handle BOM
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                ### If standard JSON decoding fails, try with utf-8-sig
                data = json.loads(response.content.decode('utf-8-sig'))
            job_rows = data.get('jobs', []) ### get the jobs array safely
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### extract job details
                    title = job.get('title', {}).get('value', 'No title')
                    link = 'https://live.solique.ch/STSG/de/' + job.get('link', {})
                    company = job.get('company', {}).get('value', 'No company')
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz, then append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            Next_url = None
            
            print(f"Found {len(content)} jobs")
            return content, Next_url
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None
    
    
    
    def crawl_valantic(self, url, keywords):
        """Function to crawl Valantic"""
        print(f"Crawling Valantic URL: {url}")
        
        ### List of all the different URL endings
        url_endings = [
            'cloud-aws/',
            'artificial-intelligence/',
            'crm/',
            'data-analytics/',
            'digital-marketing',
            'digital-platforms-e-commerce/',
            'digital-strategy/',
            'fintech/',
            'financial-services/',
            'internet-of-things/',
            'sap/',
            'cyber-security/',
            'strategy-management-consulting/',
            'backend-development/',
            'devops/',
            'frontend-development/',
            'quality-testing/',
            'it-support/',
            'second-level-support/',
            'system-administration/',
        ]
        try:
            # Enhanced headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            content = []
            for ending in url_endings:
                response = requests.get(url + ending, headers=headers, timeout=10)
                
                ### Check if the response is successful
                response.raise_for_status()
                
                print(f"Response status for {url + ending}: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_rows = soup.find_all('a', class_="bg-white flex flex-col items-start w-full rounded pt-3.5 pb-4 px-5 pr-20 shadow-[0_10px_30px_0_rgba(0,0,0,0.08)] relative group z-10 hover:z-20")
                print(f"Found {len(job_rows)} job listings")
                for job in job_rows:
                    try:
                        ### Extract title
                        title = job.find('p', class_='text-2xl font-semibold group-hover:text-red').text.strip()
                        link = job['href']
                        location = job.find('li', class_='mt-1 text-base truncate text-black/40').text.strip()
                        company = 'Valantic'
                        
                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location                                
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                            
                    except Exception as e:
                        print(f"Error during extraction: {e}")
                       
            next_url = None 
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_abraxas(self, url, keywords):
        """Crawl function for Abraxas"""
        print(f"Crawling Abraxas URL: {url}")

        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }

            # Create a session to manage cookies
            session = requests.Session()

            # First request to get the cookie consent page
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"Initial response status: {response.status_code}")

            # Check if there's a cookie consent form
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for consent button
            consent_button = soup.select_one('.js-jf-yellow-rd-active.all-active.force--consent.show--consent')
            print(f"Cookie consent dialog detected: {consent_button is not None}")

            if consent_button:
                print("Handling cookie consent...")
                # Set cookies that would typically be set after accepting
                cookies = {
                    'cookieconsent_status': 'allow',
                    'cookiecategory_optional': 'allow',
                    'cookiecategory_analytical': 'allow',
                    'cookiecategory_marketing': 'allow'
                }

                for name, value in cookies.items():
                    session.cookies.set(name, value, domain='abraxas.ch')

                # Make another request to get the actual page content
                response = session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                print(f"Post-consent response status: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
            else:
                print("No cookie consent dialog detected")

            print(f"Final response status: {response.status_code}")

            # Print the page title to help debug
            page_title = soup.title.string if soup.title else "No title found"
            print(f"Page title: {page_title}")

            # Try different selectors that might match job listings
            job_selectors = [
                'article.teaser',
                'div.teaser',
                'li.teaser',
                'div.job-teaser',
                'div.career-teaser',
                'div.job-listing',
                'li.vacancy-item',
                'div.job-position',
                '.job-card',
                '.position-card',
                'a[href*="stelle"]',
                'a.job-link'
                'li.job-list__list-item is-visible'
            ]

            job_rows = []
            used_selector = None

            for selector in job_selectors:
                temp_rows = soup.select(selector)
                if temp_rows:
                    job_rows = temp_rows
                    used_selector = selector
                    print(f"Found {len(temp_rows)} job listings using selector: {selector}")
                    break
                
            if not job_rows:
                # Look for links containing job-related keywords
                print("Trying to find job links using text content...")
                all_links = soup.find_all('a')
                job_links = []
                for link in all_links:
                    link_text = link.get_text().lower()
                    if any(kw in link_text for kw in ['stelle', 'job', 'position', 'karriere', 'vacancies']):
                        job_links.append(link)

                if job_links:
                    job_rows = job_links
                    used_selector = "text-based job links"
                    print(f"Found {len(job_links)} text-based job links")

            print(f"Found {len(job_rows)} potential job listings using {used_selector if used_selector else 'no matching selector'}")

            # If still empty, dump a sample of the HTML to debug
            if not job_rows:
                print("No job listings found. HTML sample:")
                html_sample = soup.prettify()[:1000]
                print(html_sample)

            content = []
            for job in job_rows:
                try:
                    # Extract based on what selector matched
                    if used_selector == "text-based job links":
                        title = job.get_text(strip=True)
                        link = job.get('href', '')
                        if isinstance(link, str) and link and not (link.startswith('http://') or link.startswith('https://')):
                            link = urllib.parse.urljoin(url, link)
                        location = 'St. Gallen'  # Default location for Abraxas
                    else:
                        # Try to extract title using various potential selectors
                        title_element = job.select_one('h2, h3, h4, .title, .job-title')
                        title = title_element.get_text(strip=True) if title_element else job.get_text(strip=True)

                        # Try to extract link
                        link_element = job.select_one('a') or job if job.name == 'a' else None
                        link = link_element.get('href', '') if link_element else ''
                        if isinstance(link, str) and link and not (link.startswith('http://') or link.startswith('https://')):
                            link = urllib.parse.urljoin(url, link)

                        # Try to extract location
                        location_element = job.select_one('.location, .job-location, .place')
                        location = location_element.get_text(strip=True) if location_element else 'St. Gallen'

                    company = 'Abraxas'

                    print(f"Extracted job: Title={title}, Location={location}")

                    # Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")

            next_url = None
            for job in content:
                if job['link'] == "https://www.abraxas.ch/de/karriere/lehrstellen-und-praktika":
                    print("Found the URL of Lehrstellen und Praktika")
                    next_url = job['link']
                    print(f"Next URL: {next_url}")
                    content.remove(job)
                    break
                
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_buehler(self, url, keywords):
        """Function to Crawl Buehler Group"""
        print(f"Crawling Buehler URL: {url}")
        
        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"Initial response status: {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all(lambda tag: tag.name == 'li' and 
                                                tag.has_attr('class') and
                                                'job-tile' in ' '.join(tag.get('class', [])) and
                                                'job-id' in ' '.join(tag.get('class', [])))
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    
                    title_element = (
                        job.find('a', class_=lambda c: c and 'jobTitle-lin' in c) or
                        job.find('a', class_=lambda c: c and 'job-title' in c) or
                        job.find('a', href=lambda h: h and '/job/' in h) or
                        job.find('a')                        
                    )
                    
                    if title_element:
                        title = title_element.get_text(strip=True)
                        
                        if title_element.name == 'a' and title_element.has_attr('href'):
                            link = title_element['href']

                            if not (link.startswith('http://') or link.startswith('https://')):
                                link = urllib.parse.urljoin('https://jobs.buhlergroup.com/', link)
                        else:
                            ### if title element is not a link, look for a link nearby
                            link_element = job.find('a')
                            if link_element and link_element.has_attr('href'):
                                link = link_element['href']
                                ### Make sure link is absolute
                                if not (link.startswith('http://') or link.startswith('https://')):
                                    link = urllib.parse.urljoin('https://jobs.buhlergroup.com/', link)
                            
                            else:
                                link = url ### if no link found, use the current URL
                        
                    ### try different ways to get locations
                    location_element = (
                        job.find('div', class_=lambda c: c and 'location' in c.lower()) or
                        job.find(string=lambda s: s and any(loc in s.lower() for loc in ['uzwil', 'st. gallen', 'st.gallen', 'wil', 'gossau']))
                    )
                    
                    if location_element:
                        if hasattr(location_element, 'text'):
                            location = location_element.get_text(strip=True)
                        else:
                            ### if the locatoin directly was found as string
                            location = str(location_element).strip()
                    else:
                        # If location not found in expected ways, try searching in all text of job element
                        job_text = job.get_text().lower()
                        for loc in ['uzwil', 'st. gallen', 'st.gallen', 'wil', 'gossau', 'appenzell']:
                            if loc in job_text:
                                location = loc.title()
                                break
                        else:
                            location = 'unknown'
                            
                    if location.startswith('Location'):
                        location = location[8:].strip()
                                            
                    company = 'Bühler'
                    
                    print(f"Extracted job: Title={title}, Location={location}")
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_egeli(self, url, keywords):
        """Fucntion to crawl Egeli Informatik"""
        print(f"Crawling Egleli Informatik URL: {url}")
        
        try:
            ### Set up headers to mimic a browser
            headers = {
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1', 
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            #job_rows = soup.find_all(lambda tag: tag.name == 'a' and 
            #                                    tag.has_attr('class') and
            #                                    'jobElement' in ' '.join(tag.get('class', [])) and
            #                                    'row' in ' '.join(tag.get('class', [])))
            job_rows = soup.find_all('a', class_='row jobElement pt-2 pb-2 text-decoration-none')
                
            print(f"Found {len(job_rows)} job listings")
            #if not job_rows:
                
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'Egeli Informatik'

                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    return [], None
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_hoch(self, url, keywords, page_count):
        """Function to crawl Hoch"""
        print(f"Crawling Hoch Health Ostschweiz URL: {url}")
        
        ### Retry parameters
        max_retries = 3
        retry_count = 0
        backoff_time = 2
        
        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'no-cache',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            job_rows = soup.find_all('tr', class_='data-row')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a', class_='jobTitle-link').text.strip()
                    link = 'https://jobs.h-och.ch' + job.find('a')['href']
                    location = job.find('span', class_='jobLocation').text.strip()
                    company = 'Hoch Health Ostschweiz'
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
                
            
            base_url = 'https://jobs.h-och.ch/search/'
            
            
            ### Find the link for the next page
            next_page_num = int(page_count) + 1
            next_page = soup.find('a', title=f'Seite {next_page_num}')
            if not next_page:
                print(f"No next page found. Last page reached.")
                next_page = None
                return content, next_page
            
            ### get url for the next page
            href_value = next_page['href'] if isinstance(next_page, Tag) and next_page.has_attr('href') else None
            next_url = base_url + href_value if isinstance(href_value, str) else None
            
            print(f'Moving to page {next_page_num}. Found next URL: {next_url}')
            
            print(f"Found {len(content)} jobs")
            return content, next_url

        except requests.Timeout as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = backoff_time * (2 ** (retry_count - 1)) # Exponential backoff
                print(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Max retries reached. Aborting...")
                return [], None 
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        

                    
    def crawl_inventx(self, url, keywords):
        """Function to crawl InventX"""
        print(f"Crawling InventX URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all(lambda tag: tag.name == 'div' and tag.has_attr('class') and 'row row-table' in ' '.join(tag.get('class', [])))     
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title = job.find('a').text.strip()
                link = job.find('a')['href']
                location = job.find('div', class_='inner').text.strip()
                company = 'InventX'

                ### Check if any keyword is in the title and location is in Ostschweiz
                if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_kms(self, url, keywords):
        """Function to crawl KMS"""
        print(f"Crawling KMS URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all('div', class_='job__content styled')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title_element = job.find('div', class_='job__title h4')
                title = title_element.find('strong').text.strip() if title_element else 'No title'
                link = 'https://www.kms-ag.ch/karriere/offene-jobs/'
                company = 'KMS'
                location_elements = job.find_all('p')
                ### iterate though each p element to find location
                for location_element in location_elements:
                    location_element.text.strip()
                    if 'matzingen' in location_element.text.lower():
                        location = 'Matzingen'
                
                ### Check if any keyword is in the title
                if any(keyword.lower() in title.lower() for keyword in keywords):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location,
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_hexagon(self, url, keywords):
        """Function ot crawl Hexagon / Leica Systems"""
        print(f"Crawling Hexagon URL: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            ### API request
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
            
            ### Check if the response has the excepted content
            if 'Results' not in data:
                print("No result found in API structure")
                return [], None
            
            job_rows = data['Results']
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    html_content = job.get('Html', '')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    ### Get the <a> element with URL and Title in it
                    a_element = soup.find('a')
                    if not a_element:
                        print('No <a> element found in job listing')
                        continue
                    
                    title = a_element.text.strip()
                    link = a_element['href'] if isinstance(a_element, Tag) and a_element.has_attr('href') else 'No link'
                    company = "Leica Geosystems"
                    job_url_div = soup.find('div', class_='job-url')
                    if job_url_div:
                        location = job_url_div.next_sibling.strip() if job_url_div and isinstance(job_url_div.next_sibling, str) else 'No location'

                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_raiffeisen(self, url, keywords):
        """Function to Crawl Raiffeisen Schweiz"""
        print(f"Crawling Raiffeisen Schweiz URL: {url}")
        
        try:
            ### Request the API page
            response = requests.get(url)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
            
            ### Check if the response has the expected content of listed jobs
            job_rows = data['jobs']
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job['title']
                    link = job['links']['directlink']
                    location = job['attributes']['arbeitsort'][0]
                    company = 'Raiffeisen Schweiz'

                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        ### printing what is not matching
                        print(f"Title: {title}, Location: {location}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_sfs(self, url, keywords):
        """Function to crawl SFS"""
        print(f"Crawling SFS URL: {url}")
        
        try:
            ### Setting up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='molecule-responsive-datalist-entry values-are-copytext')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('strong', class_='highlight-on-interaction').text.strip()
                    link = 'https://join.sfs.com' + job['href']
                    
                    ### Extract location and company
                    loc_com_elements = job.find('span', class_='column grid-width-5')
                    expanded_columns = loc_com_elements.find_all('span', class_='column-value')
                    location = expanded_columns[0].text.strip()
                    company = loc_com_elements.find('strong').text.strip()
                        
                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_umantis(self, url, keywords):
        """Function to crawl Umantis"""
        print(f"Crawling Umantis URL: {url}")
        
        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try: 
                    title = job.find('a', class_='HSTableLinkSubTitle').text.strip()
                    link = 'https://recruitingapp-9300.umantis.com/' + job.find('a', class_='HSTableLinkSubTitle')['href']
                    company = 'Abacus Umantis'

                    ### Extract location
                    if any(keyword.lower() and title.lower() for keyword in keywords) and self.is_it_job(title):
                        ### load the detailed job page to extract the location
                        load_job = requests.get(link, headers=headers)
                        load_job.raise_for_status()
                        job_soup = BeautifulSoup(load_job.content, 'html.parser')
                        
                        ### Check for location information in the <b> tag
                        location = None
                        is_st_gallen = False
                        
                        ### Looking for the <b> tag with the location
                        bold_elements = job_soup.find_all('b')
                        for b_elem in bold_elements:
                            text = b_elem.text.strip()
                            ### Check if this <b> tag mention a location
                            if 'Standort' in text or 'St. Gallen' in text:
                                location = text
                                if 'St. Gallen' in text:
                                    is_st_gallen = True
                                    break
                        
                        ### Onyly append the job if it's in St. Gallen
                        if is_st_gallen:
                            content.append({
                                'title': title,
                                'link': link,
                                'location': location,
                                'company': company
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs in St.Gallen")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_acreo(self, url, keywords):
        """Function to crawl Acreo"""        
        print(f"Crawling Acreo URL: {url}")
        
        try:
            ### set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_list = soup.find('ul', class_='grid-3')
            if job_list and isinstance(job_list, Tag):
                job_rows = job_list.find_all('li', class_='acreo-box-item')
            else:
                print("No valid job list found.")
                job_rows = []
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3').text.strip()
                    link = 'https://acreo.ch' + job.find('a')['href']
                    location = 'St. Gallen'
                    company = 'Acreo Consulting'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                           'title': title,
                           'link': link,
                           'location': location,
                           'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], next_page
        
    
    
    def crawl_allconsulting(self, url, keywords):
        """Function to crawl All Consulting"""
        print(f"Crawling All Consulting URL: {url}")
        
        try: 
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='link-arrow')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.text.strip()
                    link = 'https://all-consulting.ch' + job['href']
                    company = 'All Consulting'
                    
                    if 'St. Gallen' in title:
                        location = 'St. Gallen'
                    else:
                        location = 'unknown'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue

            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], next_page
            
     
    def crawl_aproda(self, url, keywords):
        """Function to crawl Aproda"""
        print(f"Crawling Aproda URL: {url}")
        
        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('article', class_='note')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3', class_='headline-five note-title').text.strip()
                    link = job.find('a', class_='button')['href']
                    company = 'Aproda'
                    location = 'St. Gallen / Rotkreuz'
                    
                    
                    
                    ### Check if any keyword is in the title, location is in ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_zoot(self, url, keywords):
        """Function to Craw Zoot Solutions"""
        print(f"Crawling Zoot Solutions URL: {url}")
        
        try:
            ### Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,de;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
            
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='story--zoot-item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h5', class_='title--h5-zoot').text.strip()
                    location = job.find('span', class_='story-location').text.strip()
                    link = url
                    company = 'Zoot Solutions'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                             
    
    def __del__(self):
        """Destructor to safely close database connection"""
        try:
            self._close_connection()
        except Exception as e:
            print(f"Error closing database connection: {e}")
            

if __name__ == "__main__":
    ### Testing the crawler
    crawler = Crawler()
    keywords = ['praktikum', 'werkstudent', 'praktika', 'manager']
    url = 'https://www.zootsolutions.eu/de/career/'
    crawler.crawl(url, keywords)