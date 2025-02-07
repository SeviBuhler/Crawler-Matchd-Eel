import winreg
import requests
import os
import sys
import subprocess
import logging
import re
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
        ### Read the current version info file
        with open('version_info_file.txt', 'r') as file:
            content = file.read()
        
        ### Parse version string into 4-component tuple
        def version_to_tuple(version):
            version = version.lstrip('v')
            parts = version.split('.')
            while len(parts) < 4:
                parts.append('0')
            return tuple(map(int, parts[:4]))
        
        version_tuple = version_to_tuple(new_version)
        
        ### Replace file and product versions (numeric tuples)
        content = re.sub(
            r'filevers=\([\d, ]+\)', 
            f'filevers={version_tuple}', 
            content
        )
        content = re.sub(
            r'prodvers=\([\d, ]+\)', 
            f'prodvers={version_tuple}', 
            content
        )
        
        ### Replace string versions
        content = re.sub(
            r'StringStruct\(\'FileVersion\', \'[\d.]+\'\)', 
            f"StringStruct('FileVersion', '{new_version}')", 
            content
        )
        content = re.sub(
            r'StringStruct\(\'ProductVersion\', \'[\d.]+\'\)', 
            f"StringStruct('ProductVersion', '{new_version}')", 
            content
        )
        
        ### Write back to the file
        with open('version_info_file.txt', 'w') as file:
            file.write(content)
        
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
        logger.info(f"INstall path found: {path}")
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
                return latest['assets'][0]['browser_download_url']
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
            logger.info(f"Downloading update from: {update_info}")
            setup = requests.get(update_info)
            setup.raise_for_status()
            
            setup_path = os.path.join(get_install_path(), "update_setup.exe")

            with open(setup_path, "wb") as f:
                f.write(setup.content)
            
            logger.info(f"Update download to: {setup_path}")

            subprocess.run([setup_path, "/SILENT"])
            
            ### Update the version after successful update
            set_current_version(update_info['version'])
            
            os.remove(setup_path)
            sys.exit()
        else:
            logger.info("No updates performed")
    except Exception as e:
        logger.error(f"Update failed: {e}")
        

if __name__ == "__main__":
    update_app()  ### Run for testing