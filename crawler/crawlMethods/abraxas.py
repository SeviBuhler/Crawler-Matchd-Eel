from bs4 import BeautifulSoup
import requests

def crawl_abraxas(crawler_instance, url, keywords):
        """Crawl function for Abraxas"""
        print(f"Crawling Abraxas URL: {url}")

        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            print(f"Initial response status: {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')
            job_rows = soup.find_all('li', class_='job-list__list-item')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for job in job_rows:
                try:
                    # Extract based on what selector matched
                    title = job.find('div', class_='job-list__job-title').text.strip()
                    location = job.find('div', class_='job-list__job-location').text.strip()
                    link = 'https://www.abraxas.ch' + job.find('a', class_='job-list__job')['href']
                    company = 'Abraxas'

                    print(f"Found job: \n Title={title} \n Location={location}")

                    # Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title} \n")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                
            next_url = None
                
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None