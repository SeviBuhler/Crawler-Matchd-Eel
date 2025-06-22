from bs4 import BeautifulSoup
import requests

def crawl_fhgr(crawler_instance, url, keywords):
        """Crawl function for FHGR"""
        print(f"Crawling FHGR URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:                    
                    ### Extract title, link and location
                    title_element = row.find('a', class_='HSTableLinkSubTitle')
                    title = title_element.get('aria-label')
                    print(f"Title: {title}")
                    
                    link_element = title_element['href'] if title_element else url
                    link = "https://jobs.fhgr.ch" + link_element
                    
                    location_element = row.find('span', class_='tableaslist_subtitle tableaslist_element_1152495')
                    location = location_element.text.replace('|', '').strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'FHGR',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None