from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crawl_migros(crawler_instance, url, keywords):
            """Function to crawl Migros jobs"""
            print(f"Crawling Migros jobs URL: {url}")
            content = []
            company = "Migros Ostschweiz"
            
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # WebDriver initialisieren
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(30)
                
                try:
                    print("Loading Migros page...")
                    driver.get(url)
                    
                    import time
                    time.sleep(5)
                    
                    print("Page loaded, waiting for job elements...")
                    
                    # Migros-spezifische Selektoren
                    try:
                        # Auf Job-Container warten
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".job-ad"))
                        )
                        
                        # Alle Job-Anzeigen finden
                        job_ads = driver.find_elements(By.CSS_SELECTOR, ".job-ad")
                        
                        if not job_ads:
                            print("No job ads found")
                            return content, None
                        
                        print(f"Found {len(job_ads)} job ads")
                        
                        for job in job_ads:
                            try:
                                # Titel extrahieren
                                title = ""
                                try:
                                    title_elem = job.find_element(By.CSS_SELECTOR, ".job-ad__title-line")
                                    title = title_elem.text.strip()
                                    # Workload von Titel trennen (falls vorhanden)
                                    if "%" in title:
                                        title = title.split("•")[0].strip() if "•" in title else title.split("%")[0].strip() + "%"
                                except:
                                    continue
                                
                                if not title:
                                    continue
                                
                                # Link extrahieren
                                link = ""
                                try:
                                    link_elem = job.find_element(By.CSS_SELECTOR, "a.job-ad__content")
                                    link = link_elem.get_attribute("href")
                                    if link and not link.startswith("http"):
                                        # Relative URLs zu absoluten machen
                                        from urllib.parse import urljoin
                                        link = urljoin(url, link)
                                except:
                                    link = url
                                
                                # Location extrahieren
                                location = "Unbekannt"
                                try:
                                    location_elems = job.find_elements(By.CSS_SELECTOR, ".job-ad__sub-line li")
                                    if location_elems:
                                        # Erste li ist normalerweise die Location
                                        location_text = location_elems[0].text.strip()
                                        # PLZ und Ort extrahieren
                                        if location_text and not "•" in location_text:
                                            location = location_text
                                except:
                                    pass
                                
                                # Company aus der Organization extrahieren (falls vorhanden)
                                try:
                                    org_elem = job.find_element(By.CSS_SELECTOR, ".job-ad__organization span:last-child")
                                    if org_elem.text.strip():
                                        company = org_elem.text.strip()
                                except:
                                    pass
                                
                                print(f"Title: {title}")
                                print(f"Location: {location}")
                                print(f"Company: {company}")
                                print(f"URL: {link}")
                                
                                # Debug: Check einzelne Bedingungen
                                keyword_match = any(keyword.lower() in title.lower() for keyword in keywords)
                                location_match = crawler_instance.is_location_in_ostschweiz(location)
                                it_job_match = crawler_instance.is_it_job(title)
                                
                                print(f"Keyword match: {keyword_match} (keywords: {keywords})")
                                print(f"Location match: {location_match}")
                                print(f"IT job match: {it_job_match}")
                                
                                # Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                                if keyword_match and location_match and it_job_match:
                                    content.append({
                                        'title': title,
                                        'link': link,
                                        'location': location,
                                        'company': company
                                    })
                                    print(f"FOUND MATCHING JOB: {title}")
                                else:
                                    reasons = []
                                    if not keyword_match:
                                        reasons.append("no keyword match")
                                    if not location_match:
                                        reasons.append("location not in Ostschweiz")
                                    if not it_job_match:
                                        reasons.append("not an IT job")
                                    print(f"Skipping job: {' | '.join(reasons)}")
                                    
                                print("---")
                                
                            except Exception as e:
                                print(f"Error during job extraction: {e}")
                                continue
                    
                    except Exception as e:
                        print(f"Error finding job ads: {e}")
                        # Debug: Seiteninhalt ausgeben
                        print("Page title:", driver.title)
                        print("Current URL:", driver.current_url)
                        page_source = driver.page_source[:2000]
                        print("Page source snippet:", page_source)
                        
                finally:
                    driver.quit()
                    
            except Exception as e:
                print(f"Error during Migros crawling: {e}")
                
            next_page = None
            print(f"Found {len(content)} matching jobs")
            return content, next_page    