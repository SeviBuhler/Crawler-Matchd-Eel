from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crawl_hostpoint(self, url, keywords):
            """Function to crawl Hostpoint"""
            print(f"Crawling Hostpoint URL: {url}")
            content = []
            company = "Hostpoint"
            
            try:
                # Chrome-Optionen konfigurieren
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Optional: Browser im Hintergrund
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                # WebDriver initialisieren
                driver = webdriver.Chrome(options=chrome_options)
                
                try:
                    # Seite laden
                    driver.get(url)
                
                    # Warten bis die Seite geladen ist
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.job"))
                    )
                
                    # Jobs finden und crawlen
                    job_rows = driver.find_elements(By.CSS_SELECTOR, "li.job h5 a[href*='/jobs/details/']")
                
                    print(f"Found {len(job_rows)} jobs")
                
                    for job in job_rows:
                        try:
                            title = job.text.strip()
                            link = job.get_attribute("href")
                            location = "Rapperswil-Jona"  # Hostpoint is located in Rapperswil-Jona
                        
                            print(f"Title: {title}")
                            print(f"Location: {location}")
                            print(f"URL: {link}")
                            
                            # Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                            if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                                content.append({
                                    'title': title,
                                    'link': link,  # Use job_url instead of link
                                    'location': location,
                                    'company': company
                                })
                                print(f"Found matching job: {title}")
                            else:
                                print(f"Skipping non-matching job: {title}")
                                
                            print("---")
                            
                        except Exception as e:
                            print(f"Error during extraction: {e}")
                            continue
                            
                finally:
                    # WebDriver schließen
                    driver.quit()
                    
            except Exception as e:
                print(f"Error during crawling: {e}")
                
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page        