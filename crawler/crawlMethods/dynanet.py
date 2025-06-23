from bs4 import BeautifulSoup
import requests

def crawl_dynanet(crawler_instance, url, keywords):
        """Function to crawl DynaNet"""
        print(f"Crawling DynaNet URL: {url}")
        
        try:            
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all section elements with class 'spaltenlayout'
            layout_sections = soup.find_all('section', class_='spaltenlayout')
            print(f"Found {len(layout_sections)} layout sections")
            
            # Make sure we have at least 2 sections
            if len(layout_sections) < 2:
                print("Couldn't find the second layout section")
                return [], None
                
            # Get the second section (index 1)
            job_section = layout_sections[1]
            print(f"Job section: {job_section}")
            
            # Find job listings within this section
            job_rows = job_section.find_all('div', class_='columns')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    # Try to find a job title and link
                    title_element = job.find('h3') or job.find('h4') or job.find('strong')
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    
                    # Look for link
                    link_element = job.find('a')
                    link = link_element['href'] if link_element else url
                    if not (link.startswith('http://') or link.startswith('https://')):
                        link = 'https://dynanet.ch' + link
                        
                    location = 'St. Gallen'
                    company = 'DynaNet'
                    
                    # Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
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