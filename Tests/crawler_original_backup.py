import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from bs4 import Tag
import sqlite3
import threading
import re
import time
from database_config import get_db_path
import urllib.parse
import json
import traceback


class CustomHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        # Remove the 'br' encoding from Accept-Encoding
        if 'Accept-Encoding' in request.headers:
            request.headers['Accept-Encoding'] = 'gzip, deflate'
        return super().send(request, **kwargs)


class Crawler:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path is not None else get_db_path()
        self.thread_local = threading.local()
        self.visited_URLs = set()
        self.results = []
        self.ostschweiz_locations = self.get_ostschweiz_locations()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.4',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    def _get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.thread_local, 'connection'):
            self.thread_local.connection = sqlite3.connect(self.db_path)
        return self.thread_local.connection
    
    def _close_connection(self):
        """Close the thread-local connection if it exists"""
        if hasattr(self.thread_local, 'connection'):
            self.thread_local.connection.close()
            del self.thread_local.connection

        
    def crawl(self, start_url: str, keywords: list[str], max_pages: int = 30):
        """Main crawl function that handles multiple pages"""
        all_content = []
        current_url = start_url
        page_count = 1
        
        print("\n" + "="*60)
        print(f"Starting crawler with keywords: {', '.join(keywords)}")
        print("="*60)
        
        while current_url and page_count <= max_pages:
            print(f"\nCrawling page {page_count}: {current_url}")
            
            try:
                ### Debug prints to see which condition is matched
                print("Checking URL")
                ### Crawl current page
                if "benedict.ch" in current_url:
                    print(f"benendict.ch: {'benedict.ch' in current_url}")
                    page_content, next_url = self.crawl_benedict(current_url, keywords)
                elif "vantage.ch" in current_url:
                    print(f"vantage.ch: {'vantage.ch' in current_url}")
                    page_content, next_url = self.crawl_vantage(current_url, keywords)
                elif "bzwu.ch" in current_url:
                    print(f"bzwu.ch: {'bzwu.ch' in current_url}")
                    page_content, next_url = self.crawl_bzwu(current_url, keywords)
                elif "ffhs.ch" in current_url:
                    print(f"ffhs.ch: {'ffhs.ch' in current_url}")
                    page_content, next_url = self.crawl_ffhs(current_url, keywords)
                elif "fhgr.ch" in current_url:
                    print(f"fhgr.ch: {'fhgr.ch' in current_url}")
                    page_content, next_url = self.crawl_fhgr(current_url, keywords)
                elif any(string in current_url for string in ['arbeitgeber-kanton-stgallen', 'umantis.com']):
                    print(f"gbssg: {any(string in current_url for string in ['arbeitgeber-kanton-stgallen', 'umantis.com'])}")
                    page_content, next_url = self.crawl_gbssg(current_url, keywords)
                elif "ipso.ch" in current_url:
                    print(f"ipso.ch: {'ipso.ch' in current_url}")
                    page_content, next_url = self.crawl_ipso(current_url, keywords)
                elif "phsg.ch" in current_url:
                    print(f"phsg.ch: {'phsg.ch' in current_url}")
                    page_content, next_url = self.crawl_phsg(current_url, keywords)
                elif "jobs-ost.ch" in current_url:
                    print(f"jobs-ost.ch: {'jobs-ost.ch' in current_url}")
                    page_content, next_url = self.crawl_ost(current_url, keywords)
                elif "swissengineering.ch" in current_url:
                    print(f"swissengineering.ch: {'swissengineering.ch' in current_url}")
                    page_content, next_url = self.crawl_swissengineering(current_url, keywords)
                elif "startfeld" in current_url:
                    print(f"innovationspark-ost.ch: {'startfeld' in current_url}")
                    page_content, next_url = self.crawl_innovationspark(current_url, keywords)
                elif "rheintalcom" in current_url:
                    print(f"rheintal.com: {'rheintalcom' in current_url}")
                    page_content, next_url = self.crawl_rheintal(current_url, keywords)
                elif "digitalliechtenstein" in current_url:
                    print(f"digitalliechtenstein.com: {'digitalliechtenstein' in current_url}")
                    page_content, next_url = self.crawl_digitalliechtenstein(current_url, keywords)
                elif "eastdigital" in current_url:
                    print(f"eastdigital: {'eastdigital' in current_url}")
                    page_content, next_url = self.crawl_eastdigital(current_url, keywords)
                elif "inside-it.ch" in current_url:
                    print(f"inside-it.ch: {'inside-it' in current_url}")
                    page_content, next_url = self.crawl_inside_it(current_url, keywords)
                elif "jobportal.abaservices" in current_url:
                    print(f"Abacus.ch: {'abacus' in current_url}")
                    page_content, next_url = self.crawl_abacus(current_url, keywords)
                elif "STSG" in current_url:
                    print(f"STSG.ch: {'STSG' in current_url}")
                    page_content, next_url = self.crawl_STSG(current_url, keywords)
                elif "valantic" in current_url:
                    print(f"valantic.ch: {'valantic' in current_url}")
                    page_content, next_url = self.crawl_valantic(current_url, keywords)
                elif 'abraxas' in current_url:
                    print(f"abraxas.ch: {'abraxas' in current_url}")
                    page_content, next_url = self.crawl_abraxas(current_url, keywords)
                elif 'ohws.prospective.ch/public/v1/medium/1008005' in current_url:
                    print(f"buhlergroup.com: {'prospective' in current_url}")
                    page_content, next_url = self.crawl_buehler(current_url, keywords)
                elif 'jobs.dualoo.com/portal/lx0anfq4?lang=DE' in current_url:
                    print(f"egeli-informatik.ch: {'egeli' in current_url}")
                    page_content, next_url = self.crawl_egeli(current_url, keywords)
                elif 'h-och.ch' in current_url:
                    print(f"h-och.ch: {'h-och' in current_url}")
                    page_content, next_url = self.crawl_hoch(current_url, keywords, page_count)
                elif 'inventx' in current_url:
                    print(f"inventx.ch: {'inventx' in current_url}")
                    page_content, next_url = self.crawl_inventx(current_url, keywords)
                elif 'kms-ag' in current_url:
                    print(f"kms-ag.ch: {'kms-ag' in current_url}")
                    page_content, next_url = self.crawl_kms(current_url, keywords)
                elif 'hexagon.com' in current_url:
                    print(f"hexagon.com: {'hexagon.com' in current_url}")
                    page_content, next_url = self.crawl_hexagon(current_url, keywords)
                elif 'ohws.prospective.ch/public/v1/medium/1950' in current_url:
                    print(f"API von Raiffeisen Schweiz: {'ohws.prospective.ch' in current_url}")
                    page_content, next_url = self.crawl_raiffeisen(current_url, keywords)
                elif 'join.sfs.com' in current_url:
                    print(f"SFS Group: {'join.sfs.com' in current_url}")
                    page_content, next_url = self.crawl_sfs(current_url, keywords)
                elif 'umantis.com' in current_url:
                    print(f"Umantis: {'umantis.com' in current_url}")
                    page_content, next_url = self.crawl_umantis(current_url, keywords)
                elif 'acreo.ch' in current_url:
                    print(f"acreo consulting: {'acreo consulting' in current_url}")
                    page_content, next_url = self.crawl_acreo(current_url, keywords)
                elif 'all-consulting.ch' in current_url:
                    print(f"All Consulting: {'all-consulting.ch' in current_url}")
                    page_content, next_url = self.crawl_allconsulting(current_url, keywords)
                elif 'aproda.ch' in current_url:
                    print(f"Aproda: {'aproda.ch' in current_url}")
                    page_content, next_url = self.crawl_aproda(current_url, keywords)
                elif 'zootsolutions' in current_url:
                    print(f"Zoot Solutions: {'zootsolutions' in current_url}")
                    page_content, next_url = self.crawl_zoot(current_url, keywords)
                elif 'stackworks.ch' in current_url:
                    print(f"Stackworks: {'stackworks.ch' in current_url}")
                    page_content, next_url = self.crawl_stackworks(current_url, keywords)
                elif 'optisizer.ch' in current_url:
                    print(f"Optisizer: {'optisizer.ch' in current_url}")
                    page_content, next_url = self.crawl_optisizer(current_url, keywords)
                elif 'ari-ag.ch' in current_url:
                    print(f"ARI AG: {'ari-ag.ch' in current_url}")
                    page_content, next_url = self.crawl_ari(current_url, keywords)
                elif 'nextlevelconsulting.com' in current_url:
                    print(f"Next Level Consulting: {'nextlevelconsulting.com' in current_url}")
                    page_content, next_url = self.crawl_nextlevelconsulting(current_url, keywords)
                elif 'edorex.ch' in current_url:
                    print(f"Edorex: {'edorex.ch' in current_url}")
                    page_content, next_url = self.crawl_edorex(current_url, keywords)
                elif 'diselva.com' in current_url:
                    print(f"Diselva: {'diselva.com' in current_url}")
                    page_content, next_url = self.crawl_diselva(current_url, keywords)
                elif 'app.ch/karriere' in current_url:
                    print(f"App: {'app.ch/karriere' in current_url}")
                    page_content, next_url = self.crawl_app(current_url, keywords)
                elif 'advision.swiss' in current_url:
                    print(f"Advision: {'advision.swiss' in current_url}")
                    page_content, next_url = self.crawl_advision(current_url, keywords)
                elif 'xerxes' in current_url:
                    print(f"Xerxes: {'xerxes' in current_url}")
                    page_content, next_url = self.crawl_xerxes(current_url, keywords)
                elif 'webwirkung.ch' in current_url:
                    print(f"Webwirkung: {'webwirkung.ch' in current_url}")
                    page_content, next_url = self.crawl_webwirkung(current_url, keywords)
                elif 'stgallennetgroup.ch' in current_url:
                    print(f"St.Gallen Netgroup: {'stgallennetgroup.ch' in current_url}")
                    page_content, next_url = self.crawl_stgallennetgroup(current_url, keywords)
                elif 'robotron.ch' in current_url:
                    print(f"Robotron: {'robotron.ch' in current_url}")
                    page_content, next_url = self.crawl_robotron(current_url, keywords)
                elif 'joshmartin.ch' in current_url:
                    print(f"Josh Martin: {'joshmartin.ch' in current_url}")
                    page_content, next_url = self.crawl_joshmartin(current_url, keywords)
                elif 'www.farner.ch' in current_url:
                    print(f"Farner: {'www.farner.ch' in current_url}")
                    page_content, next_url = self.crawl_farner(current_url, keywords)
                elif 'dynanet.ch' in current_url:
                    print(f"Dynanet: {'dynanet.ch' in current_url}")
                    page_content, next_url = self.crawl_dynanet(current_url, keywords)
                elif 'dachcom.com' in current_url:
                    print(f"Dachcom: {'dachcom.com' in current_url}")
                    page_content, next_url = self.crawl_dachcom(current_url, keywords)
                elif 'adesso.ch' in current_url:
                    print(f"Adesso: {'adesso.ch' in current_url}")
                    page_content, next_url = self.crawl_adesso(current_url, keywords)
                elif 'unisg.ch' in current_url:
                    print(f"Universität St. Gallen: {'unisg.ch' in current_url}")
                    page_content, next_url = self.crawl_unisg(current_url, keywords)
                elif 'svasg-jobs' in current_url:
                    print(f"SVA St. Gallen: {'svasg-jobs' in current_url}")
                    page_content, next_url = self.crawl_svasg(current_url, keywords)
                elif 'sgkb.ch' in current_url:
                    print(f"St. Galler KB: {'sgkb.ch' in current_url}")
                    page_content, next_url = self.crawl_sgkb(current_url, keywords)
                elif 'sak.ch' in current_url:
                    print(f"SAK: {'sak.ch' in current_url}")
                    page_content, next_url = self.crawl_sak(current_url, keywords)
                elif '.ch/public/v1/careercenter/1005765' in current_url:
                    print(f'Pychiatrie St.Gallen: {".ch/public/v1/careercenter/1005765" in current_url}')
                    page_content, next_url = self.crawl_psg(current_url, keywords)
                elif 'jobs.dualoo.com/portal/ppqp7jqv?lang=DE' in current_url:
                    print(f'Permapack: {"jobs.dualoo.com/portal/ppqp7jqv?lang=DE" in current_url}')
                    page_content, next_url = self.craw_permapack(current_url, keywords)
                elif 'optimatik.ch' in current_url:
                    print(f'Optimatik: {"optimatik.ch" in current_url}')
                    page_content, next_url = self.crawl_optimatik(current_url, keywords)
                elif 'oertli-jobs.com' in current_url:
                    print(f"Oertli: {"oertli-jobs.com" in current_url}")
                    page_content, next_url = self.crawl_oertli(current_url, keywords)
                elif 'obt.ch/de/karriere' in current_url:
                    print(f"OBT: {'.obt.ch/de/karriere' in current_url}")
                    page_content, next_url = self.crawl_obt(current_url, keywords)
                elif 'netsafe.ch/jobs' in current_url:
                    print(f"Netsafe: {'netsafe.ch/jobs' in current_url}")
                    page_content, next_url = self.crawl_netsafe(current_url, keywords)
                elif 'www.neovac.ch/jobs' in current_url:
                    print(f"Neovac: {'www.neovac.ch/jobs' in current_url}")
                    page_content, next_url = self.crawl_neovac(current_url, keywords)
                elif 'jobs.mtf.ch/de/jobportal' in current_url:
                    print(f"MTF: {'jobs.mtf.ch/de/jobportal' in current_url}")
                    page_content, next_url = self.crawl_mtf(current_url, keywords)
                elif 'msdirectgroup-jobs' in current_url:
                    print(f"MS Direct Group: {'msdirectgroup-jobs' in current_url}")
                    page_content, next_url = self.crawl_msdirect(current_url, keywords)
                elif 'search-api.metrohm.com' in current_url:
                    print(f"Metrohm: {'search-api.metrohm.com' in current_url}")
                    page_content, next_url = self.crawl_metrohm(current_url, keywords)
                elif 'dentsuaegis.wd3' in current_url:
                    print(f"Dentsu Aegis: {'dentsuaegis.wd3' in current_url}")
                    page_content, next_url = self.crawl_merkle(current_url, keywords)
                elif 'management.ostjob.ch/minisite/62' in current_url:
                    print(f"Kellenberger: {'kellenberger.com/de/stellenanzeigen' in current_url}")
                    page_content, next_url = self.crawl_kellenberger(current_url, keywords)
                elif 'jobs.dualoo.com/portal/elj8aw7v?lang=DE' in current_url:
                    print(f"Laveba Genossenschaft: {'jobs.dualoo.com/portal/elj8aw7v?lang=DE' in current_url}")
                    page_content, next_url = self.crawl_laveba(current_url, keywords)
                else:
                    print(f"Unknown URL: {current_url}")
                    return
                    
                all_content.extend(page_content)
                
                ### Prepare for next page
                if next_url and next_url != current_url:
                    current_url = next_url
                    page_count += 1
                else:
                    current_url = None
        
            except Exception as e:
                print(f"Error druing crawl: {e}")
                current_url = None
            finally:
                self._close_connection()
                
        
        ### Print final result nicely formatted
        print("\n" + "="*60)
        print(f"Crawling completed - Found {len(all_content)} matching jobs")
        print("="*60)

        if all_content:
            for i, job in enumerate(all_content, 1):
                print(f"\nJob {i}:")
                print("-"*30)
                print(f"Title:    {job['title']}")
                print(f"Company:  {job.get('company', 'Not specified')}")
                print(f"Location: {job.get('location', 'Not specified')}")
                print(f"Link:     {job['link']}")
        else:
            print("\nNo matching jobs found.")

        print("\n" + "="*60)
        print("End of results")
        print("="*60)
                
        return all_content
    
    
    def get_ostschweiz_locations(self):
        """Get all Ostschweiz municipalities from the database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT ortschaftsname, kanton FROM localities""")
            ostschweiz_locations = cursor.fetchall()
            return set([location[0].lower() for location in ostschweiz_locations])
        except Exception as e:
            print(f"Error during extraction: {e}")
            return set()
        
    
    def is_it_job(self, title):
        """Check if a job title is an IT job"""
        it_keywords = [
            'informatik',
            'software',
            'entwickler',
            'developer',
            'programmierer',
            'engineer',
            'devops',
            'cloud',
            'network',
            'storage',
            'cyber',
            'application',
            'applikation',
            'ict',
            'systemadministrator',
            'syste',
            'digital',
            'consult',
            'datenbank',
            'frontend',
            'backend',
            'fullstack',
            'it'
        ]
        return any(keyword.lower() in title.lower() for keyword in it_keywords)
    
    
    def is_location_in_ostschweiz(self, location):
        """Check if a location is in Ostschweiz"""
        print(f"Checking location: {location}")
        location_lower = location.lower()
        for loc_name in self.ostschweiz_locations:
            if loc_name in location.lower():
                if loc_name in location_lower:
                    # Check if the matched municipality is a standalone word
                    if re.search(r'\b{}\b'.format(re.escape(loc_name)), location_lower):
                        print(f"Location {location} is in Ostschweiz")
                        return True
                    else:
                        print(f"Skipping partial match: {loc_name} in {location}")

        print(f"Location {location} is not in Ostschweiz")
        return False
    
    
    def crawl_benedict(self, url, keywords):
        """Crawl function for Benedict"""
        print(f"Crawling Benedict URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
        
            ### Then find all H2 elements in the div
            ### Extract parent element of listed jobs
            if soup:
                job_rows = soup.select('div#city4 h2.h3')
                print(f"Found {len(job_rows)} job listings")
                
                ### Extract title, link, company and location from each job row
                content = []
                for row in job_rows:
                    try:
                        ### Extract title and link
                        job_element = row.find('a')
                        if job_element and isinstance(job_element, Tag):
                            title = job_element.text.strip()
                            if job_element.has_attr('href'):
                                link = job_element.attrs['href']
                            link = job_element.get('href')

                        ### Check if any keyword is in the title
                        if any(keyword.lower() in title.lower() for keyword in keywords):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': 'Benedict',
                                'location': 'St. Gallen'
                            })
                            print(f"Found job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                    except Exception as e:
                        print(f"Error during extraction: {e}")

                print(content)
                # Extract next URL
                next_url = None
                print(f"Found {len(content)} jobs")
                return content or [], next_url or None
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_vantage(self, url, keywords):
        """Crawl function for Vantage"""
        print(f"Crawling Vantage URL: {url}")
        
        try:
            ### Crawl the URL
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            if soup:
                job_rows = soup.find_all('div', class_='infos')
                print(f"Found {len(job_rows)} job listings")
                
                ### Extract title, link, company and location from each job row
                content = []
                for row in job_rows:
                    try:
                        ### Extract title and link
                        title_element = row.find('span', class_='d-block w-100 border-bottom pb-3 mb-3')
                        title = title_element.text.strip()
                        link_element = row.find('a')
                        link = link_element['href'] if link_element else url
                        
                        bold_elements = row.find_all('b')
                        company = bold_elements[0].text.strip() if len(bold_elements) > 0 else 'Not specified'
                        location = bold_elements[2].text.strip() if len(bold_elements) > 2 else 'Not specified'

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location
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
        
    
    def crawl_bzwu(self, url, keywords):
        """Crawl function for BZWU"""
        print(f"Crawling BZWU URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            advertisment = soup.find_all('div', class_='panel')
            print(f"Found {len(advertisment)} job advertisments")
            
            content = []
            ### Iterate through each advertisment
            for ad in advertisment:
                try:
                    ### job elements
                    job_rows = ad.find_all('a')
                    print(f"Found {len(job_rows)} job listings")

                    ### Extract title, link, company and location from each job row
                    for row in job_rows:
                        try:
                            ### Extract title and link
                            title = row.text.strip() if row else 'Not specified'
                            link = row['href'] if row else url
                            
                            ### Check if any keyword is in the title
                            if any(keyword.lower() in title.lower() for keyword in keywords):
                                content.append({
                                    'title': title,
                                    'link': link,
                                    'company': 'BZWU',
                                    'location': 'Wil-Uzwil'
                                })
                                print(f"Found matching job: {title}")
                            else:
                                print(f"Skipping non-matching job: {title}")

                        except Exception as e:
                            print(f"Error during extraction: {e}")
                    print(content)
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            ### Extract next URL
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_ffhs(self, url, keywords):
        """Crawl function for FFHS"""
        print(f"Crawling FFHS URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='panel panel-default')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Print each job element for debugging
                    #print("\nJob element found:")
                    #print(row.prettify())
                    
                    ### Extract title
                    title = row.find('h3', class_='panel-title').text.strip()
                    #print(f"Title: {title}")
                    ### Extract location
                    location = ""
                    description = row.find('div', class_='panel-body')
                    if description:
                        ### Look for a location in the description that is in Ostschweiz
                        for p in description.find_all('p'):
                            for loc_name in self.ostschweiz_locations:
                                if loc_name in p.text.lower():
                                    location = loc_name
                    
                    ### Check if any keyword is in the title and location contains a municipality in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': url,
                            'company': 'FFHS',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                                                          
    
    def crawl_fhgr(self, url, keywords):
        """Crawl function for FHGR"""
        print(f"Crawling FHGR URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='tableaslist_cell')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Print each job element for debugging
                    #print("\nJob element found:")
                    #print(row.prettify())
                    
                    ### Extract title, link and location
                    title_element = row.find('a', class_='HSTableLinkSubTitle')
                    title = title_element.get('aria-label')
                    print(f"Title: {title}")
                    
                    link_element = title_element['href'] if title_element else url
                    link = "https://jobs.fhgr.ch" + link_element
                    
                    location_element = row.find('span', class_='tableaslist_subtitle tableaslist_element_1152495')
                    location = location_element.text.replace('|', '').strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'FHGR',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            next_url = None
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                    
    
    def crawl_gbssg(self, url, keywords):
        """Crawl function for gbssg"""
        print(f"Crawling gbssg URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
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
        
    
    def crawl_ipso(self, url, keywords):
        """Crawl function for ipso"""
        print(f"Crawling ipso URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='beg-job-block node')
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title, link and location
                    title = row.find('p', class_='beg-job-block__title').text.strip()
                    link = row['href']
                    location = row.find('span', class_='beg-job-block__city').text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'ipso',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    
    def crawl_phsg(self, url, keywords):
        """Crawl function for Pädagogische Hochschule St. Gallen"""
        print(f"Crawling PHSG URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify()[:500])

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('tr', class_='alternative_1')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Get the first column (td with class real_table_col1)
                    col = row.find('td', class_='real_table_col1')
                    if col:
                        ### Extract title and link
                        title = col.find('div', id='job_311').text.strip()
                        link_element = col.find('a')
                        link = link_element['href'] if link_element else url
                        
                        ### Check if any keyword is in the title
                        if any(keyword.lower() in title.lower() for keyword in keywords):
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
    
    
    def crawl_ost(self, url, keywords):
        """Crawl function for jobs-ost.ch"""
        print(f"Crawling jobs-ost URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            ### Extract parent element of listed jobs
            job_rows = soup.find_all('div', class_='joboffer_container')
            print(f"Found {len(job_rows)} job listings")

            content = []
            for row in job_rows:
                try:
                    ### Extract title and link
                    title_element = row.find('a', target='_self')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    link = title_element['href'] if title_element else url
                    
                    ### Extract location
                    location_element = row.find('div', class_='joboffer_informations joboffer_box')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'OST',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")

            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    def crawl_swissengineering(self, url, keywords):
        """method to crawl swissengineering.ch"""
        print(f"Crawling swissengineering URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json() ### get the whole json data
            job_rows = data.get('jobs', []) ### get the jobs array safely
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    title = job.get('title', '')
                    link = "https://www.swissengineering.ch" + job.get('link', '')
                    
                    ### Extract location
                    location = job.get('worklocation', '')
                    
                    ### Check if any keyword is in the title and append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': 'SwissEngineering',
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue

            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_innovationspark(self, url, keywords):
        """Crawl function for innovationspark-ost.ch"""
        print(f"Crawling innovationspark-ost URL: {url}")
        try:
            ### Make a request to the URL
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print("Initial response status:", response.status_code)
            #print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href'] if link_element else url
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            print(f"Found {len(content)} jobs")
            next_url = None
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    def crawl_rheintal(self, url, keywords):
        """Crawl function for rheintal.com"""
        print(f"Crawling rheintal.com URL: {url}")
        try:            
            ### request to the URL
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print("Initial response status:", response.status_code)
            #print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href'] if link_element else url
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if(any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title)):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_digitalliechtenstein(self, url, keywords):
        """Crawl function for digitalliechtenstein.ch"""
        print(f"Crawling digitalliechtenstein URL: {url}")
        try:
            time.sleep(2)            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip()
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip()
                    
                    ### Extract Company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    def crawl_eastdigital(self, url, keywords):
        """Crawl function for eastdigital.ch"""
        print(f"Crawling eastdigital URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            print("Initial response status:", response.status_code)
            print("Response content previes:", response.text[:500])
            
            job_rows = soup.find_all('li', class_='item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('span', class_='jobtitle')
                    title = title_element.text.strip()
                    
                    ### Extract link
                    link_element = row.find('a', class_='title')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('span', class_='location')
                    location = location_element.text.strip()
                    
                    ### Extract Company
                    company_element = row.find('a', title='Alle Jobs dieser Firma anzeigen...')
                    company = company_element.text.strip()
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find_all('a', class_='btn btn-sm btn-secondary')
            print(f"Found next page element: {next_page_element}")
            
            next_url = None
            for element in next_page_element:
                if "Nächste Seite" in element.text:
                    next_url = element.get('href')
                    break
            
            if next_url:
                print(f"Next page found: {next_url}")
            else:
                print("No next page found")
            
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    def crawl_inside_it(self, url, keywords):
        """Crawl function for inside-it.ch"""
        print(f"Crawling inside-it URL: {url}")
        try:
            
            ### Set up a session with retries
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = CustomHTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            time.sleep(2)
           
            response = session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() ### Raise an exception for bad status codes
            
            response.encoding = 'utf-8' ### Force the encoding to utf-8

            ### Debug info
            #print("Response headers:", response.headers)
            #print("Content type:", response.headers.get('content-type'))
            #print("Content encoding:", response.headers.get('content-encoding'))

            
            ### parse with lxml
            soup = BeautifulSoup(response.content, 'lxml')
            #print(soup.prettify()[:500])
            
            ### Extract parent element of listed jobs
            list = soup.find('ul', class_='job_listings list-classic')
            if not list:
                print("No job listings container found")
                return [], None
            
            if isinstance(list, Tag):
                job_rows = list.find_all('li', class_='job_listing') ### get all job listings from the list container
            else:
                job_rows = []
                print("No job listings container found")
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for row in job_rows:
                try:
                    ### Extract title
                    title_element = row.find('h3', class_='job-listing-loop-job__title')
                    title = title_element.text.strip() if title_element else 'Not specified'
                    
                    ### Extract link
                    link_element = row.find('a')
                    link = link_element['href']
                    
                    ### Extract location
                    location_element = row.find('div', class_='job-location location')
                    location = location_element.text.strip() if location_element else 'Not specified'
                    
                    ### Extract Company
                    company_element = row.find('div', class_='job-listing-company company')
                    company = company_element.text.strip() if company_element else 'Not specified'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
            
            ### search for the next page
            next_page_element = soup.find('a', class_='next page-numbers')
            next_url = next_page_element['href'] if next_page_element and isinstance(next_page_element, Tag) else None
            print("Found next page element:", next_url)
            
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_abacus(self, url, keywords):
        """Crawl function for Abacus API"""
        print(f"Crawling Abacus API URL: {url}")

        try:
            ### Make the API request
            response = requests.get(url, headers=self.api_headers, timeout=10)

            ### Parse the response as a dictionary
            response_data = response.json()

            ### Check if 'html' key exists in the response
            if 'html' not in response_data:
                print("No HTML content found in the response")
                return [], None

            ### Parse the HTML content
            soup = BeautifulSoup(response_data['html'], 'html.parser')

            ### Look for job advertisement table or elements
            job_elements = soup.find_all('job-advertisement-table')

            content = []
            for job_element in job_elements:
                try:
                    ### Try to extract job data from the element's attributes
                    job_value = job_element.get('value', '')

                    ### URL decode the value
                    decoded_job_data = urllib.parse.unquote(job_value)

                    ### Parse the decoded job data
                    try:
                        jobs = json.loads(decoded_job_data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse job data: {decoded_job_data[:500]}")
                        continue

                    ### Process each job
                    for job in jobs:
                        title = job.get('JobTitle', 'No title')
                        location = job.get('u_b_jobs_xxx__userfield1', 'No location')
                        link = job.get('PublicationUrlAbacusJobPortal', '#')

                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if (any(keyword.lower() in title.lower() for keyword in keywords) and 
                            self.is_location_in_ostschweiz(location)):

                            job_entry = {
                                'title': title,
                                'link': link,
                                'company': 'Abacus',
                                'location': location,
                            }

                            content.append(job_entry)
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                except Exception as e:
                    print(f"Error processing job element: {e}")

            ### No pagination for this specific API
            next_url = None

            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None

                    
                    
    def crawl_STSG (self, url, keywords):
        """Crawl Function for Stadt St. Gallen or St.Galler Stadwerke"""
        print(f'Crawling Stadt St. Gallen / St.Galler Stadtwerke API URL: {url}')
        
        try:          
            ### Make the API request
            response = requests.get(url, headers=self.api_headers, timeout=10)
            
            ### Parse the response using utf-8-sig encoding to handle BOM
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                ### If standard JSON decoding fails, try with utf-8-sig
                data = json.loads(response.content.decode('utf-8-sig'))
            job_rows = data.get('jobs', []) ### get the jobs array safely
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### extract job details
                    title = job.get('title', {}).get('value', 'No title')
                    link_element = job.get('link', {})
                    if '../' in link_element :
                        link = 'https://live.solique.ch/STSG/de/' + link_element.replace('../', '')
                    else:    
                        link = 'https://live.solique.ch/STSG/de/' + job.get('link', {})
                    company = job.get('company', {}).get('value', 'No company')
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz, then append to content
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    
            Next_url = None
            
            print(f"Found {len(content)} jobs")
            return content, Next_url
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return [], None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [], None
    
    
    
    def crawl_valantic(self, url, keywords):
        """Function to crawl Valantic"""
        print(f"Crawling Valantic URL: {url}")
        
        ### List of all the different URL endings
        url_endings = [
            'cloud-aws/',
            'artificial-intelligence/',
            'crm/',
            'data-analytics/',
            'digital-marketing',
            'digital-platforms-e-commerce/',
            'digital-strategy/',
            'fintech/',
            'financial-services/',
            'internet-of-things/',
            'sap/',
            'cyber-security/',
            'strategy-management-consulting/',
            'backend-development/',
            'devops/',
            'frontend-development/',
            'quality-testing/',
            'it-support/',
            'second-level-support/',
            'system-administration/',
        ]
        
        try:
            content = []
            for ending in url_endings:
                response = requests.get(url + ending, headers=self.headers, timeout=10)
                
                ### Check if the response is successful
                response.raise_for_status()
                
                print(f"Response status for {url + ending}: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_rows = soup.find_all('a', class_="bg-white flex flex-col items-start w-full rounded pt-3.5 pb-4 px-5 pr-20 shadow-[0_10px_30px_0_rgba(0,0,0,0.08)] relative group z-10 hover:z-20")
                print(f"Found {len(job_rows)} job listings")
                for job in job_rows:
                    try:
                        ### Extract title
                        title = job.find('p', class_='text-2xl font-semibold group-hover:text-red').text.strip()
                        link = job['href']
                        location = job.find('li', class_='mt-1 text-base truncate text-black/40').text.strip()
                        company = 'Valantic'
                        
                        ### Check if any keyword is in the title and location is in Ostschweiz
                        if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                            content.append({
                                'title': title,
                                'link': link,
                                'company': company,
                                'location': location                                
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")
                            
                    except Exception as e:
                        print(f"Error during extraction: {e}")
                       
            next_url = None 
            print(f"Found {len(content)} jobs")
            return content, next_url
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_abraxas(self, url, keywords):
        """Crawl function for Abraxas"""
        print(f"Crawling Abraxas URL: {url}")

        try:
            # Create a session to manage cookies
            session = requests.Session()

            # First request to get the cookie consent page
            response = session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            print(f"Initial response status: {response.status_code}")

            # Check if there's a cookie consent form
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for consent button
            consent_button = soup.select_one('.js-jf-yellow-rd-active.all-active.force--consent.show--consent')
            print(f"Cookie consent dialog detected: {consent_button is not None}")

            if consent_button:
                print("Handling cookie consent...")
                # Set cookies that would typically be set after accepting
                cookies = {
                    'cookieconsent_status': 'allow',
                    'cookiecategory_optional': 'allow',
                    'cookiecategory_analytical': 'allow',
                    'cookiecategory_marketing': 'allow'
                }

                for name, value in cookies.items():
                    session.cookies.set(name, value, domain='abraxas.ch')

                # Make another request to get the actual page content
                response = session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                print(f"Post-consent response status: {response.status_code}")
                soup = BeautifulSoup(response.content, 'html.parser')
            else:
                print("No cookie consent dialog detected")

            print(f"Final response status: {response.status_code}")

            # Print the page title to help debug
            page_title = soup.title.string if soup.title else "No title found"
            print(f"Page title: {page_title}")

            # Try different selectors that might match job listings
            job_selectors = [
                'article.teaser',
                'div.teaser',
                'li.teaser',
                'div.job-teaser',
                'div.career-teaser',
                'div.job-listing',
                'li.vacancy-item',
                'div.job-position',
                '.job-card',
                '.position-card',
                'a[href*="stelle"]',
                'a.job-link'
                'li.job-list__list-item is-visible'
            ]

            job_rows = []
            used_selector = None

            for selector in job_selectors:
                temp_rows = soup.select(selector)
                if temp_rows:
                    job_rows = temp_rows
                    used_selector = selector
                    print(f"Found {len(temp_rows)} job listings using selector: {selector}")
                    break
                
            if not job_rows:
                # Look for links containing job-related keywords
                print("Trying to find job links using text content...")
                all_links = soup.find_all('a')
                job_links = []
                for link in all_links:
                    link_text = link.get_text().lower()
                    if any(kw in link_text for kw in ['stelle', 'job', 'position', 'karriere', 'vacancies']):
                        job_links.append(link)

                if job_links:
                    job_rows = job_links
                    used_selector = "text-based job links"
                    print(f"Found {len(job_links)} text-based job links")

            print(f"Found {len(job_rows)} potential job listings using {used_selector if used_selector else 'no matching selector'}")

            # If still empty, dump a sample of the HTML to debug
            if not job_rows:
                print("No job listings found. HTML sample:")
                html_sample = soup.prettify()[:1000]
                print(html_sample)

            content = []
            for job in job_rows:
                try:
                    # Extract based on what selector matched
                    if used_selector == "text-based job links":
                        title = job.get_text(strip=True)
                        link = job.get('href', '')
                        if isinstance(link, str) and link and not (link.startswith('http://') or link.startswith('https://')):
                            link = urllib.parse.urljoin(url, link)
                        location = 'St. Gallen'  # Default location for Abraxas
                    else:
                        # Try to extract title using various potential selectors
                        title_element = job.select_one('h2, h3, h4, .title, .job-title')
                        title = title_element.get_text(strip=True) if title_element else job.get_text(strip=True)

                        # Try to extract link
                        link_element = job.select_one('a') or job if job.name == 'a' else None
                        link = link_element.get('href', '') if link_element else ''
                        if isinstance(link, str) and link and not (link.startswith('http://') or link.startswith('https://')):
                            link = urllib.parse.urljoin(url, link)

                        # Try to extract location
                        location_element = job.select_one('.location, .job-location, .place')
                        location = location_element.get_text(strip=True) if location_element else 'St. Gallen'

                    company = 'Abraxas'

                    print(f"Extracted job: Title={title}, Location={location}")

                    # Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")

            next_url = None
            for job in content:
                if job['link'] == "https://www.abraxas.ch/de/karriere/lehrstellen-und-praktika":
                    print("Found the URL of Lehrstellen und Praktika")
                    next_url = job['link']
                    print(f"Next URL: {next_url}")
                    content.remove(job)
                    break
                
            print(f"Found {len(content)} matching jobs")
            return content, next_url

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_buehler(self, url, keywords):
        """Function to Crawl Buehler Group"""
        print(f"Crawling Buehler URL: {url}")
        
        try:
            response = requests.get(url, headers=self.api_headers, timeout=10)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
           
            
            job_rows = data.get('jobs', [])
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### Extract job details
                    title = job.get('title', '')
                    link = job.get('link', '')
                    
                    print(f"Extracted job: Title = {title}, Location = Uzwil")
                    
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': "Buehler Group",
                            'location': "Uzwil"
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_url = None
            print(f"Found {len(content)} jobs")
            return content, next_url
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_egeli(self, url, keywords):
        """Fucntion to crawl Egeli Informatik"""
        print(f"Crawling Egleli Informatik URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all('a', class_='row jobElement pt-2 pb-2 text-decoration-none')
                
            print(f"Found {len(job_rows)} job listings")
                
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'Egeli Informatik'

                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    return [], None
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_hoch(self, url, keywords, page_count):
        """Function to crawl Hoch"""
        print(f"Crawling Hoch Health Ostschweiz URL: {url}")
        
        ### Retry parameters
        max_retries = 3
        retry_count = 0
        backoff_time = 2
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            job_rows = soup.find_all('tr', class_='data-row')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a', class_='jobTitle-link').text.strip()
                    link = 'https://jobs.h-och.ch' + job.find('a')['href']
                    location = job.find('span', class_='jobLocation').text.strip()
                    company = 'Hoch Health Ostschweiz'
                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
                
            
            base_url = 'https://jobs.h-och.ch/search/'
            
            
            ### Find the link for the next page
            next_page_num = int(page_count) + 1
            next_page = soup.find('a', title=f'Seite {next_page_num}')
            if not next_page:
                print(f"No next page found. Last page reached.")
                next_page = None
                return content, next_page
            
            ### get url for the next page
            href_value = next_page['href'] if isinstance(next_page, Tag) and next_page.has_attr('href') else None
            next_url = base_url + href_value if isinstance(href_value, str) else None
            
            print(f'Moving to page {next_page_num}. Found next URL: {next_url}')
            
            print(f"Found {len(content)} jobs")
            return content, next_url

        except requests.Timeout as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = backoff_time * (2 ** (retry_count - 1)) # Exponential backoff
                print(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Max retries reached. Aborting...")
                return [], None 
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        

                    
    def crawl_inventx(self, url, keywords):
        """Function to crawl InventX"""
        print(f"Crawling InventX URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all(lambda tag: tag.name == 'div' and tag.has_attr('class') and 'row row-table' in ' '.join(tag.get('class', [])))     
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title = job.find('a').text.strip()
                link = job.find('a')['href']
                location = job.find('div', class_='inner').text.strip()
                company = 'InventX'

                ### Check if any keyword is in the title and location is in Ostschweiz
                if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_kms(self, url, keywords):
        """Function to crawl KMS"""
        print(f"Crawling KMS URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify()[:500])
            
            job_rows = soup.find_all('div', class_='job__content styled')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                title_element = job.find('div', class_='job__title h4')
                title = title_element.find('strong').text.strip() if title_element else 'No title'
                link = 'https://www.kms-ag.ch/karriere/offene-jobs/'
                company = 'KMS'
                location_elements = job.find_all('p')
                ### iterate though each p element to find location
                for location_element in location_elements:
                    location_element.text.strip()
                    if 'matzingen' in location_element.text.lower():
                        location = 'Matzingen'
                
                ### Check if any keyword is in the title
                if any(keyword.lower() in title.lower() for keyword in keywords):
                    content.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'location': location,
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_hexagon(self, url, keywords):
        """Function ot crawl Hexagon / Leica Systems"""
        print(f"Crawling Hexagon URL: {url}")
        
        try:
            ### API request
            response = requests.get(url, headers=self.api_headers, timeout=10)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
            
            ### Check if the response has the excepted content
            if 'Results' not in data:
                print("No result found in API structure")
                return [], None
            
            job_rows = data['Results']
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    html_content = job.get('Html', '')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    ### Get the <a> element with URL and Title in it
                    a_element = soup.find('a')
                    if not a_element:
                        print('No <a> element found in job listing')
                        continue
                    
                    title = a_element.text.strip()
                    link = a_element['href'] if isinstance(a_element, Tag) and a_element.has_attr('href') else 'No link'
                    company = "Leica Geosystems"
                    job_url_div = soup.find('div', class_='job-url')
                    if job_url_div:
                        location = job_url_div.next_sibling.strip() if job_url_div and isinstance(job_url_div.next_sibling, str) else 'No location'

                    ### Check if any keyword is in the title and location is in Ostschweiz
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_raiffeisen(self, url, keywords):
        """Function to Crawl Raiffeisen Schweiz"""
        print(f"Crawling Raiffeisen Schweiz API: {url}")
        
        try:
            ### Request the API page
            response = requests.get(url, self.api_headers, timeout=10)
            response.raise_for_status()
            
            ### Parse the json response
            data = response.json()
            
            ### Check if the response has the expected content of listed jobs
            job_rows = data['jobs']
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job['title']
                    link = job['links']['directlink']
                    location = job['attributes']['arbeitsort'][0]
                    company = 'Raiffeisen Schweiz'

                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        ### printing what is not matching
                        print(f"Title: {title}, Location: {location}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_sfs(self, url, keywords):
        """Function to crawl SFS"""
        print(f"Crawling SFS URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='molecule-responsive-datalist-entry values-are-copytext')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('strong', class_='highlight-on-interaction').text.strip()
                    link = 'https://join.sfs.com' + job['href']
                    
                    ### Extract location and company
                    loc_com_elements = job.find('span', class_='column grid-width-5')
                    expanded_columns = loc_com_elements.find_all('span', class_='column-value')
                    location = expanded_columns[0].text.strip()
                    company = loc_com_elements.find('strong').text.strip()
                        
                    ### Check if any keyword is in the title, location is in Ostschweiz and it's a IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_umantis(self, url, keywords):
        """Function to crawl Umantis"""
        print(f"Crawling Umantis URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
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

                    ### Extract location
                    if any(keyword.lower() and title.lower() for keyword in keywords) and self.is_it_job(title):
                        ### load the detailed job page to extract the location
                        load_job = requests.get(link, headers=self.headers)
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
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs in St.Gallen")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_acreo(self, url, keywords):
        """Function to crawl Acreo"""        
        print(f"Crawling Acreo URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_list = soup.find('ul', class_='grid-3')
            if job_list and isinstance(job_list, Tag):
                job_rows = job_list.find_all('li', class_='acreo-box-item')
            else:
                print("No valid job list found.")
                job_rows = []
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3').text.strip()
                    link = 'https://acreo.ch' + job.find('a')['href']
                    location = 'St. Gallen'
                    company = 'Acreo Consulting'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                           'title': title,
                           'link': link,
                           'location': location,
                           'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], next_page
        
    
    
    def crawl_allconsulting(self, url, keywords):
        """Function to crawl All Consulting"""
        print(f"Crawling All Consulting URL: {url}")
        
        try: 
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='link-arrow')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.text.strip()
                    link = 'https://all-consulting.ch' + job['href']
                    company = 'All Consulting'
                    
                    if 'St. Gallen' in title:
                        location = 'St. Gallen'
                    else:
                        location = 'unknown'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue

            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], next_page
            
     
    def crawl_aproda(self, url, keywords):
        """Function to crawl Aproda"""
        print(f"Crawling Aproda URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('article', class_='note')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3', class_='headline-five note-title').text.strip()
                    link = job.find('a', class_='button')['href']
                    company = 'Aproda'
                    location = 'St. Gallen / Rotkreuz'
                    
                    
                    
                    ### Check if any keyword is in the title, location is in ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_zoot(self, url, keywords):
        """Function to Craw Zoot Solutions"""
        print(f"Crawling Zoot Solutions URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='story--zoot-item')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h5', class_='title--h5-zoot').text.strip()
                    location = job.find('span', class_='story-location').text.strip()
                    link = url
                    company = 'Zoot Solutions'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    def crawl_stackworks(self, url, keywords,):
        """Function to crawl Stackworks"""
        print(f"Crawling Stackworks URL: {url}")
        
        try: 
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            job_rows = soup.find_all('div', class_='grid--jobs')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h4', class_='h6').text.strip()
                    link = 'https://www.stackworks.ch' + job.find('a', class_='job-item w-inline-block')['href']
                    location = job.find_all('div', class_='subline is--text is--grey is--jobs')[2].text.strip()
                    company = 'Stackworks'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_optisizer(self, url, keywords):
        """Function to crawl Optisizer"""
        print(f"Crawling Optisizer URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='body')
            print(f"Found {len(job_rows)} job listings")
            print(job_rows)
            
            content = []
            for job in job_rows:
                try: 
                    title_element = job.find('p', class_='loud')
                    if title_element:
                        if title_element.find('br'):
                            title_parts = title_element.get_text(separator='<br>').split('<br>')
                            title = title_parts[0].strip()
                        else:
                            print(f"Found no <br> tag. Extract whole text")
                            title = title_element.text.strip()
                            
                    else:
                        print("No title element found")

                    link = 'https://www.optisizer.ch' + job.find('a', class_='load')['href']
                    location = 'St. Gallen'
                    company = 'Optisizer'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_ari(self, url, keywords):
        """Function to crawl ARI AG"""
        print(f"Crawling ARI AG URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=30)
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
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
        
        
    def crawl_nextlevelconsulting(self, url, keywords):
        """Function to crawl Nextlevel Consulting"""
        print(f"Crawling Nextlevel Consulting URL: {url}")
        
        try:
            ### crate a session to keep cookies
            session = requests.Session()
            
            response = session.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            time.sleep(5)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            job_section = soup.find('div', class_='content-wrapper default-gap default-gap--small')
            print(f"Job section: {job_section}")
            if job_section and isinstance(job_section, Tag):
                print("looking for job_rows in job_section")
                job_rows = job_section.find_all('a', class_='teaser-item color-white-bg teaser-item--border teaser-item--border__effect')
            else:
                print("Job section is not valid or not found.")
                job_rows = []
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('div', class_='teaser-item__title h3').text.strip()
                    link = job['href']
                    location = job.find('div', class_='teaser-item__tags').text.strip()
                    company = 'Nextlevel Consulting'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_edorex(self, url, keywords):
        """Function to crawl Edorex"""
        print(f"Crawling Edorex URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_rows = soup.find_all(lambda tag: tag.name == 'li' and 
                                                tag.has_attr('class') and
                                                'wp-block-post' in ' '.join(tag.get('class', [])) and
                                                'shp_job_category-offene-stellen' in ' '.join(tag.get('class', [])))
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('h2', class_='wp-block-post-title has-medium-font-size')
                    title = title_element.find('a').text.strip()
                    link = title_element.find('a')['href']
                    company = 'Edorex'
                    location = 'St. Gallen / Ostermundingen'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_diselva(self, url, keywords):
        """Function to crawl Diselva"""
        print(f"Crawling Diselva URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_section = soup.find('div', class_='row-fluid-wrapper row-depth-1 row-number-2 dnd-section')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                job_rows = job_section.find_all(lambda tag: tag.name == 'div' and
                                              tag.has_attr('class') and
                                                'column item' in ' '.join(tag.get('class', [])))
            print(f"Found {len(job_rows)} job listings")
            
            
            content = []
            for job in job_rows[1:]:
                try: 
                    title = job.find('h3', class_='mt-4 title is-4 is-height-100px').text.strip()
                    link = job.find('a', class_='has-text-dark')['href']
                    company = 'Diselva'
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in the title and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    def crawl_app(self, url, keywords):
        """Function to crawl APP"""
        print(f"Crawling APP URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(soup.prettify())
            
            job_rows = []
            job_section = soup.find('section', id='offene-stellen')
            print(f"Job section: {job_section}")
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('div', class_='col-12 col-sm-6')
            else:
                print("Job section is not valid or not found.")
            print(f"Found {len(job_rows)} job listings")
            
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobs__label').text.strip()
                    link = job.find('a', class_='jobs__entry')['href']
                    location = job.find('span', class_='jobs__condition').text.strip()
                    company = 'APP'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
          
          
    def crawl_advision(self, url, keywords):
        """Function to crawl AdVision""" 
        print(f"Crawling AdVision URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('section', class_='job-list-area')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('div', class_='col-lg-6 col-md-6')
            else:
                print("Job section is not valid or not found.")
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h3').text.strip()
                    link = job.find('a')['href']
                    location = 'Gossau'
                    company = 'AdVision'
                    
                    ### Check if any keyword is in the title and job is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
                  
    
    def crawl_xerxes(self, url, keywords):
        """Function to crawl Xerxes"""
        print(f"Crawling Xerxes URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', id='c481')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('a')
            else:
                print("Job section is not valid or not found.")
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('span').text.strip()
                    link = 'https://www.xerxes.ch' + job['href']
                    company = 'Xerxes'
                    location = 'Appenzell'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_webwirkung(self, url, keywords):
        """Function to crawl Webwirkung"""
        print(f"Crawling Webwirkung URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='wp-block-columns is-layout-flex wp-container-core-columns-is-layout-1 wp-block-columns-is-layout-flex')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('section', class_='block block-core block-core--paragraph')
            else:
                print("Job section is not valid or not found.")
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a').text.strip()
                    link = job.find('a')['href']
                    company = 'Webwirkung'
                    location = 'Wil'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_stgallennetgroup(self, url, keywords):
        """Function to crawl St. Gallen Netgroup"""
        print(f"Crawling St. Gallen Netgroup URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('section', attrs={'data-id':'120b2d23'})
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('a')
            else:
                print("Job section is not valid or not found.")
                
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.text.strip()
                    link = job['href']
                    company = 'St. Gallen Netgroup'
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_robotron(self, url, keywords):
        """Function to crawl Robotron"""
        print(f"Crawling Robotron URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='contentcontainer-column')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('p')
            else:
                print("Job section is not valid or not found.")
            
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    ### Create a copy of the job element
                    import copy
                    job_copy = copy.copy(job)
                    
                    ### Remove the anchor tag from the copy
                    if job_copy.find('a'):
                        job_copy.find('a').decompose()
                    
                    title = job_copy.text.strip()
                    link = 'https://www.robotron.ch' + job.find('a')['href']
                    company = 'Robotron'
                    location = 'Wil'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    
    def crawl_joshmartin(self, url, keywords):
        """Function to crawl JoshMartin"""
        print(f"Crawling JoshMartin URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('section', class_='block special-job-entries')
            print(f"Job section: {job_section}")
            job_rows = []
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows")
                job_rows = job_section.find_all('li')
            else:
                print("Job section is not valid or not found.")
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h4').text.strip()
                    link = job.find('a')['href']
                    company = 'JoshMartin'
                    location = 'St. Gallen'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'location': location
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_farner(self, url, keywords):
        """Function to crawl Farner"""
        print(f"Crawling Farner URL: {url}")
        
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=15)
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
                                if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                                    content.append({
                                        'title': title,
                                        'link': link,
                                        'location': location,
                                        'company': company
                                    })
                                    print(f"Found matching job: {title}")
                                else:
                                    print(f"Skipping non-matching job: {title}")
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
                                    
    
    
    def crawl_dynanet(self, url, keywords):
        """Function to crawl DynaNet"""
        print(f"Crawling DynaNet URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all section elements with class 'spaltenlayout'
            layout_sections = soup.find_all('section', class_='spaltenlayout')
            print(f"Found {len(layout_sections)} layout sections")
            
            # Make sure we have at least 2 sections
            if len(layout_sections) < 2:
                print("Couldn't find the second layout section")
                return [], None
                
            # Get the second section (index 1)
            job_section = layout_sections[1]
            print(f"Job section: {job_section}")
            
            # Find job listings within this section
            job_rows = job_section.find_all('div', class_='columns')
            print(f"Found {len(job_rows)} job listings")
            
            content = []
            for job in job_rows:
                try:
                    # Try to find a job title and link
                    title_element = job.find('h3') or job.find('h4') or job.find('strong')
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    
                    # Look for link
                    link_element = job.find('a')
                    link = link_element['href'] if link_element else url
                    if not (link.startswith('http://') or link.startswith('https://')):
                        link = 'https://dynanet.ch' + link
                        
                    location = 'St. Gallen'
                    company = 'DynaNet'
                    
                    # Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
                    
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
            
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
   
   
   
    def crawl_dachcom(self, url, keywords):
        """Function to crawl Dachcom"""
        print(f"Crawling Dachcom URL: {url}")
        
        try:            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='toolbox-element toolbox-job-list')
            print(f"Job section: {job_section}")

            ### Check if the job section is valid            
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('a', class_='toolbox-job-list--item blocklink job-list-item fx-fly-up')
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('div', class_='toolbox-job-list--title a icon-link link-arrow-right link-arrow-larger').text.strip()
                    link = 'https://www.dachcom.com' + job['href']
                    location = job.find('span', class_='toolbox-job-list--spacer').text.strip()
                    company = 'Dachcom'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
   
   
    
    def crawl_adesso(self, url, keywords):
        """Function to crawl Adesso"""
        print(f"Crawling Adesso URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', class_='real_table_container')
            print(f"Job section: {job_section}")
            
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all(lambda tag : tag.name == 'tr' and tag.has_attr('class') and 
                                                'alternative' in ' '.join(tag.get('class', [])))
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                title = job.find('a').text.strip()
                
                link_element = job.find('a')['href']
                if link_element.startswith('http://') or link_element.startswith('https://'):
                    link = link_element
                else:
                    link = 'https://www.adesso.ch' + link_element
                
                location = job.find('td', class_='real_table_col2').text.strip()
                company = 'Adesso'
                
                ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                    content.append({
                        'title': title,
                        'link': link,
                        'location': location,
                        'company': company
                    })
                    print(f"Found matching job: {title}")
                else:
                    print(f"Skipping non-matching job: {title}")
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    
    def crawl_unisg(self, url, keywords):
        """Function to crawl UniSG"""
        print(f"Crawling UniSG URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('section', id='jobResults')
            if job_section and isinstance(job_section, Tag):
                print(f"Job section: {job_section}")
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('div', class_='eight wide computer column eight wide tablet column sixteen wide mobile column')
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('a')
                    if title_element:
                        title = title_element.find('h1').text.strip()
                        link = title_element['href']
                    else:
                        print("No title element found")
                    
                    location = 'St. Gallen'
                    company = 'UniSG'
                    
                    ### Check if any keyword is in the title and it is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                        
            
    
    def crawl_svasg(self, url, keywords):
        """Function to crawl SVA St. Gallen"""
        print(f"Crawling SVA St. Gallen URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all(lambda tag: tag.name == 'tr' and
                                        tag.has_attr('class') and
                                        'nav-row' in ' '.join(tag.get('class', [])))
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a').text.strip()
                    link = job.find('a')['href']
                    location = 'St. Gallen'
                    company = 'SVA St. Gallen'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
    
    
    def crawl_sgkb(self, url, keywords):
        """Function to crawl St.Galler Kantonalbank"""
        print(f"Crawling St.Galler Kantonalbank URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='searchitem')
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h4').text.strip()
                    link = 'https://www.sgkb.ch' + job['href']
                    
                    location_element = job.find_all('div', class_='col-12 col-md-4')[0]
                    if location_element:
                        #print(f"Location element: {location_element}")
                        location = location_element.find('p').text.strip()
                    else:
                        print("No location element found")
                    
                    company = 'St.Galler Kantonalbank'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
        
        
    
    def crawl_sak(self, url, keywords):
        """Function to crawl SAK"""
        print(f"Crawling SAK URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_section = soup.find('div', id='job-table')
            print(f"Job section: {job_section}")
            
            if job_section and isinstance(job_section, Tag):
                print(f"Job section is valid. Looking for job rows.")
                job_rows = job_section.find_all('tr', class_='data-row')
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job rows found in the job section.")
            else:
                print("Job section is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a').text.strip()
                    link = 'https://karriere.sak.ch' + job.find('a')['href']
                    location = job.find('span', class_='jobLocation').text.strip()
                    company = 'SAK'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title) and self.is_location_in_ostschweiz(location):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page

        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
                    
                    
    def crawl_psg(self, url, keywords):
        """Function to crawl Psychiatrie St. Gallen"""
        print(f"Crawling Psychiatrie St. Gallen URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='job')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('div', class_='jobTitle')
                    title = title_element.find('h2').text.strip() if title_element else ''
                    link = job['href']
                    location = job.find('div', class_='jobArbeitsOrt').text.strip()
                    
                    ### check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': 'Psychiatrie St. Gallen'
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                        
                    
                    
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def craw_permapack(self, url, keywords):
        """Function to crawl PermaPack"""
        print(f"Crawling PermaPack URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='row')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'PermaPack'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                
    
    
    def crawl_optimatik(self, url, keywords):
        """Function to crawl Optimatik"""
        print(f"Crawling Optimatik URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='red-highlight-box clearfix')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('div', class_='right-col').text.strip()
                    link = job.find('a', class_='ico-class')['href']
                    location = 'Teufen'
                    company = 'Optimatik'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_oertli(self, url, keywords):
        """Function to crawl Oertli"""
        print(f"Crawling Oertli URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('div', class_='joboffer_container')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
                
            content = []
            for job in job_rows:
                try:
                    title = job.find('a').text.strip()
                    link = job.find('a')['href']
                    location = job.find('div', class_='joboffer_informations joboffer_box').text.strip()
                    company = 'Oertli'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_obt(self, url, keywords):
        """Function to crawl OBT"""
        print(f"Crawling OBT URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_segment = soup.find('div', class_='Jobs__content')
            print(f"found job segment")
            if job_segment and isinstance(job_segment, Tag):
                job_element = job_segment.find_all('div', class_='Jobs__cardEntries | js-entries')[3]
                print(f"found Job Element {job_element}")
                if job_element and isinstance(job_element, Tag):
                    print(f"Job element is valid. Looking for job rows.")
                    job_rows = job_element.find_all('div', class_='Jobs__cardEntriesItem | js-entry')
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("Job element is not valid or not found.")
            else:
                print("Job segment is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('h6', class_='Jobs__cardEntriesItemTitle').text.strip()
                    link = 'https://www.obt.ch' +  job.find('a')['href']
                    location = job.find('div', class_='Jobs__cardEntriesInfoPointTitle').text.strip()
                    company = 'OBT'
                    
                    ### Check if keyword is in title, if job is in Ostschweiz and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_netsafe(self, url, keywords):
        """Function to crawl Netsafe"""
        print(f"Crawling Netsafe URL: {url}")
        
        try: 
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_element = soup.find('div', id='jobs_grid')
            
            if job_element and isinstance(job_element, Tag):
                print(f"Job element is valid. Looking for job rows.")
                #print(f"Job element: {job_element}")
                job_rows = job_element.find_all(lambda tag: tag.name == 'a' and
                                         tag.has_attr('class') and 
                                        'text-decoration-none' in ' '.join(tag.get('class', [])))
                if job_rows:
                    print(f"Found {len(job_rows)} job rows")
                    #print(f"Job rows: {job_rows}")
                else:
                    print("No job rows found in the job element.")
            else:
                print("Job element is not valid or not found.")
                
            content = []
            for job in job_rows:
                try:
                    title_element = job.find('h3', class_='text-secondary mt0 mb4')
                    title = title_element.find('span').text.strip() if title_element else ''
                    link = 'https://www.netsafe.ch' + job['href']
                    #print(f"Link: {link}")
                    location = job.find('span', class_='w-100 o_force_ltr d-block').text.strip()
                    company = 'Netsafe'
                    
                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_neovac(self, url, keywords):
        """Function to crawl Neovac"""
        print(f"Crawling Neovac URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_sections = soup.find_all('div', class_='toolbox-element toolbox-job-overview')
            print(f"Found {len(job_sections)} job sections")
            #print(f"Job section: {job_section}")
            
            for job_section in job_sections:
                if job_section and isinstance(job_section, Tag):
                    print(f"Job section is valid. Looking for job rows.")
                    #print(f"Job section: {job_section}")

                    ### Find the script element with the x-data attribute
                    script_data = job_section.get('x-data', '')

                    ### Extract jo data from JavaScript object (second parameter in jobfiltering)
                    if script_data:
                        ### Find the JSON array of jobs - it's the second parameter in the jobfiltering function
                        pattern = r'jobFiltering\(.+?, (\[.*?\])\)'
                        if isinstance(script_data, str):
                            match = re.search(pattern, script_data, re.DOTALL)
                        else:
                            match = None

                        if match:
                            job_json = match.group(1)
                            try: 
                                job_data = json.loads(job_json)
                                print(f"Succssfully extracted {len(job_data)} jobs from JavaScript object")

                                content = []
                                for job in job_data:
                                    title = job.get('jobTitle', '')
                                    link = job.get('detailLink', '')
                                    location = job.get('placeOfWork', '')
                                    company = 'Neovac'

                                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                                        content.append({
                                            'title': title,
                                            'link': link,
                                            'location': location,
                                            'company': company
                                        })
                                        print(f"Found matching job: {title}")
                                    else:
                                        print(f"Skipping non-matching job: {title}")
                                next_page = None
                                print(f"Found {len(content)} jobs")
                                return content, next_page
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")
                        else:
                            print("No job data found in the JavaScript object")
                    else:
                        print("No x-data attribute found in the job section") 
                else:
                    print("Job section is not valid or not found.")
            
            return [], None
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_mtf(self, url, keywords):
        """Function to crawl MTF"""
        print(f"Crawling MTF URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('article', id='page-job-138')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('span', class_='row row-1').text.strip()
                    link = job.find('a', class_='object-link')['href']
                    location = job.find('span', class_='job-places').text.strip()
                    company = 'MTF'
                    
                    ### check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
    
    
    
    def crawl_msdirect(self, url, keywords):
        """Function to crawl MSDirect"""
        print(f"Crawling MSDirect URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all(lambda tag: tag.name == 'div' and
                                        tag.has_attr('class') and
                                        'row nav-row' in ' '.join(tag.get('class', [])))
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
                
            content = []
            for job in job_rows:
                try:
                    ### extract title 
                    title = job.find('a', class_='nav-item font').text.strip()
                    if title:
                        print(f"Title element: {title}")
         
                    ### extract link   
                    link_element = job.find('a', class_='nav-item font')['href']
                    if link_element.startswith('/'):
                        link = 'https://msdirectgroup-jobs.abacuscity.ch' + link_element
                    else:
                        link = link_element
                        
                    ### extract location
                    location = job.find('span', class_='nav-filter jobsfiltercolumncontent cl6a9b5550-033d-74d4-f2f2-1b0e19589c4f').text.strip()
                    if location:
                        print(f"Location element: {location}")
                    
                    ### extract company                 
                    company = job.find('span', class_='nav-filter jobsfiltercolumncontent clada51a77-64c4-e8dc-646e-40de4a1d6ce3').text.strip()
                    
                    ### check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
                    
    
    
    def crawl_metrohm(self, url, keywords):
        """Function to crawl Metrohm"""
        print(f"Crawling Metrohm API: {url}")
        
        try:
            response = requests.get(url, headers=self.api_headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            job_rows = data['results']
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
                #print(f"Job rows: {job_rows}")
            else:
                print("No job rows found in the job section.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.get('title', '')
                    link = 'https://www.metrohm.com' + job.get('url', '')
                    company = 'Metrohm'
                    location = 'Herisau'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
    
    
    def crawl_merkle(self, url, keywords):
        """Function to crawl Merkle using Selenium"""
        print(f"Crawling Merkle URL {url}")       

        ### Crawl this page with selenium because JS-rendered content
        try:
            ### Import Selenium libraries
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            import time

            ### Set up Chrome in headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")

            ### Initialize the Chrome driver
            print("Initializing Chrome driver...")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            content = []
            try:
                ### Load the page with Selenium
                print(f"Loading job listing page: {url}")
                driver.get(url)

                ### Wait for the page to load completely
                wait = WebDriverWait(driver, 20)
                time.sleep(5)  # Additional wait for all JS to execute

                ### Get page source after JavaScript has rendered the content
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                ### Check if the jobs are loaded
                job_segment = soup.find('section', class_='css-27w6p6')
                if job_segment and isinstance(job_segment, Tag):
                    print("Job segment found. Looking for job rows.")
                    job_rows = job_segment.find_all('li', class_='css-1q2dra3')
                    print(f"Found {len(job_rows)} job rows")
                else:
                    print("No job segment found. Looking for alternative selectors.")
                    ### Try alternative selectors if the expected structure isn't found
                    job_rows = soup.find_all('a', attrs={'data-automation-id': 'jobTitle'})
                    print(f"Found {len(job_rows)} job rows with alternative selector")

                ### Process each job
                for job in job_rows:
                    try:
                        if job.name == 'li':
                            title = job.find('a', class_='css-19uc56f').text.strip()
                            link = 'https://dentsuaegis.wd3.myworkdayjobs.com' + job.find('a')['href']
                        else:
                            ### Alternative structure
                            title = job.text.strip()
                            link = 'https://dentsuaegis.wd3.myworkdayjobs.com' + job['href']

                        print(f"Processing job: {title}")
                        company = 'Merkle'

                        ### Visit job detail page
                        print(f"Loading job details page: {link}")
                        driver.get(link)
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        ### Wait for page to load
                        time.sleep(3)  

                        ### Get location information from the job detail page
                        job_detail_source = driver.page_source
                        job_soup = BeautifulSoup(job_detail_source, 'html.parser')

                        location_elements = job_soup.find_all('dd', class_='css-129m7dg')
                        location = "Unknown Location"
                        for location_element in location_elements:
                            loc_text = location_element.text.strip()
                            print(f"Found location element: {loc_text}")
                            location = loc_text
                            if self.is_location_in_ostschweiz(loc_text):
                                print(f"Location is in Ostschweiz: {loc_text}")
                                location = loc_text
                                break
                            
                        ### Check if job matches criteria
                        if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                            content.append({
                                'title': title,
                                'link': link,
                                'location': location,
                                'company': company
                            })
                            print(f"Found matching job: {title}")
                        else:
                            print(f"Skipping non-matching job: {title}")

                    except Exception as e:
                        print(f"Error processing job: {e}")
                        continue

                next_page = None
                print(f"Found {len(content)} matching jobs")
                return content, next_page

            finally:
                ### close the driver
                print("Closing Chrome driver")
                driver.quit()

        except Exception as e:
            print(f"Error during crawl: {e}")
            traceback.print_exc()
            return [], None
            
            
                                
    def crawl_kellenberger(self, url, keywords):
        """Function to crawl Kellenberger"""    
        print(f"Crawling Kellenberger URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup.prettify())
            
            job_segment = soup.find('div', class_='vacancy-list__items vacancy-list__items--grouped-by-name')
            if job_segment and isinstance(job_segment, Tag):
                print(f'Job segment is valid. Looking for job rows.')
                job_rows = job_segment.find_all('div', class_='vacancy-list__item')
                print(f"Found {len(job_rows)} job rows")
            else:
                print("Job segment is not valid or not found.")
            
            content = []
            for job in job_rows:
                try:
                    title = job.find('a', class_='vacancy__title-link').text.strip()
                    link = 'ttps://management.ostjob.ch' + job.find('a')['href']
                    location = job.find('span', class_='vacancy__workplace-city').text.strip()
                    company = 'Kellenberger'
                    
                    ### Check if any keyword is in the title and if it's an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None
            
        
    
    def crawl_laveba(self, url, keywords):
        """Function to crawl Laveba Genossenscahft"""
        print(f"Crawling Laveba URL: {url}")
        
        try: 
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('a', class_='row jobElement pt-2 pb-2 text-decoration-none')
            if job_rows:
                print(f"Found {len(job_rows)} job rows")
            else:
                print("No job rows found in the job section.")
            
            content = []    
            for job in job_rows:
                try:
                    title = job.find('span', class_='jobName').text.strip()
                    link = 'https://jobs.dualoo.com/portal/' + job['href']
                    location = job.find('span', class_='cityName').text.strip()
                    company = 'Laveba'

                    ### Check if any keyword is in the title, location is in Ostschweiz and is an IT job
                    if any(keyword.lower() in title.lower() for keyword in keywords) and self.is_location_in_ostschweiz(location) and self.is_it_job(title):
                        content.append({
                            'title': title,
                            'link': link,
                            'location': location,
                            'company': company
                        })
                        print(f"Found matching job: {title}")
                    else:
                        print(f"Skipping non-matching job: {title}")
                except Exception as e:
                    print(f"Error during extraction: {e}")
                    continue
            next_page = None
            print(f"Found {len(content)} jobs")
            return content, next_page
        
        except Exception as e:
            print(f"Error during crawl: {e}")
            return [], None

    
        
   
    def __del__(self):
        """Destructor to safely close database connection"""
        try:
            self._close_connection()
        except Exception as e:
            print(f"Error closing database connection: {e}")
            

if __name__ == "__main__":
    ### Testing the crawler
    crawler = Crawler()
    keywords = ['praktikum', 'werkstudent', 'praktika', 'verkauf']
    url = 'https://www.benedict.ch/stellen/'
    crawler.crawl(url, keywords)