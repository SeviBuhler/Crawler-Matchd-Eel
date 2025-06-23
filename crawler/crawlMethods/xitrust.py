from bs4 import BeautifulSoup
import requests

def crawl_xitrust(crawler_instance, url, keywords):
        """Function to crawl Xitrust"""
        print(f"Crawling Xitrust URL: {url}")
        try:

            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_rows = soup.find_all(lambda tag: tag.name == 'tr' and
                                        tag.has_attr('class') and
                                        'uael-table-row' in ' '.join(tag.get('class', [])))

            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            content = []
            for job in job_rows:

                try:
                    ### extract title
                    title = job.find('span', class_='uael-table__text-inner').text.strip()
                    if title:
                        print(f"Title element: {title}")
                        
                    ### extract link  
                    link_element = job.find('a')['href']
                    if  link_element.startswith('/'):
                        link = 'https://www.xitrust.com' + link_element
                    else:
                        link = link_element
                        
                    ### extract location
                    location_cell = job.find('td', attrs={'data-title': 'Arbeitsort'})

                    if location_cell:
                        location = location_cell.find('span', class_='uael-table__text-inner').get_text()
                        print(f"Location element: {location}") 

                    ### extract company      
                    company = 'Xitrust'                   
                    
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