import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from bs4 import Tag
import sqlite3
import re
import time


class CustomHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        # Remove the 'br' encoding from Accept-Encoding
        if 'Accept-Encoding' in request.headers:
            request.headers['Accept-Encoding'] = 'gzip, deflate'
        return super().send(request, **kwargs)


class Crawler:
    def __init__(self, db_path='crawls.db'):
        self.visited_URLs = set()
        self.results = []
        self.db = sqlite3.connect(db_path)
        self.ostschweiz_locations = self.get_ostschweiz_locations()
        
    def crawl(self, start_url: str, keywords: list[str], max_pages: int = 10):
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
            cursor = self.db.cursor()
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
                return content, next_url
        
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
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
                    if any(keyword.lower() in title.lower() for keyword in keywords):
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
                    if any(keyword.lower() in title.lower() for keyword in keywords):
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
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
        ### This website needs to be loaded with with a driver an not with requests, because its a JavaScript rendered page and requests does not execute JavaScript
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
                    if(any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location)):
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
            
    
    def __del__(self):
        if self.db:
            self.db.close()
            print("Database connection closed")
    


#if __name__ == "__main__":
#    crawler = Crawler('crawls.db') ### pass the db_path to the crawler
#    start_url = "https://jobs.inside-it.ch/jobs/"
#    keywords = ["praktikant", "praktikum", "praktikantin", "internship"]
#    crawler.crawl(start_url, keywords, max_pages=10)