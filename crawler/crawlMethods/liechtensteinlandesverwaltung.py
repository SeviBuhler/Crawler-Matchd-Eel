from bs4 import BeautifulSoup
import requests

def crawl_liechtensteinlandesverwaltung(crawler_instance, url, keywords):
        """Function to crawl Liechtenstein Landesverwaltung"""
        print(f"Crawling Liechteinstein Landesverwaltung URL: {url}")
        try:

            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all(lambda tag: tag.name == 'li' and
                                        tag.has_attr('class') and
                                        'opening-job job' in ' '.join(tag.get('class', [])))

            if job_rows:
                print(f"Found {len(job_rows)} job rows")
            else:
                print("No job rows found in the job section.")
            content = []
            for job in job_rows:

                try:
                    ### extract title
                    title = job.find('h4', class_='details-title job-title link--block-target').text.strip()
                    if title:
                        print(f"Title: {title}")
                        
                    ### extract link  
                    link_element = job.find('a')['href']
                    if  link_element.startswith('/'):
                        link = 'https://careers.smartrecruiters.com/LiechtensteinischeLandesverwaltung' + link_element
                    else:
                        link = link_element
                        
                    ### extract location
                    location_element = job.find('ul', class_='job-list list--dotted')
                    if location_element:
                        location_items = location_element.find_all('li', class_='job-desc')
                        company = location_items[0].get_text() if len(location_items) > 0 else None
                        location = location_items[1].get_text() if len(location_items) > 1 else None
                        print(f"Company: {company}")
                        print(f"Location: {location}")        
                    
                    ### check if any keyword is in the title, location is in Ostschweiz and is an IT job
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