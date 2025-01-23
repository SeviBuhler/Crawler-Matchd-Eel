import winreg
import requests
import os
import sys
import subprocess
from cryptography.fernet import Fernet

def get_install_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BHM\JobCrawler")
        path = winreg.QueryValueEx(key, "InstallLocation")[0]
        return path
    except WindowsError:
        return os.path.dirname(sys.executable)

def check_github_update():
    repo_url = "https://api.github.com/repos/SeviBuhler/Crawler-Matchd-Eel/releases/latest"
    current_version = "0.1.1"  # Store in app or registry
    
    response = requests.get(repo_url)
    latest = response.json()
    
    if latest['tag_name'] > current_version:
        return latest['assets'][0]['browser_download_url']
    return None

def update_app():
    if update_url := check_github_update():
        setup = requests.get(update_url)
        setup_path = os.path.join(get_install_path(), "update_setup.exe")
        
        with open(setup_path, "wb") as f:
            f.write(setup.content)
            
        subprocess.run([setup_path, "/SILENT"])
        os.remove(setup_path)
        sys.exit()

if __name__ == "__main__":
    update_app()  # Run at startup