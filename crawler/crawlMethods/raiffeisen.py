import requests

def crawl_raiffeisen(crawl_instance, url, keywords):
        """Function to Crawl Raiffeisen Schweiz"""
        print(f"Crawling Raiffeisen Schweiz API: {url}")
        
        try:
            ### Request the API page
            response = requests.get(url, crawl_instance.api_headers, timeout=10)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
            
            ### Check if the response has the expected content of listed jobs
            job_rows = data['jobs']
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job['title']
                    link = job['links']['directlink']
                    location = job['attributes']['arbeitsort'][0]
                    company = 'Raiffeisen Schweiz'

                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawl_instance.is_location_in_ostschweiz(location) and crawl_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        ### printing what is not matching
                        print(f"Title: {title}, Location: {location}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None