from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import bs4

def crawl_unisg(crawler_instance, url, keywords):
    """Function to crawl UniSG with AJAX pagination"""
    print(f"Crawling UniSG URL: {url}")
    
    all_content = []
    driver = None
    
    try:
        # ✅ Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        time.sleep(5)
        
        page_num = 1
        max_pages = 15
        
        while page_num <= max_pages:
            print(f"\n=== CRAWLING PAGE {page_num} ===")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            job_section = soup.find('section', id='jobResults')
            if job_section and isinstance(job_section, bs4.Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('div', class_='eight wide computer column eight wide tablet column sixteen wide mobile column')
                if job_rows:
                    print(f"Found {len(job_rows)} job rows on page {page_num}")
                else:
                    print("No job rows found in the job section.")
                    break
            else:
                print("Job section is not valid or not found.")
                break
            
            page_content = []
            for job in job_rows:
                try:
                    title_element = job.find('a')
                    if title_element:
                        title = title_element.find('h1').text.strip()
                        link = title_element['href']
                    else:
                        print("No title element found")
                        continue
                    
                    location = 'St. Gallen'
                    company = 'UniSG'
                    
                    print(f"Processing: {title}")
                    
                    if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_it_job(title):
                        job_data = {
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        }
                        page_content.append(job_data)
                        all_content.append(job_data)
                        print(f"✅ Found matching job: {title}")
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
                    print(f"Error processing job: {e}")
                    continue
            
            print(f"Page {page_num} completed: {len(page_content)} matches")
            
            ### Try to find and click next page button
            try:
                ### Look for the next button with the sendPagination onclick
                next_button = driver.find_element(By.ID, "btn-forward")
                
                ### Check if button is clickable/enabled
                class_attr = next_button.get_attribute("class") or ""
                if "disabled" in class_attr or not next_button.is_enabled():
                    print("Next button is disabled - no more pages")
                    break
                
                ### Check if onclick attribute exists
                onclick_attr = next_button.get_attribute("onclick")
                if not onclick_attr or "sendPagination" not in onclick_attr:
                    print("Next button has no pagination function - no more pages")
                    break
                
                print(f"Clicking next page button (sendPagination)...")
                driver.execute_script("arguments[0].click();", next_button)
                
                ### Wait for AJAX content to load
                print("Waiting for new content to load...")
                time.sleep(8)  # Longer wait for AJAX
                
                ### Optional: Wait for job section to be refreshed
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, "jobResults"))
                    )
                    time.sleep(3)
                except TimeoutException:
                    print("Timeout waiting for new content")
                    break
                
                page_num += 1
                
            except NoSuchElementException:
                print("Next button not found - no more pages")
                break
            except Exception as e:
                print(f"Error clicking next button: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                break
        
        print(f"\n All pages completed: {len(all_content)} total matches")
        return all_content, None
        
    except Exception as e:
        print(f"Error during crawl: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return [], None
        
    finally:
        if driver:
            driver.quit()
            print("Chrome driver closed")