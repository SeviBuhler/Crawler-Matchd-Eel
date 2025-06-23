from bs4 import BeautifulSoup
import requests

def crawl_sfs(self, url, keywords):
        """Function to crawl SFS"""
        print(f"Crawling SFS URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='molecule-responsive-datalist-entry values-are-copytext')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('strong', class_='highlight-on-interaction').text.strip()
                    link = 'https://join.sfs.com' + job['href']
                    
                    ### Extract location and company
                    loc_com_elements = job.find('span', class_='column grid-width-5')
                    expanded_columns = loc_com_elements.find_all('span', class_='column-value')
                    location = expanded_columns[0].text.strip()
                    company = loc_com_elements.find('strong').text.strip()
                        
                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None