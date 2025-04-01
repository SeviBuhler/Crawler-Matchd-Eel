from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from pytz import timezone
import sqlite3
from crawler import Crawler
import logging
from email_notification import send_daily_email_report
from database_config import get_db_path
import threading

### Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Scheduler')


class CrawlerScheduler:
    def __init__(self):
        self.db_path = get_db_path()
        self.thread_local = threading.local()
        self.scheduler = BackgroundScheduler()
        self.timezone = timezone('Europe/Zurich')
        self.daily_crawls_complete = False
        self.active_crawls = set()
        self.today_crawls_completed = set() ### Saves IDs of crawls completed today
        self.email_job_id = 'daily_email_report'
        
        
    
    def _get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.thread_local, 'connection'):
            self.thread_local.connection = sqlite3.connect(self.db_path)
        return self.thread_local.connection

    def _close_connection(self):
        """Close the thread-local connection if it exists"""
        if hasattr(self.thread_local, 'connection'):
            self.thread_local.connection.close()
            del self.thread_local.connection
    
    
    def start(self):
        """Start the scheduler and load all crawls from database"""
        try:
            ### Checks the settins 
            self.scheduler.add_job(
                self.check_settings,
                'interval',
                minutes=1,
                id='settings_checker'
            )
            
            ### Check crawls every minute for updates
            self.scheduler.add_job(
                self.update_crawl_schedules,
                'interval',
                minutes=1,
                id='crawl_schedule_updater'
            )
            
            ### Get the email time from database and plan the job
            self.schedule_email_job()
                        
            ### Load all crawls from database
            self.update_crawl_schedules()
            
            ### Start the scheduler
            self.scheduler.start()
            print('Scheduler started successfully')
            
        except Exception as e:
            print(f'Error starting scheduler: {e}')
    
    
    def schedule_email_job(self):
        """Function to plan the daily email job based on database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ### check if settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                logger.error("Settings table does not exist")
                email_time = '15:30'  ### Default time
            else:
                ### Get the email time from the settings table
                cursor.execute("SELECT value FROM settings WHERE name='email_time'")
                result = cursor.fetchone()
                email_time = "15:30" if result is None else result[0]
            
            ### Parse the email time
            hour, minute = map(int, email_time.split(':'))
            
            ### Remove existing email job if it exists
            try:
                self.scheduler.remove_job(self.email_job_id)
            except:
                pass
            
            ### Add the new email job
            self.scheduler.add_job(
                self.send_daily_report,
                CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
                id=self.email_job_id
            )
            
            reset_minute = (minute + 5) % 60
            reset_hour = hour + ((minute +5) // 60)
            
            ### Reset completed crawls list at daily report time
            self.scheduler.add_job(
                self.reset_daily_tracking,
                CronTrigger(hour=reset_hour, minute=reset_minute, timezone=self.timezone),
                id='reset_daily_tracking'
            )
            
            logger.info(f"Email job scheduled at {email_time} successfully")
        except Exception as e:
            logger.error(f"Error scheduling email job: {e}")
        finally:
            self._close_connection()

    
    
    def reset_daily_tracking(self):
        """Reset the tracking of completed crawls fot the new day"""
        self.today_crawls_completed = set()
        logger.info('Daily crawls tracking reset')
        self.schedule_email_job()
            
    
    
    def send_daily_report(self):
        """Send daily email report reardless of crawl status"""
        try:
            send_daily_email_report(self.db_path)
            logger.info('Daily email report sent successfully')
        except Exception as e:
            logger.error(f'Error sending daily email report: {e}')
    
    
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info('Scheduler stopped successfully')
        except Exception as e:
            logger.error(f'Error stopping scheduler: {e}')
            
    
    
    def update_crawl_schedules(self):
        """Check database for crawls and update scheduler accordingly"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ### Get all crawls with their keywords
            cursor.execute("""
                SELECT c.id, c.title, c.url, c.scheduleTime, c.scheduleDay, 
                       GROUP_CONCAT(k.keyword) as keywords
                FROM crawls c
                LEFT JOIN keywords k ON c.id = k.crawl_id
                GROUP BY c.id
            """)
            crawls = cursor.fetchall()
            
            ### Get currently scheduled job IDs
            system_jobs = {'crawl_schedule_updater', 'settings_checker', 'daily_email_report', 'reset_daily_tracking'}
            scheduled_jobs = {job.id for job in self.scheduler.get_jobs() if job.id not in system_jobs and job.id.startswith('crawl_')}
            
            for crawl in crawls:
                crawl_id, title, url, scheduleTime, scheduleDay, keywords = crawl
                job_id = f'crawl_{crawl_id}'
                
                ### Parse schedule time
                hour, minute = map(int, scheduleTime.split(':')) 
                days_list = scheduleDay.split(',')
                keywords_list = keywords.split(',') if keywords else []
                
                ### Create cron trigger
                trigger = CronTrigger(
                    day_of_week=','.join(days_list),
                    hour=hour,
                    minute=minute,
                    timezone=self.timezone
                )

                ### Add or update job
                if job_id in scheduled_jobs:
                    self.scheduler.reschedule_job(
                        job_id, 
                        trigger=trigger
                    )
                    scheduled_jobs.remove(job_id)
                else:
                    self.scheduler.add_job(
                        self.execute_crawl,
                        trigger=trigger,
                        args=[crawl_id, url, keywords_list],
                        id=job_id,
                        name=title
                    )
            
            for job_id in scheduled_jobs:
                self.scheduler.remove_job(job_id)
                
            conn.close()
            
        except Exception as e:
            print(f'Error updating crawl schedules: {e}')
        finally:
            self._close_connection()
    
    
    def check_settings(self):
        """Checks the settings table for any changes"""
        try:
            ### Check the actual settings in the database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ### Check for existing settings table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                ### If settings dont exist, no changes are made
                return 
            
            ### Get Actual email time 
            cursor.execute("SELECT value FROM settings WHERE name='email_time'")
            result = cursor.fetchone()
            current_email_time = result[0] if result else "15:30"
            
            ### Save the previous email time and check if it changed
            if not hasattr(self, 'previous_email_time'):
                self.previous_email_time = current_email_time
                return
            
            ### Only if the email time changed, reschedule the job
            if current_email_time != self.previous_email_time:
                logger.info(f"Email time changed from {self.previous_email_time} to {current_email_time}")
                self.previous_email_time = current_email_time
                self.schedule_email_job()
            
        except Exception as e:
            logger.error(f"Error checking settings: {e}")
        finally:
            self._close_connection()
        
    
    def execute_crawl(self, crawl_id, url, keywords):
        """Execute a crawl"""
        self.active_crawls.add(crawl_id)
        try:
            current_time = datetime.now(self.timezone)
            logger.info(f'Starting crawl {crawl_id} at {datetime.now(self.timezone)}')
            
            ### Initialize your crawler
            crawler = Crawler()
            ### Execute crawl
            results = crawler.crawl(url, keywords)
            
            if results is None:
                logger.warning(f'No results found for crawl {crawl_id}')
                return
            
            ### Store results in database.
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                new_jobs = 0
                existing_jobs = 0
                
                for result in results:
                    ### Check if the job already exists
                    cursor.execute("""
                        SELECT id FROM crawl_results 
                        WHERE crawl_id = ? 
                        AND link = ?
                    """, (
                        crawl_id, 
                        result['link']
                    ))
                    
                    existing_job = cursor.fetchone()
                    
                    if not existing_job:
                        ### If job does not exist, insert it
                        cursor.execute("""
                            INSERT INTO crawl_results 
                            (crawl_id, title, company, location, link, crawl_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            crawl_id, 
                            result['title'], 
                            result['company'], 
                            result['location'], 
                            result['link'],
                            current_time.strftime('%Y-%m-%d %H:%M:%S')
                        ))
                        new_jobs += 1
                    else:
                        existing_jobs += 1
                
                conn.commit()
                logger.info(f"Completed crawl {crawl_id} - Added {new_jobs} new jobs, {existing_jobs} existing jobs")
            
            finally:
                conn.close()                        
        except Exception as e:
            logger.error(f'Error executing crawl {crawl_id}: {e}')
        
        finally:
            self.today_crawls_completed.add(crawl_id)
            self.active_crawls.remove(crawl_id)
            self._close_connection()
                
    
    def update_email_time(self, new_time):
        """Update the email time in the database for daily email report"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ### Check for existing settings table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                logger.error("Settings table does not exist")
                ### Create the settings table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE settings (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE  ,
                        value TEXT
                    )
                ''')
                
            ### Update the email time
            cursor.execute('''
            INSERT OR REPLACE INTO settings (name, value)
            VALUES ('email_time', ?)            
            ''', (new_time,))
            
            conn.commit()
            logger.info(f"Email time updated to {new_time}")
            
            ### Reschedule the email job
            self.schedule_email_job()
            
            return True
        except Exception as e:
            logger.error(f"Error updating email time: {e}")
            return False
        finally:
            self._close_connection()
            
    
                
    def __del__(self):
        """Clean up resources when the schedluar is stopped"""
        try:
            self.stop()
        except Exception as e:
            logger.info(f"Error stopping scheduler: {e}")