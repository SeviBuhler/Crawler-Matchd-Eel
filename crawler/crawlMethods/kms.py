from bs4 import BeautifulSoup
import requests

def crawl_kms(crawler_instance, url, keywords):
        """Function to crawl KMS"""
        print(f"Crawling KMS URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='job__content styled')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title_element = job.find('div', class_='job__title h4')
                title = title_element.find('strong').text.strip() if title_element else 'No title'
                link = 'https://www.kms-ag.ch/karriere/offene-jobs/'
                company = 'KMS'
                location_elements = job.find_all('p')
                ### iterate though each p element to find location
                for location_element in location_elements:
                    location_element.text.strip()
                    if 'matzingen' in location_element.text.lower():
                        location = 'Matzingen'
                
                ### Check if any keyword is in the title
                if any(keyword.lower() in title.lower() for keyword in keywords):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location,
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None