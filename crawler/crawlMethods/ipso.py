from bs4 import BeautifulSoup
import requests

def crawl_ipso(crawler_instance, url, keywords):
        """Crawl function for ipso"""
        print(f"Crawling ipso URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='beg-job-block node')
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title, link and location
                    title = row.find('p', class_='beg-job-block__title').text.strip()
                    link = row['href']
                    location = row.find('span', class_='beg-job-block__city').text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'ipso',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None