from bs4 import BeautifulSoup
import requests
import time

def crawl_digitalliechtenstein(crawler_instance, url, keywords):
        """Crawl function for digitalliechtenstein.ch"""
        print(f"Crawling digitalliechtenstein URL: {url}")
        try:
            time.sleep(2)            
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip()
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip()
                    
                    ### Extract Company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location):
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
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None