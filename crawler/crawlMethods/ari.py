from bs4 import BeautifulSoup
import requests
import time

def crawl_ari(crawler_instance, url, keywords):
        """Function to crawl ARI AG"""
        print(f"Crawling ARI AG URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=crawler_instance.headers, timeout=30)
            response.raise_for_status()
            
            time.sleep(5)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            page_title = soup.find('title')
            print(f"Page title: {page_title.text if page_title else 'No title'}")
            
            job_rows = soup.find_all('div', class_='w-vwrapper usg_vwrapper_1 align_none valign_middle')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('h2', class_='w-post-elm post_title usg_post_title_1 entry-title color_link_inherit')
                    title = title_element.find('a').text.strip()
                    link = title_element.find('a')['href']
                    location = 'Herisau'
                    company = 'ARI AG'
                    
                    ### Check if any keyword is in the title and if it's an IT job
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