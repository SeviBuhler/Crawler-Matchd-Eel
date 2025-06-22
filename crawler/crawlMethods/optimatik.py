from bs4 import BeautifulSoup
import requests

def crawl_optimatik(crawler_instance, url, keywords):
        """Function to crawl Optimatik"""
        print(f"Crawling Optimatik URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='red-highlight-box clearfix')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('div', class_='right-col').text.strip()
                    link = job.find('a', class_='ico-class')['href']
                    location = 'Teufen'
                    company = 'Optimatik'
                    
                    ### Check if any keyword is in the title and if it's an IT job
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
            return [], None