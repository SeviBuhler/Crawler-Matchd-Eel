from bs4 import BeautifulSoup
import requests

def crawl_allconsulting(crawler_instance, url, keywords):
        """Function to crawl All Consulting"""
        print(f"Crawling All Consulting URL: {url}")
        
        try: 
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='link-arrow')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.text.strip()
                    link = 'https://all-consulting.ch' + job['href']
                    company = 'All Consulting'
                    
                    if 'St. Gallen' in title:
                        location = 'St. Gallen'
                    else:
                        location = 'unknown'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
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
            return [], next_page