from bs4 import BeautifulSoup
import requests
from bs4.element import Tag
import re
import json

def crawl_neovac(crawler_instance, url, keywords):
        """Function to crawl Neovac"""
        print(f"Crawling Neovac URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_sections = soup.find_all('div', class_='toolbox-element toolbox-job-overview')
            print(f"Found {len(job_sections)} job sections")
            #print(f"Job section: {job_section}")
            
            for job_section in job_sections:
                if job_section and isinstance(job_section, Tag):
                    print(f"Job section is valid. Looking for job rows.")
                    #print(f"Job section: {job_section}")

                    ### Find the script element with the x-data attribute
                    script_data = job_section.get('x-data', '')

                    ### Extract jo data from JavaScript object (second parameter in jobfiltering)
                    if script_data:
                        ### Find the JSON array of jobs - it's the second parameter in the jobfiltering function
                        pattern = r'jobFiltering\(.+?, (\[.*?\])\)'
                        if isinstance(script_data, str):
                            match = re.search(pattern, script_data, re.DOTALL)
                        else:
                            match = None

                        if match:
                            job_json = match.group(1)
                            try: 
                                job_data = json.loads(job_json)
                                print(f"Succssfully extracted {len(job_data)} jobs from JavaScript object")

                                content = []
                                for job in job_data:
                                    title = job.get('jobTitle', '')
                                    link = job.get('detailLink', '')
                                    location = job.get('placeOfWork', '')
                                    company = 'Neovac'

                                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
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
                            
                                next_page = None
                                print(f"Found {len(content)} jobs")
                                return content, next_page
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")
                        else:
                            print("No job data found in the JavaScript object")
                    else:
                        print("No x-data attribute found in the job section") 
                else:
                    print("Job section is not valid or not found.")
            
            return [], None
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None