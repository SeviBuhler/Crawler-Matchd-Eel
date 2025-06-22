from bs4 import BeautifulSoup
import requests

def crawl_inventx(crawler_instance, url, keywords):
        """Function to crawl InventX"""
        print(f"Crawling InventX URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all(lambda tag: tag.name == 'div' and tag.has_attr('class') and 'row row-table' in ' '.join(tag.get('class', [])))     
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title = job.find('a').text.strip()
                link = job.find('a')['href']
                location = job.find('div', class_='inner').text.strip()
                company = 'InventX'

                ### Check if any keyword is in the title and location is in Ostschweiz
                if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location
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