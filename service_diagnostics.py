import win32serviceutil
import win32service
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_service(service_name):
    """Inspect service configuration and status"""
    try:
        # Get service status
        status = win32serviceutil.QueryServiceStatus(service_name)
        
        # Map status code to readable string
        state_map = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "START PENDING",
            win32service.SERVICE_STOP_PENDING: "STOP PENDING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUE PENDING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSE PENDING",
            win32service.SERVICE_PAUSED: "PAUSED"
        }
        current_state = state_map.get(status[1], f"UNKNOWN ({status[1]})")
        logger.info(f"Current State: {current_state}")
        
        # Get service configuration
        config = win32service.QueryServiceConfig(service_name)
        start_types = {
            win32service.SERVICE_AUTO_START: "Automatic",
            win32service.SERVICE_DEMAND_START: "Manual",
            win32service.SERVICE_DISABLED: "Disabled",
            win32service.SERVICE_BOOT_START: "System Boot",
            win32service.SERVICE_SYSTEM_START: "System Start"
        }
        
        logger.info("\nService Configuration:")
        logger.info(f"  Display Name: {service_name}")
        logger.info(f"  Binary Path: {config[3]}")
        logger.info(f"  Start Type: {start_types.get(config[1], f'Unknown ({config[1]})')}")
        logger.info(f"  Account: {config[7]}")
        
        # Check if binary exists
        binary_path = config[3].strip('"').split()[0]
        if Path(binary_path).exists():
            logger.info(f"  Binary file exists: {binary_path}")
            
            # Get file details
            file_stat = Path(binary_path).stat()
            logger.info(f"  File size: {file_stat.st_size} bytes")
            logger.info(f"  Last modified: {file_stat.st_mtime}")
        else:
            logger.error(f"  Binary file not found: {binary_path}")
        
        # Try to get additional service details
        try:
            description = win32service.QueryServiceConfig2(service_name, win32service.SERVICE_CONFIG_DESCRIPTION)
            if description:
                logger.info(f"  Description: {description}")
        except:
            pass
            
        return True
    except Exception as e:
        logger.error(f"Error inspecting service: {str(e)}")
        return False

if __name__ == "__main__":
    # List all services for reference
    logger.info("Scanning for installed services...")
    try:
        scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
        services = win32service.EnumServicesStatus(scm_handle, win32service.SERVICE_WIN32, win32service.SERVICE_STATE_ALL)
        win32service.CloseServiceHandle(scm_handle)
        crawler_services = [svc for svc in services if "crawler" in svc[0].lower()]
        
        if crawler_services:
            logger.info("\nFound crawler-related services:")
            for service in crawler_services:
                logger.info(f"  - {service[0]}")
                inspect_service(service[0])
        else:
            logger.warning("No crawler-related services found")
            
    except Exception as e:
        logger.error(f"Error listing services: {str(e)}")

    # Also try to inspect specific service
    SERVICE_NAME = "JobCrawlerService"
    logger.info(f"\nInspecting specific service: {SERVICE_NAME}")
    inspect_service(SERVICE_NAME)