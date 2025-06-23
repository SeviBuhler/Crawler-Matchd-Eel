from bs4 import BeautifulSoup
import requests
from bs4.element import Tag


def crawl_emonitor(crawler_instance, url, keywords):
    """Function to crawl eMonitor AG"""
    print(f"Crawling eMonitor AG URL: {url}")
    
    try:
        session = requests.Session()
        response = session.get(url, headers=crawler_instance.headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        job_section = soup.find('div', class_='sc-beqWaB gMKCKu')
        
        job_rows = []
        if job_section and isinstance(job_section, Tag):
            job_rows = job_section.find_all('a', class_='sc-fRcFJl iKSIhu JobTile___StyledJobLink-sc-16c0b629-0 cHnRQy JobTile___StyledJobLink-sc-16c0b629-0 cHnRQy')
        print(f"Found {len(job_rows)} job listings")
        
        content = []
        for job in job_rows:
            try:
                title = job.find('h3', class_='sc-hLseeU cqebHa').text.strip()
                link = job['href']
                location = job.find('div', class_='sc-hLseeU JobTile-elements___StyledText-sc-51fc004f-4 fyJRsY cRWjLU').text.strip()
                company = 'emonitor AG'
                
                print(f"Found job: {title} at {location}")
                
                ### Check if any keyword is in the title, if it's an IT job, and if the location is in Ostschweiz
                if (any(keyword.lower() in title.lower() for keyword in keywords) and 
                    crawler_instance.is_it_job(title) and 
                    crawler_instance.is_location_in_ostschweiz(location)):
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