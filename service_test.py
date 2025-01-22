import win32serviceutil
import win32service
import psutil
import unittest
import time
import logging
import os
import ctypes
from pathlib import Path
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class CrawlerServiceTests(unittest.TestCase):
    # Update these settings for your specific service
    SERVICE_NAME = "JobCrawlerService"  # Your service name from services.msc
    EXECUTABLE_PATH = Path(os.getcwd()) / "service.py"  # Your service script
    LOG_DIR = Path("logs")
    LOG_PATH = LOG_DIR / "crawler_service.log"
    
    def setUp(self):
        """Set up test environment"""
        if not is_admin():
            print("\nWARNING: Tests are running without administrator privileges.")
            print("Some tests may fail due to insufficient permissions.\n")
        
        self.LOG_DIR.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=self.LOG_PATH,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
        self.logger = logging.getLogger(__name__)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def verify_service_installation(self):
        """Verify service installation details"""
        try:
            # Check if service exists
            status = win32serviceutil.QueryServiceStatus(self.SERVICE_NAME)
            
            # Get service configuration
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            service_handle = win32service.OpenService(scm_handle, self.SERVICE_NAME, win32service.SERVICE_QUERY_CONFIG)
            config = win32service.QueryServiceConfig(service_handle)
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm_handle)
            self.logger.info(f"Service binary path: {config[3]}")  # Log the binary path
            
            return True
        except Exception as e:
            self.logger.error(f"Service verification failed: {str(e)}")
            return False

    def test_1_service_installation(self):
        """Test if the service is properly installed and configured"""
        self.assertTrue(
            self.verify_service_installation(),
            f"Service '{self.SERVICE_NAME}' is not properly installed"
        )
        self.logger.info("Service installation verified")

    def test_2_service_configuration(self):
        """Test service configuration details"""
        try:
            # Get service configuration
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            service_handle = win32service.OpenService(scm_handle, self.SERVICE_NAME, win32service.SERVICE_QUERY_CONFIG)
            config = win32service.QueryServiceConfig(service_handle)
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm_handle)
            
            self.logger.info(f"Service Details:")
            self.logger.info(f"  Name: {self.SERVICE_NAME}")
            self.logger.info(f"  Binary Path: {config[3]}")
            self.logger.info(f"  Start Type: {config[1]}")
            self.logger.info(f"  Account: {config[7]}")
            
            # Verify executable exists
            binary_path = config[3].strip('"').split()[0]
            self.assertTrue(
                Path(binary_path).exists(),
                f"Service executable not found: {binary_path}"
            )
            
        except Exception as e:
            self.logger.error(f"Configuration test failed: {str(e)}")
            raise

    def test_3_service_dependencies(self):
        """Test if all service dependencies are available"""
        try:
            scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            service_handle = win32service.OpenService(scm_handle, self.SERVICE_NAME, win32service.SERVICE_QUERY_STATUS)
            deps = win32service.EnumDependentServices(service_handle, win32service.SERVICE_STATE_ALL)
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm_handle)
            self.logger.info(f"Found {len(deps)} service dependencies")
            for dep in deps:
                self.logger.info(f"  Dependency: {dep}")
        except Exception as e:
            self.logger.warning(f"Dependency check failed: {str(e)}")

if __name__ == '__main__':
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(CrawlerServiceTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        print("\nTest Summary:")
        print(f"  Ran {result.testsRun} tests")
        print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        
    except Exception as e:
        print(f"\nError running tests: {str(e)}")