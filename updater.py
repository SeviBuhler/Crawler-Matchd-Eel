import winreg
import requests
import os
import sys
import subprocess
import logging

### Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_install_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BHM\JobCrawler")
        path = winreg.QueryValueEx(key, "InstallLocation")[0]
        logger.info(f"INstall path found: {path}")
        return path
    except WindowsError:
        logger.warning("Could not find install path in registry, using executable directory")
        return os.path.dirname(sys.executable)


def check_github_update():
    repo_url = "https://api.github.com/repos/SeviBuhler/Crawler-Matchd-Eel/releases/latest"
    current_version = "0.1.2"  # Store in app or registry
    
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        latest = response.json()
        
        logger.info(f"Current version: {current_version}")
        logger.info(f"Latest version: {latest['tag_name']}")
    
        if latest['tag_name'] > current_version:
            logger.info("Update available")
            return latest['assets'][0]['browser_download_url']
        
        logger.info("No update available")
        return None
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return None
    

def update_app():
    try:
        update_url = check_github_update()
        if update_url:
            logger.info(f"Downloading update from: {update_url}")
            setup = requests.get(update_url)
            setup.raise_for_status()
            
            setup_path = os.path.join(get_install_path(), "update_setup.exe")

            with open(setup_path, "wb") as f:
                f.write(setup.content)
            
            logger.info(f"Update download to: {setup_path}")

            subprocess.run([setup_path, "/SILENT"])
            os.remove(setup_path)
            sys.exit()
        else:
            logger.info("No updates performed")
    except Exception as e:
        logger.error(f"Update failed: {e}")
        

if __name__ == "__main__":
    update_app()  # Run at startup