from bs4 import BeautifulSoup
import requests

def crawl_laveba(crawler_instance, url, keywords):
        """Function to crawl Laveba Genossenscahft"""
        print(f"Crawling Laveba URL: {url}")
        
        try: 
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='row jobElement pt-2 pb-2 text-decoration-none')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
            else:
                print("No job rows found in the job section.")
            
            content = []    
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'Laveba'

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