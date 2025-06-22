from bs4 import BeautifulSoup
import requests

def crawl_bzwu(crawler_instance, url, keywords):
        """Crawl function for BZWU"""
        print(f"Crawling BZWU URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            advertisment = soup.find_all('div', class_='panel')
            print(f"Found {len(advertisment)} job advertisments")
            
            content = []
            ### Iterate through each advertisment
            for ad in advertisment:
                try:
                    ### job elements
                    job_rows = ad.find_all('a')
                    print(f"Found {len(job_rows)} job listings")

                    ### Extract title, link, company and location from each job row
                    for row in job_rows:
                        try:
                            ### Extract title and link
                            title = row.text.strip() if row else 'Not specified'
                            link = row['href'] if row else url
                            
                            ### Check if any keyword is in the title
                            if any(keyword.lower() in title.lower() for keyword in keywords):
                                content.append({
                                    'title': title,
                                    'link': link,
                                    'company': 'BZWU',
                                    'location': 'Wil-Uzwil'
                                })
                                print(f"Found matching job: {title}")
                            else:
                                print(f"Skipping non-matching job: {title}")

                        except Exception as e:
                            print(f"Error during extraction: {e}")
                    print(content)
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            ### Extract next URL
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None