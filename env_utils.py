import os
import logging

### Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_env_file():
    """
    Ensure .env file exists in the JobCrawler AppData directory.
    Creates a tempalte .env file if it doesn't exist.
    
    Returns:
    str: Path to the created or existing .env file
    """
    try:
        ### Get AppData path
        appdata = os.getenv('APPDATA')
        if not appdata:
            logging.error("APPDATA environment varaible not set")
            return None
        
        ### Create JobCrawler directory if it doesn't exists
        jobcrawler_dir = os.path.join(appdata, 'JobCrawler')
        os.makedirs(jobcrawler_dir, exist_ok=True)
        
        ### Define .env file path
        env_path = os.path.join(jobcrawler_dir, '.env')
        
        ### Chekc if .env file already exists
        if not os.path.exists(env_path):
            ### Create a template .env file
            with open(env_path, 'w') as f:
                f.write("# SMTP configuration fo JobCrawler\n")
                f.write("SMTP_SERVER=smtp.gmail.com")
                f.write("SMTP_PORT=587")
                f.write("SMTP_USERNAME=sevibuhler@gmail.com")
                f.write("SMTP_PASSWORD=dwdy cwss xjrx vezu")
            
            logging.info(f"Created template .env file at {env_path}")
        else:
            logging.info(f".env file already exists at {env_path}")
        return env_path
    
    except Exception as e:
        logging.error(f"Error creating .env file: {e}")
        return None