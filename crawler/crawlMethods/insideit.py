from bs4 import BeautifulSoup, Tag
import requests
import time
from requests.adapters import Retry, HTTPAdapter

def crawl_insideit(crawler_instance, url, keywords):
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
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            time.sleep(2)
           
            response = session.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status() 
            
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'lxml')
            #print(soup.prettify()[:500])
            
            ### Extract parent element of listed jobs
            list = soup.find('ul', class_='job_listings list-classic')
            if not list:
                print("No job listings container found")
                return [], None
            
            if isinstance(list, Tag):
                job_rows = list.find_all('li', class_='job_listing') 
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location):
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