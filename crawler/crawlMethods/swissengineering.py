import requests

def crawl_swissengineering(crawler_instance, url, keywords):
        """method to crawl swissengineering.ch"""
        print(f"Crawling swissengineering URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            data = response.json()
            job_rows = data.get('jobs', [])
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    title = job.get('title', '')
                    link = "https://www.swissengineering.ch" + job.get('link', '')
                    
                    ### Extract location
                    location = job.get('worklocation', '')
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'SwissEngineering',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue

            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None