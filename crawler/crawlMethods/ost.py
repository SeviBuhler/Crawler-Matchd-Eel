from bs4 import BeautifulSoup
import requests

def crawl_ost(crawler_instance, url, keywords):
        """Crawl function for jobs-ost.ch"""
        print(f"Crawling jobs-ost URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            data = response.json()
            ### Extract parent element of listed jobs
            job_rows = data.get('jobs', [])
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    title = row['title']
                    link = row['links']['directlink']
                    location = row['attributes']['10'][0]
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'OST',
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