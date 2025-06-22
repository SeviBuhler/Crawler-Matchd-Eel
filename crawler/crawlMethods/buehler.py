import requests

def crawl_buehler(crawler_instance, url, keywords):
        """Function to Crawl Buehler Group"""
        print(f"Crawling Buehler URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.api_headers, timeout=10)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
           
            
            job_rows = data.get('jobs', [])
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    title = job.get('title', '')
                    link = job.get('link', '')
                    
                    print(f"Extracted job: Title = {title}, Location = Uzwil")
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': "Buehler Group",
                            'location': "Uzwil"
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None