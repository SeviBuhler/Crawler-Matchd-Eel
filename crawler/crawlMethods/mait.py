def crawl_mait(crawler_instance, url, keywords):
            """Function to crawl dynamic JavaScript jobs"""
            print(f"Crawling dynamic jobs URL: {url}")
            content = []
            company = "Swiss-MAIT"  # Anpassen je nach Website
            
            try:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Erweiterte Chrome-Optionen
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--disable-javascript-harmony-shipping")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # WebDriver initialisieren
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(30)
               
                try:
                    print("Loading page...")
                    driver.get(url)
                    
                    # Längere Wartezeit für die Seite
                    import time
                    time.sleep(5)
                    
                    print("Page loaded, waiting for elements...")
                    
                    # Ersten Check: Schauen ob überhaupt Jobs da sind
                    try:
                        # Verschiedene mögliche Selektoren testen
                        selectors_to_try = [
                            ".JobTableItem__Container-sc-1rl91hf-0",
                            "[class*='JobTableItem__Container']",
                            "[class*='job-item']",
                            "[class*='JobItem']",
                            ".job-listing",
                            "[data-testid*='job']"
                        ]
                        
                        job_rows = []
                        for selector in selectors_to_try:
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                job_rows = driver.find_elements(By.CSS_SELECTOR, selector)
                                if job_rows:
                                    print(f"Found jobs with selector: {selector}")
                                    break
                            except:
                                continue
                        
                        if not job_rows:
                            # Fallback: Alle Links auf der Seite analysieren
                            print("No jobs found with standard selectors, analyzing page...")
                            print("Page title:", driver.title)
                            print("Current URL:", driver.current_url)
                            
                            # HTML-Snippet für Debugging ausgeben
                            page_source = driver.page_source[:2000]
                            print("Page source snippet:", page_source)
                            
                            return content, None
                        
                        print(f"Found {len(job_rows)} jobs")
                        
                        for job in job_rows:
                            try:
                                # Flexibler Titel-Extraktor
                                title = ""
                                title_selectors = [
                                    ".JobTableItem__Title-sc-1rl91hf-2",
                                    "[class*='JobTableItem__Title']",
                                    "[class*='job-title']",
                                    "h1", "h2", "h3", "h4", "h5"
                                ]
                                
                                for title_sel in title_selectors:
                                    try:
                                        title_elem = job.find_element(By.CSS_SELECTOR, title_sel)
                                        title = title_elem.text.strip()
                                        if title:
                                            break
                                    except:
                                        continue
                                
                                if not title:
                                    title = job.text.strip()[:100]  # Fallback
                                
                                # Link extrahieren
                                link = job.get_attribute("href") or url
                                
                                # Location extrahieren
                                location = "Unbekannt"
                                location_selectors = [
                                    ".JobItem__City-sc-amhyo-0",
                                    "[class*='JobItem__City']",
                                    "[class*='location']",
                                    "[class*='city']"
                                ]
                                
                                for loc_sel in location_selectors:
                                    try:
                                        location_elem = job.find_element(By.CSS_SELECTOR, loc_sel)
                                        location = location_elem.text.strip()
                                        if location:
                                            break
                                    except:
                                        continue
                                
                                print(f"Title: {title}")
                                print(f"Location: {location}")
                                print(f"URL: {link}")
                                
                                # Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                                if any(keyword.lower() in title.lower() for keyword in keywords) and crawler_instance.is_location_in_ostschweiz(location) and crawler_instance.is_it_job(title):
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
                                    
                                print("---")
                                
                            except Exception as e:
                                print(f"Error during extraction: {e}")
                                continue
                    
                    except Exception as e:
                        print(f"Error finding jobs: {e}")
                        
                finally:
                    driver.quit()
                    
            except Exception as e:
                print(f"Error during crawling: {e}")
                
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page