import os
import sys
import logging

logger = logging.getLogger(__name__)

def get_db_path():
    """
    Get teh database path based on wether the applicaton is running in development or production mode.
    
    Returns:
        str: The absolute path to the database file
    """
    
    try:
        ### Check if we're running in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            ### We're in production mode
            appdata = os.getenv('APPDATA')
            if appdata is None:
                raise EnvironmentError(f"APPDATA environment variable is not set")
            
            ### Create teh application directory in AppData
            app_dir = os.path.join(appdata, 'JobCrawler')
            os.makedirs(app_dir, exist_ok=True)

            ### Return the full path to the database
            db_path = os.path.join(app_dir, 'crawls.db')
            
        else:
            ### We're in development mode
            ### Use the curent directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, 'crawls.db')
            
        ### Ensure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"Database path set to: {db_path}")
        return db_path
    except Exception as e:
        logger.error(f"Error determining database path: {e}")
        raise