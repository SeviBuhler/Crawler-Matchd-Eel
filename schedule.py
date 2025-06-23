from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from pytz import timezone
import sqlite3
from crawler import Crawler
import logging
from email_notification import send_daily_email_report, send_failure_email
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
        self.today_crawls_completed = set()
        self.email_task_id = 'daily_email_report'
        
        
    
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
            
    
    def get_email_time_from_db(self):
        """Get email time from database with fallback to default"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                logger.warning("Settings table does not exist, using default time")
                return "15:30"

            # Get email time
            cursor.execute("SELECT value FROM settings WHERE name='email_time'")
            result = cursor.fetchone()
            return result[0] if result else "15:30"

        except Exception as e:
            logger.error(f"Error getting email time: {e}")
            return "15:30"
        finally:
            self._close_connection()
    
    
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
            self.schedule_email_task()
                        
            ### Load all crawls from database when starting
            self.update_crawl_schedules()
            
            ### Start the scheduler
            self.scheduler.start()
            print('Scheduler started successfully')
            
        except Exception as e:
            print(f'Error starting scheduler: {e}')
    
    
    def schedule_email_task(self):
        """Function to plan the daily email job based on database"""
        try:
            email_time = self.get_email_time_from_db()
            
            ### Parse the email time
            hour, minute = map(int, email_time.split(':'))
            
            ### Remove existing email task if it exists
            try:
                self.scheduler.remove_job(self.email_task_id)
                self.scheduler.remove_job('database_cleanup')
                self.scheduler.remove_job('reset_daily_tracking')
            except:
                pass
            
            ### Add the new email job
            self.scheduler.add_job(
                self.send_daily_report,
                CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
                id=self.email_task_id
            )
            
            ### Schedule cleanup task to run 5 minutes after teh email job
            cleanup_minute = (minute + 5) % 60
            cleanup_hour = hour + ((minute +5) // 60)
            
            self.scheduler.add_job(
                self.cleanup_after_daily_crawls,
                CronTrigger(hour=cleanup_hour, minute=cleanup_minute, timezone=self.timezone),
                id='database_cleanup'
            )
            
            ### Reset completed crawls list 10 minutes after email
            reset_minute = (minute + 10) % 60
            reset_hour = hour + ((minute + 10) // 60)
            
            ### Reset completed crawls list at daily report time
            self.scheduler.add_job(
                self.reset_daily_tracking,
                CronTrigger(hour=reset_hour, minute=reset_minute, timezone=self.timezone),
                id='reset_daily_tracking'
            )
            
            logger.info(f"Email job scheduled at {email_time}")
            logger.info(f"Database cleanup scheduled at {cleanup_hour}:{cleanup_minute:02d}")
            logger.info(f"Daily tracking reset scheduled at {reset_hour}:{reset_minute:02d}")
            
        except Exception as e:
            logger.error(f"Error scheduling email job: {e}")
        finally:
            self._close_connection()

    
    
    def reset_daily_tracking(self):
        """Reset the tracking of completed crawls fot the new day"""
        self.today_crawls_completed = set()
        logger.info('Daily crawls tracking reset')
        self.schedule_email_task()
            
    
    
    def send_daily_report(self):
        """Send daily email report of crawl status"""
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
            system_tasks = {'crawl_schedule_updater', 'settings_checker', 'daily_email_report', 'reset_daily_tracking'}
            scheduled_tasks = {job.id for job in self.scheduler.get_jobs() if job.id not in system_tasks and job.id.startswith('crawl_')}
            
            for crawl in crawls:
                crawl_id, title, url, scheduleTime, scheduleDay, keywords = crawl
                task_id = f'crawl_{crawl_id}'
                
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
                if task_id in scheduled_tasks:
                    self.scheduler.reschedule_job(
                        task_id, 
                        trigger=trigger
                    )
                    scheduled_tasks.remove(task_id)
                else:
                    self.scheduler.add_job(
                        self.execute_crawl,
                        trigger=trigger,
                        args=[crawl_id, url, keywords_list],
                        id=task_id,
                        name=title
                    )
            
            for job_id in scheduled_tasks:
                self.scheduler.remove_job(job_id)
                
            conn.close()
            
        except Exception as e:
            print(f'Error updating crawl schedules: {e}')
        finally:
            self._close_connection()
    
    
    def check_settings(self):
        """Checks the settings table for any changes"""
        try:
            current_email_time = self.get_email_time_from_db()
            
            ### Save the previous email time and check if it changed
            if not hasattr(self, 'previous_email_time'):
                self.previous_email_time = current_email_time
                return
            
            ### Only if the email time changed, reschedule the job
            if current_email_time != self.previous_email_time:
                logger.info(f"Email time changed from {self.previous_email_time} to {current_email_time}")
                self.previous_email_time = current_email_time
                self.schedule_email_task()
            
        except Exception as e:
            logger.error(f"Error checking settings: {e}")
        finally:
            self._close_connection()
        
    
    def execute_crawl(self, crawl_id, url, keywords):
        """Execute a crawl task and process job listings"""
        self.active_crawls.add(crawl_id)
        
        try:
            current_time = datetime.now(self.timezone)
            current_date = current_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f'Starting crawl {crawl_id} at {current_time}')
            
            # Execute crawl
            crawler = Crawler()
            results = crawler.crawl(url, keywords)
            
            if results is None:
                raise Exception("Crawler returned None - website unreachable, network error, or parsing failed")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # 1. Get all existing jobs for this crawl
                cursor.execute('''
                    SELECT id, title, company, location, link 
                    FROM crawl_results 
                    WHERE crawl_id = ? AND crawl_url = ?
                ''', (crawl_id, url))
                existing_jobs = {row[4]: row for row in cursor.fetchall()}
                
                new_jobs = 0
                updated_jobs = 0
                found_links = set()
                
                # 2. Process crawl results
                for result in results:
                    link = result['link']
                    found_links.add(link)
                    
                    if link in existing_jobs:
                        updated_jobs += 1
                        del existing_jobs[link]
                    else:
                        # Insert new job
                        cursor.execute('''
                            INSERT INTO crawl_results 
                            (crawl_id, crawl_url, title, company, location, link, crawl_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (crawl_id, url, result['title'], result.get('company', 'Not specified'),
                              result.get('location', 'Not specified'), result['link'], current_date))
                        new_jobs += 1
                
                # 3. Process removed jobs (left overs in existing_jobs = not found in results)
                removed_jobs = []
                for link, job_data in existing_jobs.items():
                    job_id, title, company, location, _ = job_data
                    removed_jobs.append((job_id, title, company, location, link))
                
                # 4. Add removed jobs to removed_jobs table
                if removed_jobs:
                    for job_id, title, company, location, link in removed_jobs:
                        cursor.execute('''
                            INSERT INTO removed_jobs
                            (job_id, crawl_id, title, company, location, link, removal_date, notified)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        ''', (job_id, crawl_id, title, company, location, link, current_date))
                        
                        logger.info(f'Job removed: {title} at {company}')
                    
                    # 5. DELETE removed jobs from crawl_results
                    job_ids_to_delete = [job[0] for job in removed_jobs]
                    placeholders = ','.join('?' * len(job_ids_to_delete))
                    cursor.execute(f'''
                        DELETE FROM crawl_results 
                        WHERE id IN ({placeholders})
                    ''', job_ids_to_delete)
                
                conn.commit()
                logger.info(f"Completed crawl {crawl_id} - Added {new_jobs} new, updated {updated_jobs}, removed {len(removed_jobs)}")
                
            finally:
                conn.close()
                    
        except Exception as crawl_error: 
            ### Crawl-Fehler aufgetreten - in Database eintragen
            print(f"=== DEBUG: Exception caught: {crawl_error} ===")
            print(f"=== DEBUG: Exception type: {type(crawl_error)} ===")
            import traceback
            error_traceback = traceback.format_exc()
            print(f"=== DEBUG: Full traceback: {error_traceback} ===")
            logger.error(f'Crawl {crawl_id} failed: {crawl_error}')
            # Fehler in Database speichern
            from database import Database
            db = Database()
            db.add_failed_crawl(
                crawl_id=crawl_id,
                crawl_url=url,
                error_message=str(crawl_error),
                error_type=type(crawl_error).__name__,
                traceback_str=error_traceback
            )
            # E-Mail senden
            print(f"=== DEBUG: Calling send_failure_notification ===")
            self.send_failure_notification(crawl_id, url, crawl_error, error_traceback)

        finally:
            self.today_crawls_completed.add(crawl_id)
            self.active_crawls.remove(crawl_id)
            self._close_connection()
            
            
    
    def send_failure_notification(self, crawl_id, url, error, traceback_str):
        """Send email notification for failed crawls"""
        try:
            subject = f"🚨 Crawl Failed - ID: {crawl_id}"
            message = f"""
            <strong>Crawl Details:</strong><br>
            • Crawl ID: {crawl_id}<br>
            • URL: {url}<br>
            • Error: {error}<br>
            • Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br><br>

            <strong>Traceback:</strong><br>
            <div class="traceback">{traceback_str.replace('\n', '<br>')}</div>
            """

            send_failure_email(subject, message)
            logger.info(f"Failure notification sent for crawl {crawl_id}")

        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
                
                
    
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
            self.schedule_email_task()
            
            return True
        except Exception as e:
            logger.error(f"Error updating email time: {e}")
            return False
        finally:
            self._close_connection()
            
    
    def cleanup_after_daily_crawls(self):
        """Clean up old data from the database"""
        logger.info("Starting daily database cleanup...")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            ### Calculate cutoff date (30 days ago)
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            ### Clean up old removed jobs (only older than 30 days AND notified)
            cursor.execute("DELETE FROM removed_jobs WHERE removal_date < ? AND notified = 1", (cutoff_date,))
            removed_count = cursor.rowcount

            ### Clean up old failed crawls (older than 30 days)
            cursor.execute("DELETE FROM failed_crawls WHERE failure_date < ?", (cutoff_date,))
            failed_count = cursor.rowcount

            conn.commit()
            logger.info(f"Database cleanup completed:")
            logger.info(f"  - Removed {removed_count} old removed job notifications")
            logger.info(f"  - Removed {failed_count} old failed crawl entries")

        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            self._close_connection()
                
                
    def __del__(self):
        """Clean up resources when the schedluar is stopped"""
        try:
            self.stop()
        except Exception as e:
            logger.info(f"Error stopping scheduler: {e}")