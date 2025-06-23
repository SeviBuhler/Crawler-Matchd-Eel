from bs4 import BeautifulSoup
import requests
import time

def crawl_hoch(crawler_instance, url, keywords):
    """Function to crawl Hoch"""
    print(f"Crawling Hoch Health Ostschweiz URL: {url}")
    
    all_content = []
    
    base_url = url[:-3]
    
    for page_start in range(0, 225, 25):
        page_num = f"{page_start:03d}"
        current_url = base_url + page_num
        
        print(f"\n=== CRAWLING PAGE {page_start//25 + 1} (startrow={page_num}) ===")
        print(f"URL: {current_url}")
    
        try:            
            response = requests.get(current_url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            job_rows = soup.find_all('tr', class_='data-row')
            print(f"Found {len(job_rows)} job listings")
            content = []
            for job in job_rows:
                try:
                    title = job.find('a', class_='jobTitle-link').text.strip()
                    link = 'https://jobs.h-och.ch' + job.find('a')['href']
                    location = job.find('span', class_='jobLocation').text.strip()
                    company = 'Hoch Health Ostschweiz'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                        job_data ={
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        }
                        content.append(job_data)
                        all_content.append(job_data)
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
        
            print(f"Found {len(content)} matching jobs on this page")
            print(f"Total jobs found so far: {len(all_content)}")
            
            time.sleep(1)
        
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error on page {page_num}: {e}")
            continue
    
    print(f"\n=== CRAWLING COMPLETED ===")
    print(f"Total pages crawled: {(page_start//25) + 1}")
    print(f"Total matching jobs found: {len(all_content)}")

    return all_content, None
        
        