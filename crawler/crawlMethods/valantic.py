from bs4 import BeautifulSoup
import requests

def crawl_valantic(crawler_instance, url, keywords):
        """Function to crawl Valantic"""
        print(f"Crawling Valantic URL: {url}")
        
        ### List of all the different URL endings
        url_endings = [
            'cloud-aws/',
            'artificial-intelligence/',
            'crm/',
            'data-analytics/',
            'digital-marketing',
            'digital-platforms-e-commerce/',
            'digital-strategy/',
            'fintech/',
            'financial-services/',
            'internet-of-things/',
            'sap/',
            'cyber-security/',
            'strategy-management-consulting/',
            'backend-development/',
            'devops/',
            'frontend-development/',
            'quality-testing/',
            'it-support/',
            'second-level-support/',
            'system-administration/',
        ]
        
        try:
            content = []
            for ending in url_endings:
                response = requests.get(url + ending, headers=crawler_instance.headers, timeout=10)
                
                ### Check if the response is successful
                response.raise_for_status()
                
                print(f"Response status for {url + ending}: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_rows = soup.find_all('a', class_="bg-white flex flex-col items-start w-full rounded pt-3.5 pb-4 px-5 pr-20 shadow-[0_10px_30px_0_rgba(0,0,0,0.08)] relative group z-10 hover:z-20")
                print(f"Found {len(job_rows)} job listings")
                for job in job_rows:
                    try:
                        ### Extract title
                        title = job.find('p', class_='text-2xl font-semibold group-hover:text-red').text.strip()
                        link = job['href']
                        location = job.find('li', class_='mt-1 text-base truncate text-black/40').text.strip()
                        company = 'Valantic'
                        
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
                       
            next_url = None 
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None