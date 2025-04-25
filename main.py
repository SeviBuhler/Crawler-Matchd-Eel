import eel
from database import Database
from crawler import Crawler
import os
import sys
import logging
from gui import CrawlerGUI
from startup_utils import add_to_startup, remove_from_startup, is_in_startup
from env_utils import ensure_env_file
from updater import update_app
from datetime import datetime, timedelta



### Get the application root directory
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

### Set up logging directory in AppData
appdata = os.getenv('APPDATA')
if appdata:
    LOG_DIR = os.path.join(appdata, 'JobCrawler', 'logs')
else:
    # Fallback to current directory in development
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

os.makedirs(LOG_DIR, exist_ok=True)

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


def get_app_data_path():
    """Get the application data directory path"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        appdata = os.getenv('APPDATA')
        if appdata is None:
            raise EnvironmentError("APPDATA environment variable is not set")
        app_data = os.path.join(appdata, 'JobCrawler')
    else:
        # Running in development
        app_data = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the directory exists
    os.makedirs(app_data, exist_ok=True)
    return app_data


# Modified main.py startup code
def setup_application():
    """Set up the application with proper database initialization"""
    try:
        ### Create and initalize database
        db = Database()
        if not os.path.exists(db.db_file):
            db.initialize_database()
        
        # Create crawler instance
        crawler = Crawler(db.db_file)
        
        return db, crawler
        
    except Exception as e:
        logging.error(f"Error setting up application: {e}")
        raise


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


@eel.expose
def get_email_settings():
    """Get email settings"""
    try: 
        settings = db.get_email_settings()
        return settings
    except Exception as e:
        logger.error(f"Error getting email settings: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def update_email_settings(email_time):
    """Update email settings"""
    try:
        ### Validate timezone
        import re
        if not re.match(r'^\d{2}:\d{2}$', email_time):
            return {"status": "error", "message": "Invalid time format. Use HH:MM."}
        
        ### Update the settings in the database
        result = db.update_email_settings(email_time)
        return result
    
    except Exception as e:
        logger.error(f"Error updating email settings: {e}")
        return {"status": "error", "message": str(e)}


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


@eel.expose
def get_dashboard_stats():
    """Get statistics for the dashboard"""
    try:
        global db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Active jobs count
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE is_active = 1")
        stats['active_jobs'] = cursor.fetchone()[0]
        
        # New jobs today
        cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE DATE(crawl_date) = ?", (today,))
        stats['new_jobs_today'] = cursor.fetchone()[0]
        
        # Removed jobs today
        cursor.execute("SELECT COUNT(*) FROM removed_jobs WHERE DATE(removal_date) = ?", (today,))
        stats['removed_jobs_today'] = cursor.fetchone()[0]
        
        # Active crawls count
        cursor.execute("SELECT COUNT(*) FROM crawls")
        stats['active_crawls'] = cursor.fetchone()[0]
        
        # Jobs per website
        cursor.execute("""
            SELECT c.title, COUNT(cr.id) 
            FROM crawl_results cr
            JOIN crawls c ON cr.crawl_id = c.id
            WHERE cr.is_active = 1
            GROUP BY c.title
            ORDER BY COUNT(cr.id) DESC
            LIMIT 10
        """)
        stats['jobs_per_website'] = cursor.fetchall()
        
        # Recent crawls
        cursor.execute("""
            SELECT c.title, MAX(cr.crawl_date) as last_crawl,
                   (SELECT 1 FROM crawl_results WHERE crawl_id = c.id LIMIT 1) as success
            FROM crawls c
            LEFT JOIN crawl_results cr ON c.id = cr.crawl_id
            GROUP BY c.title
            ORDER BY last_crawl DESC
            LIMIT 10
        """)
        stats['recent_crawls'] = cursor.fetchall()
        
        # Job trends for the last 7 days
        dates = []
        new_jobs = []
        removed_jobs = []
        
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            
            # New jobs for this date
            cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE DATE(crawl_date) = ?", (date,))
            new_jobs.append(cursor.fetchone()[0])
            
            # Removed jobs for this date
            cursor.execute("SELECT COUNT(*) FROM removed_jobs WHERE DATE(removal_date) = ?", (date,))
            removed_jobs.append(cursor.fetchone()[0])
        
        stats['job_trends'] = {
            'dates': dates,
            'new_jobs': new_jobs,
            'removed_jobs': removed_jobs
        }
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            'active_jobs': 0,
            'new_jobs_today': 0,
            'removed_jobs_today': 0,
            'active_crawls': 0,
            'jobs_per_website': [],
            'recent_crawls': [],
            'job_trends': {'dates': [], 'new_jobs': [], 'removed_jobs': []}
        } 
    
def start_gui():
    app = CrawlerGUI()
    app.run()


def main():
    ### Check for updates
    try:
        update_app()
    except Exception as e:
        logging.error(f"Update check failed: {e}")
        
    ### Ensure .env file exists before astarting the application
    env_file = ensure_env_file()
    if not env_file:
        logging.warning("Could not create .env file. SMTP notifications may not work.")
        
    ### Start the GUI
    start_gui()


if __name__ == "__main__":
    try:
        db, crawler = setup_application()
        main()
    except Exception as e:
        logging.exception(f"Critical error: {e}")
        sys.exit(1)