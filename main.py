import eel
from database import Database
from crawler import Crawler
import os
import sys
import logging
from gui import CrawlerGUI
from startup_utils import add_to_startup, remove_from_startup, is_in_startup

### Get the application root directory
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

### Set up logging directory in AppData
appdata = os.getenv('APPDATA')
if appdata is None:
    # Fallback to a directory next to the executable if APPDATA is not available
    LOG_DIR = os.path.join(APP_DIR, 'logs')
else:
    LOG_DIR = os.path.join(appdata, 'JobCrawler')

if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except Exception as e:
        print(f"Error creating log directory: {e}")

### Set up logging
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOG_DIR, 'crawler.log')),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    print(f"Error setting up logging: {e}")
    
logger = logging.getLogger('WebInterface')


### Initialize eel with your web files directory
db_path = os.path.join(APP_DIR, "crawls.db")  ### Set the path to the database file
db = Database(db_path) ### pass the db_path to the database
crawler = Crawler(db_path) ### pass the db_path to the crawler
    

@eel.expose
def crawl(url, keywords): 
    ### Adding crawl logic
    try:
        logger.info(f"Starting crawl for {url} with keywords: {keywords}")
        results = crawler.crawl(url, keywords)
        return results
    except Exception as e:
        logger.error(f"Error crawling {url}: {e}")
        return {"status": "error", "message": str(e)}
    
    
@eel.expose
def add_crawl(title, url, scheduleTime, scheduleDay, keywords):
    ### Adding a new crawl logic
    try:
        logger.info(f"Adding crawl: {title}")
        result = db.add_crawl(title, url, scheduleTime, scheduleDay, keywords)
        return result
    except Exception as e:
        logger.error(f"Error adding crawl: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def delete_crawl(crawl_id):
    ### Add your delete logic here
    try:
        logger.info(f"Deleting crawl: {crawl_id}")
        result = db.delete_crawl(crawl_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting crawl: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def update_crawl(crawl_id, title, url, scheduleTime, scheduleDay, keywords):
    ### Add your update logic here
    try:
        logger.info(f"Updating crawl: {crawl_id}")
        result = db.update_crawl(crawl_id, title, url, scheduleTime, scheduleDay, keywords)
        return result
    except Exception as e:
        logger.error(f"Error updating crawl: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def get_crawls():
    ### Adding crawl_logic
    try:
        logger.info("Getting all crawls")
        crawls = db.get_all_crawls()
        logger.debug(f"Loaded crawls: {crawls}")
        return crawls
    except Exception as e:
        logger.error(f"Error getting crawls: {e}")
        return {"status": "error", "message": str(e)}
    

@eel.expose
def add_email(email):
    ### Add email logic
    try:
        logger.info(f"Adding email: {email}")
        result = db.add_email(email)
        return result
    except Exception as e:
        logger.error(f"Error adding email: {e}")
        return {"status": "error", "message": str(e)}
    

@eel.expose
def get_emails():
    ### Get all emails
    try:
        logger.info("Getting all emails")
        emails = db.get_email()
        return emails
    except Exception as e:
        logger.error(f"Error getting emails: {e}")
        return {"status": "error", "message": str(e)}
    

@eel.expose
def delete_email(email_id):
    ### Delete email
    try:
        logger.info(f"Deleting email: {email_id}")
        result = db.delete_email(email_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting email: {e}")
        return {"status": "error", "message": str(e)}
        

### Start the application in installation mode
##def install_service():
##    try:
##        win32serviceutil.InstallService(
##            pythonClassString="service.CrawlerService",
##            serviceName="JobCrawlerService",
##            displayName="Job Crawler Service",
##            startType=win32service.SERVICE_AUTO_START
##        )
##        logger.info("Service installed successfully with auto-start enabled")
##    except Exception as e:
##        logger.error(F"Error installing service: {e}")
    

@eel.expose
def toggle_startup():
    """Toggle the application's startup status"""
    try:
        if is_in_startup():
            success = remove_from_startup()
            return {"status": "success", "enabled": False} if success else {"status": "error"}
        else:
            success = add_to_startup()
            return {"status": "success", "enabled": True} if success else {"status": "error"}
    except Exception as e:
        logger.error(f"Error toggling startup: {e}")
        return {"status": "error", "message": str(e)} 


@eel.expose
def get_startup_status():
    """Get the current startup status"""
    try:
        return {"status": "success", "enabled": is_in_startup()}
    except Exception as e:
        logger.error(f"Error getting startup status: {e}")
        return {"status": "error", "message": str(e)}
    
    
def start_gui():
    app = CrawlerGUI()
    app.run()


def main():
    ### Start the GUI
    start_gui()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        sys.exit(1)