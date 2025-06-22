from bs4 import BeautifulSoup
import requests

def crawl_phsg(crawler_instance, url, keywords):
        """Crawl function for Pädagogische Hochschule St. Gallen"""
        print(f"Crawling PHSG URL: {url}")
        try:
            response = requests.get(url, headers=crawler_instance.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify()[:500])

            ### Extract parent element of listed jobs
            job_rows = soup.find_all(lambda tag: tag.name == 'tr' and tag.has_attr('class') and 'alternative_' in ' '.join(tag.get('class', [])))
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Get the first column (td with class real_table_col1)
                    col = row.find('td', class_='real_table_col1')
                    if col:
                        ### Extract title and link
                        title = col.find('a').text.strip()
                        link_element = col.find('a')
                        link = link_element['href'] if link_element else url
                        
                        ### Check if any keyword is in the title
                        if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': 'Pädagogische Hochschule St. Gallen',
                                'location': 'St. Gallen'
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")

            print(content)
            # Extract next URL
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None