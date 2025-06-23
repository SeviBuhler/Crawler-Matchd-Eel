from bs4 import BeautifulSoup
import requests

def crawl_ffhs(crawler_instance, url, keywords):
        """Crawl function for FFHS"""
        print(f"Crawling FFHS URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='panel panel-default')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:        
                    ### Extract title
                    title = row.find('h3', class_='panel-title').text.strip()
                    ### Extract location
                    location = ""
                    description = row.find('div', class_='panel-body')
                    if description:
                        ### Look for a location in the description that is in Ostschweiz
                        for p in description.find_all('p'):
                            for loc_name in crawler_instance.ostschweiz_locations:
                                if loc_name in p.text.lower():
                                    location = loc_name
                    
                    ### Check if any keyword is in the title and location contains a municipality in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': url,
                            'company': 'FFHS',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None