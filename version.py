import os
import json

VERSION_FILE = os.path.join(os.getenv('APPDATA', ''), 'JobCrawler', 'version.json')

def get_current_version():
    """Retrieve the current version"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
        
        # If version file doesn't exist, create it with initial version
        if not os.path.exists(VERSION_FILE):
            set_current_version("1.0.1")
        
        # Read version from file
        with open(VERSION_FILE, 'r') as f:
            version_data = json.load(f)
        return version_data.get('version', "1.0.1")
    
    except Exception as e:
        print(f"Error reading version: {e}")
        return "1.0.1"  # Fallback version

def set_current_version(new_version):
    """Update the current version"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
        
        # Write new version
        with open(VERSION_FILE, 'w') as f:
            json.dump({"version": new_version}, f)
        return True
    
    except Exception as e:
        print(f"Error updating version: {e}")
        return False