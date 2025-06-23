from bs4 import BeautifulSoup
import requests

def crawl_infosystem(crawler_instance, url, keywords):
    """Function to crawl Infosystem"""
    print(f"Crawling Infosystem URL: {url}")
    
    try:
        response = requests.get(url, headers=crawler_instance.headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        job_rows = soup.find_all('div', class_='section-inner d-flex flex-column')
        print(f"Found {len(job_rows)} job listings")
        print(job_rows)  #Debugging line to print the HTML structure
        
        content = []
        for job in job_rows:
            title_element = job.find('strong', class_='title font-size-l')
            title = title_element.text.strip() if title_element else 'No title'
            link = job.find('a', class_='area-link')['href'] if job.find('a', class_='area-link') else 'No link'
            location = job.find('span', class_='overline font-size-xs').text.strip() if job.find('span', class_='overline font-size-xs') else 'No location'
            company = 'Infosystem'
            
            if any(keyword.lower() in title.lower() for keyword in keywords):
                content.append({
                    'title': title,
                    'link': link,
                    'company': company,
                    'location': location,
                })
                print(f"Found matching job: \n {title} \n {location} \n {link}")
            else:
                print(f"Skipping non-matching job:\n {title} \n {location} \n {link}")
        
        next_page = None
        print(f"Found {len(content)} jobs")
        return content, next_page
    
    except Exception as e:
        print(f"Error during crawl: {e}")
        return [], None