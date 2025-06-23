from bs4 import BeautifulSoup
import requests
from bs4.element import Tag

def crawl_netsafe(crawler_instance, url, keywords):
        """Function to crawl Netsafe"""
        print(f"Crawling Netsafe URL: {url}")
        
        try: 
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_element = soup.find('div', id='jobs_grid')
            
            if job_element and isinstance(job_element, Tag):
                print(f"Job element is valid. Looking for job rows.")
                #print(f"Job element: {job_element}")
                job_rows = job_element.find_all(lambda tag: tag.name == 'a' and
                                         tag.has_attr('class') and 
                                        'text-decoration-none' in ' '.join(tag.get('class', [])))
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                    #print(f"Job rows: {job_rows}")
                else:
                    print("No job rows found in the job element.")
            else:
                print("Job element is not valid or not found.")
                
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('h3', class_='text-secondary mt0 mb4')
                    title = title_element.find('span').text.strip() if title_element else ''
                    link = 'https://www.netsafe.ch' + job['href']
                    location = 'St. Gallen'
                    company = 'Netsafe'
                    
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