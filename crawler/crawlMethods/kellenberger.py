from bs4 import BeautifulSoup
import requests
from bs4 import Tag

def crawl_kellenberger(crawler_instance, url, keywords):
        """Function to crawl Kellenberger"""    
        print(f"Crawling Kellenberger URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify())
            
            job_segment = soup.find('div', class_='vacancy-list__items vacancy-list__items--grouped-by-name')
            if job_segment and isinstance(job_segment, Tag):
                print(f'Job segment is valid. Looking for job rows.')
                job_rows = job_segment.find_all('div', class_='vacancy-list__item')
                print(f"Found {len(job_rows)} job rows")
            else:
                print("Job segment is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a', class_='vacancy__title-link').text.strip()
                    link = 'ttps://management.ostjob.ch' + job.find('a')['href']
                    location = job.find('span', class_='vacancy__workplace-city').text.strip()
                    company = 'Kellenberger'
                    
                    ### Check if any keyword is in the title and if it's an IT job
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