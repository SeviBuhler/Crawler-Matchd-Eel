from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_acreo(crawler_instance, url, keywords):
        """Function to crawl Acreo"""        
        print(f"Crawling Acreo URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
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