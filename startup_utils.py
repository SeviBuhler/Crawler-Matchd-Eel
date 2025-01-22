import winreg
import sys
import os
import logging

logger = logging.getLogger('StartupUtils')


def get_executable_path():
    """Get the path to the executable"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Try to find the compiled executable
        app_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(app_dir, 'dist', 'JobCrawler', 'JobCrawler.exe'),
            os.path.join(app_dir, 'JobCrawler.exe'),
            os.path.join(os.path.dirname(app_dir), 'JobCrawler.exe')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # If no executable found, log error and return None
        logger.error("Could not find JobCrawler.exe")
        return None
    

def add_to_startup():
    """Add the application to Windows startup"""
    try:
        # Get the path to the executable
        app_path = get_executable_path()
        if not app_path:
            logger.error("Could not add to startup")
            return False
        logger.info(f"Adding to startup: {app_path}")
            
        ### Prepare the registry key
        key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        try:
            ### Open the registry key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            ### if running as exe, ensure proper quoting
            if not app_path.startswith('"'):
                app_path = f'"{app_path}"'
            
            ### Set the registry value
            winreg.SetValueEx(
                key,
                "JobCrawler",  # Name in startup
                0,
                winreg.REG_SZ,
                app_path
            )
            
            winreg.CloseKey(key)
            logger.info("Successfully added to startup")
            return True
            
        except WindowsError as e:
            logger.error(f"Error adding to startup: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in add_to_startup: {e}")
        return False


def remove_from_startup():
    """Remove the application from Windows startup"""
    try:
        ### Prepare the registry key
        key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        try:
            ### Open the registry key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            ### Delete the registry value
            winreg.DeleteValue(key, "JobCrawler")
            winreg.CloseKey(key)
            logger.info("Successfully removed from startup")
            return True
            
        except WindowsError as e:
            logger.error(f"Error removing from startup: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in remove_from_startup: {e}")
        return False

def is_in_startup():
    """Check if the application is in Windows startup"""
    try:
        key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, "JobCrawler")
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
                
        except WindowsError:
            return False
            
    except Exception as e:
        logger.error(f"Error checking startup status: {e}")
        return False