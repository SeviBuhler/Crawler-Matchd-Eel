from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_robotron(crawler_instance, url, keywords):
        """Function to crawl Robotron"""
        print(f"Crawling Robotron URL: {url}")
        
        try:            
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='contentcontainer-column')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('p')
            else:
                print("Job section is not valid or not found.")
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### Create a copy of the job element
                    import copy
                    job_copy = copy.copy(job)
                    
                    ### Remove the anchor tag from the copy
                    if job_copy.find('a'):
                        job_copy.find('a').decompose()
                    
                    title = job_copy.text.strip()
                    link = 'https://www.robotron.ch' + job.find('a')['href']
                    company = 'Robotron'
                    location = 'Wil'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
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