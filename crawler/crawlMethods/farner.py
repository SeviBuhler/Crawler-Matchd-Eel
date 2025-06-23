from bs4 import BeautifulSoup
import requests
from bs4 import Tag

def crawl_farner(crawler_instance, url, keywords):
        """Function to crawl Farner"""
        print(f"Crawling Farner URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=crawler_instance.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
        
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            job_section = soup.find(lambda tag: tag.name == 'section' and
                                                tag.has_attr('class') and
                                                'mod-jobslist' in ' '.join(tag.get('class', [])) and
                                                'padding-top-0' in ' '.join(tag.get('class', [])))
            #print(f"Job section: {job_section}")
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                sg_p = soup.find('p', string='St. Gallen')
                
                if sg_p:
                    ### Find the parent article of this paragraph
                    sg_article = sg_p.find_parent('article')
                    print(f"Found parent article: {sg_article}")
                    
                    if sg_article:
                        ### Get the next article that contains Job listings
                        next_article = sg_article.find_next('article')
                        print(f"Found next article: {next_article}")
                        
                        job_rows = []
                        if next_article and isinstance(next_article, Tag):
                            print(f"Next article is valid. Looking for job rows.")
                            job_rows = next_article.find_all('li')
                        else:
                            print("Next article is not valid or not found.")
                        print(f"Found {len(job_rows)} job listings")
                        
                        content = []
                        for job in job_rows:
                            try:
                                ### Create a copy of the job element
                                import copy
                                job_copy = copy.copy(job)
                                
                                ### Remove the anchor tag from the copy
                                if job_copy.find_all('span'):
                                    for span in job_copy.find_all('span'):
                                        span.decompose()
                                
                                title = job_copy.text.strip()
                                link = job.find('a')['href']
                                location = 'St. Gallen'
                                company = 'Farner'
                                
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
                    else:
                        print("Parent Article of St. Gallen not found")
                        return [], None
                else:
                    print("No element with St. Gallen found")
                    return [], None
            else:
                print("Job section is not valid or not found.")
                    
        except Exception as e:
            print(f"Error during extraction: {e}")
            return [], None