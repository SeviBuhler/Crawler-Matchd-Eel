from bs4 import BeautifulSoup
import requests

def crawl_edorex(crawler_instance, url, keywords):
        """Function to crawl Edorex"""
        print(f"Crawling Edorex URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=crawler_instance.headers, timeout=15)
            response.raise_for_status()
            
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_rows = soup.find_all(lambda tag: tag.name == 'li' and 
                                                tag.has_attr('class') and
                                                'wp-block-post' in ' '.join(tag.get('class', [])) and
                                                'shp_job_category-offene-stellen' in ' '.join(tag.get('class', [])))
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('h2', class_='wp-block-post-title has-medium-font-size')
                    title = title_element.find('a').text.strip()
                    link = title_element.find('a')['href']
                    company = 'Edorex'
                    location = 'St. Gallen / Ostermundingen'
                    
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