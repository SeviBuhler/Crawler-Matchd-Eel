from bs4 import BeautifulSoup
import requests

def crawl_sgkb(crawler_instance, url, keywords):
        """Function to crawl St.Galler Kantonalbank"""
        print(f"Crawling St.Galler Kantonalbank URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='searchitem')
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h4').text.strip()
                    link = 'https://www.sgkb.ch' + job['href']
                    
                    location_element = job.find_all('div', class_='col-12 col-md-4')[0]
                    if location_element:
                        #print(f"Location element: {location_element}")
                        location = location_element.find('p').text.strip()
                    else:
                        print("No location element found")
                    
                    company = 'St.Galler Kantonalbank'
                    
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