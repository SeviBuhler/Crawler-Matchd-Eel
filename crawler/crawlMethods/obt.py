from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_obt(crawler_instance, url, keywords):
        """Function to crawl OBT"""
        print(f"Crawling OBT URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_segment = soup.find('div', class_='Jobs__content')
            print(f"found job segment")
            if job_segment and isinstance(job_segment, Tag):
                job_element = job_segment.find_all('div', class_='Jobs__cardEntries | js-entries')[2]
                print(f"found Job Element {job_element}")
                if job_element and isinstance(job_element, Tag):
                    print(f"Job element is valid. Looking for job rows.")
                    job_rows = job_element.find_all('div', class_='Jobs__cardEntriesItem | js-entry')
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("Job element is not valid or not found.")
            else:
                print("Job segment is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h6', class_='Jobs__cardEntriesItemTitle').text.strip()
                    link = 'https://www.obt.ch' +  job.find('a')['href']
                    location = job.find('div', class_='Jobs__cardEntriesInfoPointTitle').text.strip()
                    company = 'OBT'
                    
                    ### Check if keyword is in title, if job is in Ostschweiz and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        keyword_match = any(keyword.lower() in title.lower() for keyword in keywords)
                        it_job_match = crawler_instance.is_it_job(title)
                        if not keyword_match and not it_job_match:
                            print(f"Skipping: no keyword match + not IT job - {title}")
                        elif not keyword_match:
                            print(f"Skipping: no keyword match - {title}")
                        elif not it_job_match:
                            print(f"Skipping: not IT job - {title}")
                            
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None