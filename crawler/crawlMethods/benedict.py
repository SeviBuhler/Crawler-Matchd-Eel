"""
Benedict.ch Crawler
"""

import requests
from bs4 import BeautifulSoup, Tag

def crawl_benedict(crawler_instance, url, keywords):
    """Crawl function for Benedict"""
    print(f"Crawling Benedict URL: {url}")
    try:
        response = requests.get(url, headers=crawler_instance.headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
    
        ### Extract parent element of listed jobs
        ### Then find all H2 elements in the div
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
                            link = "www.benedict.ch/" + job_element.attrs['href']
                        else:
                            href = job_element.get('href')
                            link = "www.benedict.ch/" + str(href) if href else "www.benedict.ch/"
                            
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
            return content or [], next_url or None
    
    except Exception as e:
        print(f"Error during crawl: {e}")
        return [], None