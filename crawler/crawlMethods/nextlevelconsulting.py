from bs4 import BeautifulSoup
import requests
import time
from bs4.element import Tag

def crawl_nextlevelconsulting(crawler_instance, url, keywords):
        """Function to crawl Nextlevel Consulting"""
        print(f"Crawling Nextlevel Consulting URL: {url}")
        
        try:
            ### crate a session to keep cookies
            session = requests.Session()
            
            response = session.get(url, headers=crawler_instance.headers, timeout=20)
            response.raise_for_status()
            time.sleep(5)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            job_section = soup.find('div', class_='content-wrapper default-gap default-gap--small')
            print(f"Job section: {job_section}")
            if job_section and isinstance(job_section, Tag):
                print("looking for job_rows in job_section")
                job_rows = job_section.find_all('a', class_='teaser-item color-white-bg teaser-item--border teaser-item--border__effect')
            else:
                print("Job section is not valid or not found.")
                job_rows = []
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('div', class_='teaser-item__title h3').text.strip()
                    link = job['href']
                    location = job.find('div', class_='teaser-item__tags').text.strip()
                    company = 'Nextlevel Consulting'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
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