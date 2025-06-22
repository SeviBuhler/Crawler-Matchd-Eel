from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_diselva(crawler_instance, url, keywords):
        """Function to crawl Diselva"""
        print(f"Crawling Diselva URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=crawler_instance.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_section = soup.find('div', class_='row-fluid-wrapper row-depth-1 row-number-2 dnd-section')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                job_rows = job_section.find_all(lambda tag: tag.name == 'div' and
                                              tag.has_attr('class') and
                                                'column item' in ' '.join(tag.get('class', [])))
            print(f"Found {len(job_rows)} job listings")
            
            
            content = []
            for job in job_rows[1:]:
                try: 
                    title = job.find('h3', class_='mt-4 title is-4 is-height-100px').text.strip()
                    link = job.find('a', class_='has-text-dark')['href']
                    company = 'Diselva'
                    location = 'St. Gallen'
                    
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