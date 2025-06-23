from bs4 import BeautifulSoup
import requests
from bs4 import Tag

def crawl_adesso(crawler_instance, url, keywords):
        """Function to crawl Adesso"""
        print(f"Crawling Adesso URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='real_table_container')
            print(f"Job section: {job_section}")
            
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all(lambda tag : tag.name == 'tr' and tag.has_attr('class') and 
                                                'alternative' in ' '.join(tag.get('class', [])))
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                title = job.find('a').text.strip()
                
                link_element = job.find('a')['href']
                if link_element.startswith('http://') or link_element.startswith('https://'):
                    link = link_element
                else:
                    link = 'https://www.adesso.ch' + link_element
                
                location = job.find('td', class_='real_table_col2').text.strip()
                company = 'Adesso'
                
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
                            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None