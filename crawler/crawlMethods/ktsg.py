from bs4 import BeautifulSoup
import requests
import re

def crawl_ktsg(crawler_instance, url, keywords):
        """Crawl function for Kanton St.Gallen"""
        print(f"Crawling Kanton St.Gallen URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            
            ### Get the actual URL from the response
            actual_url = response.url
            print(f"Actual URL: {actual_url}")
            
            ### Check if we're being redirected back to page 1
            if 'tc1152481=p1' in actual_url and 'tc1152481=p1' not in url:
                print(f"Redirected back to page 1. Stopping the crawl.")
                return [], None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title, link, company and location
                    title_element = row.find('a', class_='HSTableLinkSubTitle')
                    title = title_element.get('aria-label')
                    print(f"Title: {title}")
                    
                    link_element = title_element['href'] if title_element else url
                    link = "https://recruitingapp-2800.umantis.com" + link_element
                    
                    location_element = row.find('span', class_='tableaslist_subtitle tableaslist_element_1152495')
                    location = location_element.text.replace('|', '').strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'Kanton St.Gallen',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### Check if next page is available
            current_page_match = re.search(r'tc1152481=p(\d+)', url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
                ### Construct next page URL
                next_page = current_page + 1
                base_url = url.split('tc1152481=')[0] ### Get the base URL
                token = url.split('_search_token1152481=')[1].split('#')[0] ### Get the token
                next_url = f"{base_url}tc1152481=p{next_page}&_search_token1152481={token}#connectortable_1152481" ### Construct the next URL
                print(f"Moving to page {next_page}")
            else:
                next_url = None
                print("No page number found in URL")

            print(f"Found {len(content)} jobs")
            return content, next_url
            

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None