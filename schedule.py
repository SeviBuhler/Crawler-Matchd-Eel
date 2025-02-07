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
            ### Check crawls every minute for updates
            self.scheduler.add_job(
                self.update_crawl_schedules,
                'interval',
                minutes=1,
                id='crawl_schedule_updater'
            )
            
            ### Add job for daily email report at 15:30
            self.scheduler.add_job(
                self.check_and_send_daily_report,
                CronTrigger(hour=15, minute=30, timezone=self.timezone),
                id='daily_email_report'
            )
            
            ### Load all crawls from database
            self.update_crawl_schedules()
            
            ### Start the scheduler
            self.scheduler.start()
            print('Scheduler started successfully')
            
        except Exception as e:
            print(f'Error starting scheduler: {e}')
    
    
    def check_and_send_daily_report(self):
        """Check all crawls are complete and send daily report"""
        if not self.active_crawls:
            try:
                send_daily_email_report(self.db_path)
                self.daily_crawls_complete = False ### Reset fot next day
            except Exception as e:
                logger.error(f'Error sending daily report: {e}')
    
    
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
            scheduled_jobs = {job.id for job in self.scheduler.get_jobs() if job.id != 'crawl_schedule_updater'}
            
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
            conn = self._get_connection
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
            self.active_crawls.remove(crawl_id)
            ### Check if this was the last  active crawl for the day
            if not self.active_crawls:
                self.check_and_send_daily_report()
            self._close_connection()
                
    def __del__(self):
        """Clean up resources when the schedluar is stopped"""
        try:
            self.stop()
        except Exception as e:
            logger.info(f"Error stopping scheduler: {e}")