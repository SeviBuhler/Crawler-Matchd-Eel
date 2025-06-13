import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import sqlite3
import logging
import os
from dotenv import load_dotenv
from database_config import get_db_path
import threading


def get_env_path():
    """
    Find the .env file, prioritizing the AppData location
    """
    appdata = os.getenv('APPDATA')
    if appdata:
        appdata_env = os.path.join(appdata, 'JobCrawler', '.env')
        if os.path.exists(appdata_env):
            return appdata_env
    
    ### Fallback to script directory or other locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    potential_paths = [
        os.path.join(script_dir, '.env'),
        os.path.join(script_dir, '..', '.env')
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            return path
    
    return None

env_path = get_env_path()
if env_path:
    load_dotenv(env_path, override=True)
    print(f"Loaded -env file from {env_path}")
else:
    print("Warning: No .env file found")

### set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EmailNotifications')


class EmailNotifier:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path is not None else get_db_path()
        self.thread_local = threading.local()
        self.timezone = pytz.timezone('Europe/Zurich')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        print("Environment Variables:")
        print(f"SMTP_SERVER: {self.smtp_server}")
        print(f"SMTP_PORT: {self.smtp_port}")
        print(f"SMTP_USERNAME: {self.smtp_username}")
        print(f"SMTP_PASSWORD set: {bool(self.smtp_password)}")
        
        if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password]):
            error_msg = "Missing SMTP configuration. Please check your .env file."
            print(error_msg)
            raise ValueError(error_msg)
        
    
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
    
       
    def get_todays_results(self):
        """Get all results from today"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ### Get today's date in the correct timezone
            today = datetime.now(self.timezone).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT cr.title, cr.company, cr.location, cr.link, c.title as crawl_name
                FROM crawl_results cr
                JOIN crawls c ON cr.crawl_id = c.id
                WHERE DATE(cr.crawl_date) = ?
                ORDER BY cr.crawl_date DESC
            """, (today,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
    
        except Exception as e:
            logger.error(f"Error getting today's results: {e}")
            return []
        finally:
            self._close_connection()
            
    
    def get_removed_jobs(self, mark_as_notified=False):
        """Get jobs that were removed since the last report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Debug: Check if we have any removed jobs at all
            cursor.execute("SELECT COUNT(*) FROM removed_jobs")
            total_removed = cursor.fetchone()[0]
            logger.info(f"Total removed jobs in database: {total_removed}")

            # Debug: Check notified status
            cursor.execute("SELECT COUNT(*) FROM removed_jobs WHERE notified = 0")
            unnotified = cursor.fetchone()[0]
            logger.info(f"Unnotified removed jobs: {unnotified}")

            # Get removed jobs that haven't been notified yet
            try:
                cursor.execute("""
                    SELECT r.job_id, r.title, r.company, r.location, r.link, r.removal_date, c.title
                    FROM removed_jobs r
                    JOIN crawls c ON r.crawl_id = c.id
                    WHERE r.notified = 0
                """)

                removed_jobs = cursor.fetchall()
                logger.info(f"Found {len(removed_jobs)} removed jobs to report")

                # Mark these jobs as notified
                if removed_jobs:
                    cursor.execute("UPDATE removed_jobs SET notified = 1 WHERE notified = 0")
                    conn.commit()
                    logger.info("Marked removed jobs as notified")

                return removed_jobs
            except Exception as e:
                logger.error(f"Error in SQL query for removed jobs: {e}")
                import traceback
                traceback.print_exc()
                return []

        except Exception as e:
            logger.error(f"Error getting removed jobs: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
            
    
    def get_recipient_emails(self):
        """Get all recipient emails"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT email FROM emails")
            emails = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return emails
        
        except Exception as e:
            logger.error(f"Error getting recipient emails: {e}")
            return []
        finally:
            self._close_connection()
    
    
    def format_email_content(self, results, removed_jobs=None):
        """Format the email content"""
        # If removed_jobs not provided, get them (but don't mark as notified)
        if removed_jobs is None:
            removed_jobs = self.get_removed_jobs(mark_as_notified=False)
        
        logger.info(f"Formatting email with {len(results) if results else 0} new jobs found and {len(removed_jobs) if removed_jobs else 0} removed jobs")
        
        ### If we have netihher new jobs nor removed jobs, return a simple message
        if not results and not removed_jobs:
            return "No new jobs found today and no jobs have been removed since the last report."

        current_date = datetime.now(self.timezone).strftime('%Y-%m-%d')
        
        ### Start building HTML content in all other cases
        html = """
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .crawl-section {{
                    margin-bottom: 40px;
                    background: #fff;
                }}
                .job {{ 
                    margin-bottom: 25px;
                    padding: 15px;
                    border: 1px solid #eee;
                    border-left: 4px solid #2c5282;
                    background: #f8f9fa;
                    margin-top: 25px;
                }}
                .title {{ 
                    font-weight: bold; 
                    color: #2c5282;
                    font-size: 16px;
                    margin-bottom: 12px;
                }}
                .details {{ 
                    color: #4a5568; 
                    margin: 8px 0;
                    padding-left: 10px;
                    border-left: 2px solid #eee;
                }}
                .link {{ 
                    margin-top: 15px;
                }}
                .link a {{
                    color: #2b6cb0;
                    text-decoration: none;
                }}
                .link a:hover {{
                    text-decoration: underline;
                }}
                h2 {{
                    color: #1a365d;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #2c5282;
                }}
                h3 {{
                    color: #2d3748;
                    margin-top: 30px;
                    padding: 10px;
                    background: #edf2f7;
                    border-radius: 4px;
                }}
                .separator {{
                    height: 1px;
                    background: #e2e8f0;
                    margin: 20px 0;
                }}
                .removed-job {{
                    margin-bottom: 25px;
                    padding: 15px;
                    border: 1px solid #eee;
                    border-left: 4px solid #e53e3e;
                    background: #fff5f5;
                    margin-top: 25px;
                }}
                .removed-section {{
                    margin-top: 40px;
                    border-top: 2px solid #e53e3e;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>Job Report - {date}</h2>
        """.format(date=current_date)
        
        ### Add new jobs section if there are any
        if results:
            html += "<h3>New Jobs</h3>"
        
            ### Group resluts by crawl name
            jobs_by_crawl = {}
            for title, company, location, link, crawl_name in results:
                if crawl_name not in jobs_by_crawl:
                    jobs_by_crawl[crawl_name] = []
                jobs_by_crawl[crawl_name].append((title, company, location, link))

            ### Add jobs grouped by crawl
            for crawl_name, jobs in jobs_by_crawl.items():
                html += "<div class='crawl-section'>"
                html += f"<h3>From {crawl_name}</h3>"
                for title, company, location, link in jobs:
                    html += f"""
                    <div class="job">
                        <div class="title">{title}</div>
                        <div class="details">Company: {company}</div>
                        <div class="details">Location: {location}</div>
                        <div class="link"><a href="{link}">View Job</a></div>
                    </div>
                    """
                html += "</div>"
        
        else:
            html += "<p>No new jobs found today.</p>"
        
        if removed_jobs:
            html += "<div class='removed-section'>"
            html += "<h3>Removed Jobs</h3>"
            html += "<p>The following jobs are no longer available:</p>"
            
            logger.info(f"Removed jobs data structure: {removed_jobs[:1]}")
            
            ### Group removved jobs by crawl name
            removed_by_crawl = {}
            for job_id, title, company, location, link, removal_date, crawl_name in removed_jobs:
                if crawl_name not in removed_by_crawl:
                    removed_by_crawl[crawl_name] = []
                removed_by_crawl[crawl_name].append((job_id, title, company, location, link, removal_date))
            
            
            ### Display removed jobs by crawl
            for crawl_name, jobs in removed_by_crawl.items():
                html += f"<h4>From {crawl_name}</h4>"
                for job_id, title, company, location, link, removal_date in jobs:
                    removal_date_formatted = datetime.fromisoformat(removal_date.replace(' ', 'T')).strftime('%Y-%m-%d %H:%M')
                    html += f"""
                    <div class="removed-job">
                        <div class="title">{title}</div>
                        <div class="details">Company: {company}</div>
                        <div class="details">Location: {location}</div>
                        <div class="link"><a href="{link}">View Job</a></div>
                        <div class="details">Removed on: {removal_date_formatted}</div>
                    </div>
                    """
            html += "</div>"
        
        else:
            html += "<p>No jobs have been removed since the last report.</p>"
        
        html += """
        </body>
        </html>
        """
    
        return html
    
    
    def send_daily_report(self):
        """Send daily report of new jobs to all recipients"""
        try:
            ### Get today's results
            results = self.get_todays_results()
            recipients = self.get_recipient_emails()
            
            if not recipients:
                logger.warning("No recipients found in database")
                return
            
            # Get removed jobs - don't mark as notified yet
            removed_jobs = self.get_removed_jobs(mark_as_notified=False)

            ### Format the email content
            html_content = self.format_email_content(results, removed_jobs)
            
            ### Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Job Report - {datetime.now(self.timezone).strftime('%Y-%m-%d')}"
            msg['From'] = self.smtp_username if self.smtp_username else 'yourCrawler@bhm.com'
            msg['To'] = ', '.join(recipients)

            ### Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            ### Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                else:
                    logger.error("SMTP username or password is not set.")
                    return
                server.send_message(msg)
                if removed_jobs:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE removed_jobs SET notified = 1 WHERE notified = 0")
                    conn.commit()
                    conn.close()
                    logger.info(f"Marked {len(removed_jobs)} removed jobs as notified")
            
            logger.info(f"Daily report sent successfully to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            
    
            
            
### Function to be called after all daily crawls are completed
def send_daily_email_report(db_path='crawls.db'):
    """Send daily email report"""
    try:
        notifier = EmailNotifier(db_path)
        notifier.send_daily_report()
    except Exception as e:
        logger.error(f"Error sending daily email report: {e}")