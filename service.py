import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import logging
from schedule import CrawlerScheduler

def setup_logging():
    ### Get the application root directory
    if getattr(sys, 'frozen', False):
        APP_DIR = os.path.dirname(sys.executable)
    else:
        APP_DIR = os.path.dirname(os.path.abspath(__file__))
    
    ### Try get APPDATA path, fall back to APP_DIR if not available
    appdata = os.getenv('APPDATA')
    if appdata is not None:
        log_dir = os.path.join(appdata, 'JobCrawler', 'logs')
    else:
        log_dir = os.path.join(APP_DIR, 'logs')
    
    ### Create the log directory if it doesn't exist
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    except Exception as e:
        ### If we can't create the log directory in APPDATA, fall back to app directory
        log_dir = os.path.join(APP_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    ### Set up logger
    logger = logging.getLogger('JobCrawlerService')
    logger.setLevel(logging.INFO)
    
    ### Create handler with the log file path
    log_file = os.path.join(log_dir, 'service.log')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    ### Add the handler to the logger
    logger.addHandler(handler)
    
    return logger

class CrawlerService(win32serviceutil.ServiceFramework):
    """Windows Service that runs scheduled crawls in the background"""
    _svc_name_ = 'JobCrawlerService'
    _svc_display_name_ = 'Job Crawler Service'
    _svc_description_ = 'Runs scheduled crawls in the background'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(120)
        self.is_alive = True
        self.scheduler = None
        
        self.logger = setup_logging()
         
    def SvcStop(self):
        """Gets called when the service is asked to stop"""
        try:
            self.logger.info('Stopping service...')
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.is_alive = False
            
            ### Stop the scheduler if it exists
            if self.scheduler:
                try:
                    self.scheduler.stop()
                    self.logger.info("Scheduler stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error stopping scheduler: {e}")
        
            self.logger.info("Service stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
        
    
    def SvcDoRun(self):
        """Called when the service is asked to start"""
        try:
            self.logger.info('Starting service...')
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            
            ### Initialize and start the scheduler
            self.scheduler = CrawlerScheduler()
            self.scheduler.start()
            
            ### Report that we're running
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.logger.info('Service started successfully')
            
            ### Main service loop
            while self.is_alive:
                ### Wait for the stop event or timeout after 1 second
                rc = win32event.WaitForSingleObject(self.stop_event, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    ### Stop event triggered
                    break
            
        except Exception as e:
            self.logger.error(f"Service error: {str(e)}")
            raise
        finally:
            if self.scheduler:
                try:
                    self.scheduler.stop()
                    self.logger.info("Scheduler stopped")
                except Exception as e:
                    self.logger.error("Error stopping scheduler during shutdown: {e}")
    

if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(CrawlerService)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as e:
            if e.winerror == 1063: ### ERROR_FAILED_SERVICE_CONTROLLER_CONNECT
                win32serviceutil.usage()
    else:
        win32serviceutil.HandleCommandLine(CrawlerService)