from bs4 import BeautifulSoup
import requests
import json

def crawl_stsg (crawler_instance, url, keywords):
        """Crawl Function for Stadt St. Gallen or St.Galler Stadwerke"""
        print(f'Crawling Stadt St. Gallen / St.Galler Stadtwerke API URL: {url}')
        
        try:          
            ### Make the API request
            response = requests.get(url, headers=crawler_instance.api_headers, timeout=10)
            
            ### Parse the response using utf-8-sig encoding to handle BOM
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                ### If standard JSON decoding fails, try with utf-8-sig
                data = json.loads(response.content.decode('utf-8-sig'))
            job_rows = data.get('jobs', []) 
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### extract job details
                    title = job.get('title', {}).get('value', 'No title')
                    link_element = job.get('link', {})
                    if '../' in link_element :
                        link = 'https://live.solique.ch/STSG/de/' + link_element.replace('../', '')
                    else:    
                        link = 'https://live.solique.ch/STSG/de/' + job.get('link', {})
                    company = job.get('company', {}).get('value', 'No company')
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz, then append to content
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
                    
            Next_url = None
            
            print(f"Found {len(content)} jobs")
            return content, Next_url
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None