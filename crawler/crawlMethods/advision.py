from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_advision(crawler_instance, url, keywords):
        """Function to crawl AdVision""" 
        print(f"Crawling AdVision URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('section', class_='job-list-area')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('div', class_='col-lg-6 col-md-6')
            else:
                print("Job section is not valid or not found.")
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3').text.strip()
                    link = job.find('a')['href']
                    location = 'Gossau'
                    company = 'AdVision'
                    
                    ### Check if any keyword is in the title and job is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
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