import winreg
import requests
import os
import sys
import logging
import re
import tkinter as tk
from tkinter import messagebox
from version import get_current_version, set_current_version

### Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_version_info_file(new_version):
    """
    Update the version_info_file.txt with new version information
    """
    try:
        ### Determine the path to version_info_file.txt
        if getattr(sys, 'frozen', False):
            ### If running as compiled executabel
            base_path = os.path.dirname(sys.executable)
            logger.info(f"Executable path: {sys.executable}")
            logger.info(f"Base Path is: {base_path}")
            version_file_path = r"C:\Program Files\JobCrawler\_internal\version_info_file.txt"
        else:
            ### If running in development
            base_path = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Base Path is: {base_path}")
            version_file_path = os.path.join(base_path, "version_info_file.txt")
                
        logger.info(f"Attempting to update version file at: {version_file_path}")
        logger.info(f"File exists: {os.path.exists(version_file_path)}")
        
        ### Read the current version info file
        with open(version_file_path, 'r') as file:
            content = file.read()
        
        logger.info(f"Original file content: {content}")
        
        clean_version = new_version.lstrip('v')
        
        version_parts = clean_version.split('.')
        while len(version_parts) < 4:
            version_parts.append('0')
            
        version_tuple = tuple(map(int, version_parts[:4]))
        
        #### Replace file and product versions (numeric tuples)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'filevers=' in line:
                lines[i] = f'    filevers={version_tuple},'
            elif 'prodvers=' in line:
                lines[i] = f'    prodvers={version_tuple},'
            elif "StringStruct('FileVersion'," in line:
                lines[i] = f"        StringStruct('FileVersion', 'v{clean_version}'),"
            elif "StringStruct('ProductVersion'," in line:
                lines[i] = f"        StringStruct('ProductVersion', 'v{clean_version}')])"
                
        updated_content = '\n'.join(lines)
        
        ### Write back to the file
        with open(version_file_path, 'w') as file:
            file.write(updated_content)
        
        logger.info("Succesfully updated version info file")
        return True
    
    except Exception as e:
        logger.error(f"Error updating version info file: {e}")
        return False


def compare_versions(v1, v2):
    """
    Compare version strings
    Removes 'v' prefix and handles semantic versioning
    """
    ### Remove 'v' prefix if present
    v1 = v1.lstrip('v')
    v2 = v2.lstrip('v')
    
    ### Split versions into components
    v1_parts = [int(x) for x in re.findall(r'\d+', v1)]
    v2_parts = [int(x) for x in re.findall(r'\d+', v2)]
    
    ### Pad shorter version with zeros
    max_length = max(len(v1_parts), len(v2_parts))
    v1_parts += [0] * (max_length - len(v1_parts))
    v2_parts += [0] * (max_length - len(v2_parts))
    
    ### Compare version components
    for a, b in zip(v1_parts, v2_parts):
        if a > b:
            return 1
        elif a < b:
            return -1
    return 0


def get_install_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BHM\JobCrawler")
        path = winreg.QueryValueEx(key, "InstallLocation")[0]
        logger.info(f"Install path found: {path}")
        return path
    except WindowsError:
        logger.warning("Could not find install path in registry, using executable directory")
        return os.path.dirname(sys.executable)


def check_github_update():
    repo_url = "https://api.github.com/repos/SeviBuhler/Crawler-Matchd-Eel/releases/latest"
    current_version = get_current_version()
    
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        latest = response.json()
        
        latest_version = latest.get('tag_name', '')
        logger.info(f"Current version: {current_version}")
        logger.info(f"Latest version: {latest['tag_name']}")
    
        if compare_versions(latest_version, current_version) > 0:
            ### Ensure assets exist and have download URL's
            if latest.get('assets') and latest['assets'][0].get('browser_download_url'):
                logger.info("Update available")
                return {
                    'url': latest['assets'][0]['browser_download_url'],
                    'version': latest_version
                }
            else:
                logger.warning("No valid download URL found")
        
        logger.info("No update available")
        return None
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return None
    

def update_app():
    try:
        update_info = check_github_update()
        if update_info:
            ### Show update notifiaction
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True) ### Brint the prompt to the front
            
            ### Show meassage box
            response = messagebox.askyesno(
                "Update available",
                f"A new version {update_info['version']} for your JobCrawler is available.\n\nDo you want to install the update now?\n\nPlease follow the installation window that will open."
            )
            root.attributes("-topmost", False) ### Remove the topmost attribute
            
            if response: 
                logger.info(f"Downloading update from: {update_info}")
                setup = requests.get(update_info['url'])
                setup.raise_for_status()

                ### Use a temporary file to store the setup
                temp_dir = os.path.join(os.getenv('TEMP') or '', 'JobCrawlerUpdate')
                os.makedirs(temp_dir, exist_ok=True)
                setup_path = os.path.join(temp_dir, "SetupJobCrawler.exe")

                with open(setup_path, "wb") as f:
                    f.write(setup.content)

                logger.info(f"Update download to: {setup_path}")

                ### Run the installer with elevation
                try:                    
                    ### Use ShellExecute to with potential elevation
                    import subprocess
                    try:
                        subprocess.Popen(setup_path)
                        logger.info("Setup started")
                    except Exception as e:
                        logger.error(f"Error starting installer: {e}")
                        return False
                    
                    ### Update version before
                    set_current_version(update_info['version'])
                    update_version_info_file(update_info['version'])
                    
                    logger.info("Update downloaded.")
                    sys.exit()
                except Exception as e:
                    logger.error(f"Error running installer: {e}")
                    return False
            
            root.destroy()
            return False
        
        else:
            logger.info("No updates performed")
            return False
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False
        

if __name__ == "__main__":
    update_app()  ### Run for testing