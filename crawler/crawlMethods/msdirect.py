from bs4 import BeautifulSoup
import requests

def crawl_msdirect(crawler_instance, url, keywords):
        """Function to crawl MSDirect"""
        print(f"Crawling MSDirect URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all(lambda tag: tag.name == 'div' and
                                        tag.has_attr('class') and
                                        'row nav-row' in ' '.join(tag.get('class', [])))
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
                
            content = []
            for job in job_rows:
                try:
                    ### extract title 
                    title = job.find('a', class_='nav-item font').text.strip()
                    if title:
                        print(f"Title element: {title}")
         
                    ### extract link   
                    link_element = job.find('a', class_='nav-item font')['href']
                    if link_element.startswith('/'):
                        link = 'https://msdirectgroup-jobs.abacuscity.ch' + link_element
                    else:
                        link = link_element
                        
                    ### extract location
                    location = job.find('span', class_='nav-filter jobsfiltercolumncontent cl6a9b5550-033d-74d4-f2f2-1b0e19589c4f').text.strip()
                    if location:
                        print(f"Location element: {location}")
                    
                    ### extract company                 
                    company = job.find('span', class_='nav-filter jobsfiltercolumncontent clada51a77-64c4-e8dc-646e-40de4a1d6ce3').text.strip()
                    
                    ### check if any keyword is in the title, location is in Ostschweiz and is an IT job
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
                            
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None