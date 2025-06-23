from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def crawl_hexagon(crawl_instance, url, keywords):
    """Function to crawl Hexagon / Leica Systems"""
    print(f"Crawling Hexagon URL: {url}")
    
    all_content = []
    driver = None
    
    try:
        ### Set up Chrome in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        base_url = url[:-2]
        for page_start in range(0, 45, 15):
            page_num = f"{page_start:02d}"
            current_url = base_url + page_num
            print(f"Current URL: {current_url}")
            
            print(f"\n=== CRAWLING PAGE {page_start//15 + 1} (startrow={page_num}) ===")
            print(f"URL: {current_url}")

            try:
                driver.get(current_url)
                time.sleep(3)
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                job_container = soup.find('ul', class_='search-result-list')
                if not job_container:
                    print("❌ Job container (search-result-list) not found")
                    return

                # Check if job_container is a Tag object (not a NavigableString)
                from bs4.element import Tag
                if isinstance(job_container, Tag):
                    job_rows = job_container.find_all('li')
                else:
                    print("❌ Job container is not a Tag object")
                    return [], None
                if not job_rows:
                    print("❌ No job listings found in the container")
                    driver.quit()
                    return [], None

                print(f"Found {len(job_rows)} job listings on the page")

                content = []
                for job in job_rows:
                    try:
                        div_element = job.find('div', class_='job-url')
                        link_title_element = div_element.find('a')

                        title = link_title_element.text.strip()
                        link = link_title_element['href']
                        job_text_nodes = job.find_all(text=True, recursive=True)
                        job_text_nodes = job.find_all(text=True, recursive=True)
                        for text_node in job_text_nodes:
                            text = text_node.strip()
                            if any(loc in text.lower() for loc in ['switzerland', 'zürich', 'heerbrugg', 'unterentfelden']):
                                location = text
                                break
                        company = "Geosystems Divison"

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and crawl_instance.is_location_in_ostschweiz(location) and crawl_instance.is_it_job(title):
                            job_data = {
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location
                            }
                            content.append(job_data)
                            all_content.append(job_data)
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                    except Exception as e:
                        print(f"Error during extraction: {e}")
                        continue
                
                print(f"Page {page_start//15 + 1} completed: {len(content)} matches")
                print(f"Found {len(content)} jobs")

            except Exception as e:
                print(f"Error during crawl: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                continue
            
        return all_content, None
    
    except Exception as e:
        print(f"Error during crawl: {e}")
        return [], None
    finally:
        if driver:
            driver.quit()
        print("\n" + "="*60)
        print(f"Crawling completed - Found {len(all_content)} matching jobs")
        print("="*60)