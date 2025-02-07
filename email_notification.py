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

### Load environment variables
load_dotenv()

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
        
        if not all([self.smtp_username, self.smtp_password]):
            raise ValueError("SMTP credentials not preperly onfigured in .env file")
        
    
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
    
    
    def format_email_content(self, results):
        """Format the email content"""
        if not results:
            return "No new jobs found today."

        html = """
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .crawl-section {
                    margin-bottom: 40px;
                    background: #fff;
                }
                .job { 
                    margin-bottom: 25px;
                    padding: 15px;
                    border: 1px solid #eee;
                    border-left: 4px solid #2c5282;
                    background: #f8f9fa;
                    margin-top: 25px;
                }
                .title { 
                    font-weight: bold; 
                    color: #2c5282;
                    font-size: 16px;
                    margin-bottom: 12px;
                }
                .details { 
                    color: #4a5568; 
                    margin: 8px 0;
                    padding-left: 10px;
                    border-left: 2px solid #eee;
                }
                .link { 
                    margin-top: 15px;
                }
                .link a {
                    color: #2b6cb0;
                    text-decoration: none;
                }
                .link a:hover {
                    text-decoration: underline;
                }
                h2 {
                    color: #1a365d;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #2c5282;
                }
                h3 {
                    color: #2d3748;
                    margin-top: 30px;
                    padding: 10px;
                    background: #edf2f7;
                    border-radius: 4px;
                }
                .separator {
                    height: 1px;
                    background: #e2e8f0;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h2>New Jobs Found Today</h2>
        """
        
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
            recitipents = self.get_recipient_emails()
            
            if not recitipents:
                logger.warning("No recipients found in database")
                return

            ### Format the email content
            html_content = self.format_email_content(results)
            
            ### Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Job Report - {datetime.now(self.timezone).strftime('%Y-%m-%d')}"
            msg['From'] = self.smtp_username if self.smtp_username else 'yourCrawler@bhm.com'
            msg['To'] = ', '.join(recitipents)

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
            
            logger.info(f"Daily report sent successfully to {len(recitipents)} recipients")
            
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