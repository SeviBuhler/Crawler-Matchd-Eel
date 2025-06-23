import eel
from database import Database
from crawler import Crawler
import os
import sys
import logging
import pystray
from PIL import Image
import threading
from schedule import CrawlerScheduler
import threading
import time

### Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WebInterface')

### Get the application root directory
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

class CrawlerGUI:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS # type: ignore
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
                        
        self.db = Database()
        self.crawler = Crawler(self.db.db_file)
        self.icon = None
        self.eel_thread = None
        self.eel_started = False
        self.current_port = None
        self.chrome_pid = None 
        self.is_shutting_down = False
        self.scheduler = None      
        
        ### Ensure the icon exists before starting the tray
        self.icon_path = os.path.join(str(self.base_path), 'image.ico')
        if not os.path.exists(self.icon_path):
            logger.error(f"Icon not found: {self.icon_path}")
            raise FileNotFoundError(f"Icon not found: {self.icon_path}")
        
        self.setup_tray()
        
        ### Start background initialization
        self.init_thread = threading.Thread(target=self.background_init, daemon=True)
        self.init_thread.start()  
        
        
    def background_init(self):
        """Initialize heavy components in the background"""
        logger.info("Background initialization started")
        start_time = time.time()
        
        try:
            ### Initialize database
            self.db = Database()
            
            def delayed_init():
                self.crawler = Crawler(self.db.db_file)
                self.start_scheduler()

            threading.Thread(target=delayed_init, daemon=True).start()
            print(f"Background initialization completed in {time.time() - start_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Background initialization failed: {e}")
            
    
    def open_gui(self, icon, item):
        """Open the Gui in a new thread"""
        logger.info("Attempting to open GUI...")
        
        if not self.eel_started:
            self.eel_thread = threading.Thread(target=self.start_eel)
            self.eel_thread.daemon = True
            self.eel_thread.start()
            logger.info("Started new GUI thread")
        else:
            logger.info("GUI thread already running")
            
    
    def setup_tray(self):
        try:
            logger.info("Setting up tray icon...")
            image = Image.open(self.icon_path)
            
            def create_menu():
                return (
                    pystray.MenuItem("Open Application", self.open_gui),
                    pystray.MenuItem("Exit", self.exit_app)
                )
                
            self.icon = pystray.Icon(
                name="Job Crawler",
                icon=image,
                title="Job Crawler",
                menu=create_menu()
            )
            logger.info("Tray icon created successfully")
        
        except Exception as e:
            logger.error(f"Error setting up tray: {e}")
            raise
            
        
    def start_eel(self):
        """Start the eel web interface in seperate thread"""
        import socket
        
        def find_free_port():
            """Find a free port to use"""
            for port in range(8000, 8020):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(('localhost', port))
                        return port
                    except OSError:
                        continue
            return None
        
        def run_eel():
            """Run the Eel web interface"""
            try:
                if getattr(sys, 'frozen', False):
                    web_path = os.path.join(sys._MEIPASS, 'web') # type: ignore
                else:
                    web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

                if not os.path.exists(web_path):
                    raise Exception(f"Web path not found: {web_path}")

                logger.info(f"Starting eel with path: {web_path}")

                ### Find an available port
                port = find_free_port()
                if port is None:
                    raise Exception("No available ports found")

                self.current_port = port
                logger.info(f"Using port: {port}")

                ### Initialize new Eel instance
                eel.init(web_path, allowed_extensions=['.js', '.html', '.css'])
                
                appdata_dir = os.getenv('APPDATA')
                if appdata_dir:
                    chrome_data_dir = os.path.join(appdata_dir, 'JobCrawler', 'chrome_data')
                else:
                    # Fallback zu temp directory
                    import tempfile
                    chrome_data_dir = os.path.join(tempfile.gettempdir(), 'JobCrawler_chrome_data')
                
                # Stelle sicher dass das Verzeichnis existiert
                os.makedirs(chrome_data_dir, exist_ok=True)
                logger.info(f"Chrome data directory: {chrome_data_dir}")

                try:
                    options = {
                        'mode': 'chrome',
                        'port': port,
                        'size': (1200, 800),
                        'disable_cache': True,
                        'cmdline_args': [
                            '--disable-http-cache',
                            f'--user-data-dir={chrome_data_dir}',
                            '--new-window', 
                            '--disable-features=PromptOnExit'
                        ]
                    }

                    eel.start('index.html', **options)

                except (SystemExit, KeyboardInterrupt):
                    logger.info("Eel window closed normally")
                except Exception as e:
                    logger.error(f"Error starting eel: {e}")

            except Exception as e:
                logger.error(f"Error starting eel: {e}")
            finally:
                self.cleanup_eel()

        ### Use therading to run Eel
        eel_thread = threading.Thread(target=run_eel, daemon=True)
        eel_thread.start()
        
        self.eel_started = True
                
    
    def cleanup_eel(self):
        """Clean up Eel resources"""
        logger.info("Starting Eel cleanup")
        try:
            ### Reset instance state
            self.eel_started = False
            self.eel_thread = None
            self.current_port = None
            
            ### Clean up Chrome data directory
            appdata_dir = os.getenv('APPDATA')
            if appdata_dir:
                chrome_data_dir = os.path.join(appdata_dir, 'JobCrawler', 'chrome_data')
            else:
                import tempfile
                chrome_data_dir = os.path.join(tempfile.gettempdir(), 'JobCrawler_chrome_data')
                
            if os.path.exists(chrome_data_dir):
                try:
                    import shutil
                    shutil.rmtree(chrome_data_dir, ignore_errors=True)
                except Exception as e:
                    logger.error(f"Error cleaning up Chrome data: {e}")
                                
            import gc
            gc.collect()
                    
        except Exception as e:
            logger.error(f"Error cleaning up Eel: {e}")
        finally:
            logger.info("Eel cleanup complete")  
        
        
    def exit_app(self):
        """Clean up resources and exit the application if the user selects exit in the tray menu"""
        logger.info("Exiting application")
        self.is_shutting_down = True
        
        try:
            ### Clean Eel if its running
            if self.eel_started:
                self.cleanup_eel()
            
            ### Stop the scheduler
            self.stop_scheduler()
            
            ### Stop the icon
            if self.icon:
                self.icon.stop()
                
            ### Close database connection
            if hasattr(self, 'db'):
                self.db.close()
            
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error shutting down application: {e}")
        finally:
            ### Use os._exit to avoid the SystemExit exception
            os._exit(0)
        
        
    def stop_scheduler(self):
        """Stop the scheduler and perform cleanpu"""
        if self.scheduler:
            try:
                if self.scheduler.scheduler.running:
                    self.scheduler.stop()
                    logger.info("Scheduler stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
            finally:
                self.scheduler = None
    
    
    def start_scheduler(self):
        """Start the scheduler"""
        if not self.scheduler:
            try:
                self.scheduler = CrawlerScheduler()
                self.scheduler.start()
                logger.info("Scheduler started")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
                self.scheduler = None            
        
        
    def run(self):
        logger.info("Start application")
        try:
            if self.icon is None:
                raise RuntimeError("Icon not properly initialized")
            self.icon.run()
        except Exception as e:
            logger.error(f"Error running application: {e}")
            self.stop_scheduler()
            raise