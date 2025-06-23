from bs4 import BeautifulSoup
import requests
from bs4 import Tag

def crawl_sak(crawler_instance, url, keywords):
        """Function to crawl SAK"""
        print(f"Crawling SAK URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', id='job-table')
            print(f"Job section: {job_section}")
            
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('tr', class_='data-row')
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a').text.strip()
                    link = 'https://karriere.sak.ch' + job.find('a')['href']
                    location = job.find('span', class_='jobLocation').text.strip()
                    company = 'SAK'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title) and crawler_instance.is_location_in_ostschweiz(location):
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