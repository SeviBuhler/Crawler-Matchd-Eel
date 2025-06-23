from bs4 import BeautifulSoup
import requests

def crawl_egeli(crawler_instance, url, keywords):
        """Fucntion to crawl Egeli Informatik"""
        print(f"Crawling Egleli Informatik URL: {url}")
        
        try:            
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='row jobElement pt-2 pb-2 text-decoration-none')
                
            print(f"Found {len(job_rows)} job listings")
                
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'Egeli Informatik'

                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    return [], None
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None