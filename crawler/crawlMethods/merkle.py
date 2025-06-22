import requests
import json

def crawl_merkle(crawler_instance, url, keywords):
    """Function to crawl Merkle Schweiz AG"""
    print(f"Crawling Merkle Schweiz AG URL: {url}")
    
    try:
        session = requests.Session()
        response = session.get(url, headers=crawler_instance.api_headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        job_rows = data.get('pages', [])
        
        print(f"Found {len(data)} job listings")
        content = []
        for job in job_rows:
            try:
                title = job.get('jobname', '')
                link = 'https://www.merkle.com/en/careers.html' + job.get('path', '')
                location = job.get('city', '')
                company = 'Merkle'

                # Check if any keyword is in the title, if location is in ostschweiz and if is it job
                if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location,
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
            
            
            
            