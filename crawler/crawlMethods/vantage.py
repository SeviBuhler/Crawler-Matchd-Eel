from bs4 import BeautifulSoup
import requests

def crawl_vantage(crawler_instance, url, keywords):
        """Crawl function for Vantage"""
        print(f"Crawling Vantage URL: {url}")
        
        try:
            ### Crawl the URL
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            if soup:
                job_rows = soup.find_all('div', class_='infos')
                print(f"Found {len(job_rows)} job listings")
                
                ### Extract title, link, company and location from each job row
                content = []
                for row in job_rows:
                    try:
                        ### Extract title and link
                        title_element = row.find('span', class_='d-block w-100 border-bottom pb-3 mb-3')
                        title = title_element.text.strip()
                        link_element = row.find('a')
                        link = link_element['href'] if link_element else url
                        
                        bold_elements = row.find_all('b')
                        company = bold_elements[0].text.strip() if len(bold_elements) > 0 else 'Not specified'
                        location = bold_elements[2].text.strip() if len(bold_elements) > 2 else 'Not specified'

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                    
                    except Exception as e:
                        print(f"Error during extraction: {e}")

                print(content)
                # Extract next URL
                next_url = None
                print(f"Found {len(content)} jobs")
                return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None