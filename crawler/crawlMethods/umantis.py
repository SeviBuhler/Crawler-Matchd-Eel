from bs4 import BeautifulSoup
import requests

def crawl_umantis(crawler_instance, url, keywords):
        """Function to crawl Umantis"""
        print(f"Crawling Umantis URL: {url}")
        
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try: 
                    title = job.find('a', class_='HSTableLinkSubTitle').text.strip()
                    link = 'https://recruitingapp-9300.umantis.com/' + job.find('a', class_='HSTableLinkSubTitle')['href']
                    company = 'Abacus Umantis'
                    
                    print(f"Processing: {title}")

                    ### Extract location
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        ### load the detailed job page to extract the location
                        load_job = requests.get(link, headers=crawler_instance.headers)
                        load_job.raise_for_status()
                        job_soup = BeautifulSoup(load_job.content, 'html.parser')
                        
                        ### Check for location information in the <b> tag
                        location = None
                        is_st_gallen = False
                        
                        ### Looking for the <b> tag with the location
                        bold_elements = job_soup.find_all('b')
                        for b_elem in bold_elements:
                            text = b_elem.text.strip()
                            ### Check if this <b> tag mention a location
                            if 'Standort' in text or 'St. Gallen' in text:
                                location = text
                                if 'St. Gallen' in text:
                                    is_st_gallen = True
                                    break
                        
                        ### Onyly append the job if it's in St. Gallen
                        if is_st_gallen:
                            content.append({
                                'title': title,
                                'link': link,
                                'location': location,
                                'company': company
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                            
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
            print(f"Found {len(content)} jobs in St.Gallen")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None