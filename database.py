import sqlite3
import logging
import os
from crawls_data import CRAWLS_DATA
from localities_data import LOCALITIES_DATA
from database_config import get_db_path
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initalize Database with path from configuration"""
        self.db_file = get_db_path()
        self.ensure_db_directory()
        
    def _get_connection(self):
        """Private method to create a database connection"""
        return sqlite3.connect(self.db_file)
        
    def get_connection(self):
        """Public method to get a database connection"""
        return self._get_connection()
        
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        try:
            db_dir = os.path.dirname(self.db_file)
            if not os.path.exists(db_dir):
                logger.info(f"Creating database directory: {db_dir}")
                ### Create parent directory if it doesn't exist
                os.makedirs(db_dir, exist_ok=True)
                ### Set permissions
                os.chmod(self.db_file, 0o666)
                logger.info(f"Database directory created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize databse directory: {e}")
            return False
        
    def initialize_database(self):
        """Initialize the database with tables and populate localities"""
        try:
            print(f"Initializing database at {self.db_file}")
            conn =sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            ### Check if the localities table exists and is empty
            self.create_tables(cursor)
            cursor.execute("SELECT COUNT(*) FROM localities")
            locals_count = cursor.fetchone()[0]
            
            if locals_count == 0:
                logger.info("Localities table is empty, populating with initial data")
                self.populate_localities(cursor)
            else:
                logger.info("Localities table already populated, skipping population")
                
            ### Check if crawls table exists and is empty
            cursor.execute("SELECT COUNT(*) FROM crawls")
            crawls_count = cursor.fetchone()[0]
            
            if crawls_count == 0:
                logger.info("Crawls table is empty, populating with initial data")
                self.populate_crawls(cursor)
            else:
                logger.info("Crawls table already populated, skipping population")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
            

    def create_tables(self, cursor):
        """Create the tables in the database"""
        
        ### Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawls(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            scheduleTime TEXT NOT NULL,
            scheduleDay TEXT NOT NULL
        )               
        ''')
        
        ### Create keywords table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_id INTEGER,
            keyword TEXT NOT NULL,
            FOREIGN KEY (crawl_id) REFERENCES crawls (id)
        )
        ''')
        
        #### Create locations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS localities(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ortschaftsname TEXT NOT NULL,    -- Gemeinde
            kanton TEXT NOT NULL          -- Kanton
        )
        ''')
        
        ### Create crawl_results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_id INTEGER,
            crawl_url TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT,
            crawl_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (crawl_id) REFERENCES crawls (id)
        )
        ''')
        
        ### Create removed_jobs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS removed_jobs (
            id INTEGER PRIMARY KEY,
            job_id INTEGER,
            crawl_id INTEGER,
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT,
            removal_date DATETIME,
            notified BOOLEAN DEFAULT 0,
            FOREIGN KEY (job_id) REFERENCES crawl_results (id) ON DELETE SET NULL,
            FOREIGN KEY (crawl_id) REFERENCES crawls (id)
        )
        ''')
        
        ### Create emails table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE
        )
        ''')
        
        ### Create settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            value TEXT
        )
        ''')
        
        ### Insert Standard email time if not exists
        cursor.execute('''
        INSERT OR IGNORE INTO settings (name, value)
        VALUES ('email_time', '15:30')            
        ''')
        
        ### Create failed_crawls table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS failed_crawls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_id INTEGER,
            crawl_url TEXT,
            error_message TEXT,
            error_type TEXT,
            failure_date DATETIME,
            traceback TEXT,
            notified BOOLEAN DEFAULT 0,
            FOREIGN KEY (crawl_id) REFERENCES crawls(id)
        )
        ''')

    
    def populate_localities(self, cursor):
        """Populate the localities initial with data"""
        try:
            ### First check if the table is empty
            cursor.execute('SELECT COUNT(*) FROM localities')
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info('Populating localities...')
                cursor.executemany(
                    "INSERT INTO localities (ortschaftsname, kanton) VALUES (?, ?)",
                    LOCALITIES_DATA
                )
                logger.info(f"Successfully populated localities table with {len(LOCALITIES_DATA)} records")
            else:
                logger.info('Localities table already populated')
        except Exception as e:
            logger.error(f"Error populating localities: {e}")
            raise
        
    
    def populate_crawls(self, cursor):
        """Populate the crawls table with initial data"""
        try:
            # First check if the crawls table is empty
            cursor.execute('SELECT COUNT(*) FROM crawls')
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info('Populating crawls table...')
                
                for crawl_data in CRAWLS_DATA:
                    title, url, schedule_time, schedule_day, keywords = crawl_data
                    
                    # Insert crawl
                    cursor.execute('''
                        INSERT INTO crawls (title, url, scheduleTime, scheduleDay)
                        VALUES (?, ?, ?, ?)
                    ''', (title, url, schedule_time, schedule_day))
                    
                    crawl_id = cursor.lastrowid
                    
                    # Insert keywords for this crawl
                    for keyword in keywords:
                        cursor.execute('''
                            INSERT INTO keywords (crawl_id, keyword)
                            VALUES (?, ?)
                        ''', (crawl_id, keyword))
                
                logger.info(f"Successfully populated crawls table with {len(CRAWLS_DATA)} crawls")
            else:
                logger.info('Crawls table already populated')
                
        except Exception as e:
            logger.error(f"Error populating crawls: {e}")
            raise
    
    
    def add_crawl(self, title, url, scheduleTime, scheduleDay, keywords):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        
        try:
            # Convert keywords list to comma-separated string if it's a list
            keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
            
            ### Insert Crawl
            cursor.execute('''
            Insert into crawls (title, url, scheduleTime, scheduleDay)
            VALUES (?, ?, ?, ?)
            ''', (title, url, scheduleTime, scheduleDay))
            
            crawl_id = cursor.lastrowid
            
            ### Insert Keywords
            for keyword in keywords:
                cursor.execute('''
                INSERT INTO keywords (crawl_id, keyword)
                VALUES (?, ?)
                ''', (crawl_id, keyword))
            
            conn.commit()
            return {"status": "success", "id": crawl_id}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
        
    
    def get_all_crawls(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT c.id, c.title, c.url, c.scheduleTime, c.scheduleDay, GROUP_CONCAT(k.keyword) as keywords
            FROM crawls c
            LEFT JOIN keywords k ON c.id = k.crawl_id
            GROUP BY c.id
            ''')
        
            crawls = []
            for row in cursor.fetchall():
                crawls.append({
                    "id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "scheduleTime": row[3],
                    "scheduleDay": row[4].split(',') if row[4] else [],
                    "keywords": row[5].split(',') if row[5] else []
                })
            return crawls
        finally:
            conn.close()
    
    
    def delete_crawl(self, crawl_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            ### Delete keywords first (due to foreign key)
            cursor.execute("DELETE FROM keywords WHERE crawl_id = ?", (crawl_id,))
            cursor.execute("DELETE FROM crawls WHERE id = ?", (crawl_id,))
        
            conn.commit()
            return {"status": "success"}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    
    def update_crawl(self, crawl_id, name, url, scheduleTime, scheduleDay, keywords):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()     
        
        try:
            ### Update Crawl details
            cursor.execute('''
            UPDATE crawls
            SET title = ?, url = ?, scheduleTime = ?, scheduleDay = ?
            WHERE id = ?
            ''', (name, url, scheduleTime, scheduleDay, crawl_id))
            
            ### Delete old keywords
            cursor.execute("DELETE FROM keywords WHERE crawl_id = ?", (crawl_id,))
            
            ### Insert new keywords
            for keyword in keywords:
                cursor.execute('''
                INSERT INTO keywords (crawl_id, keyword)
                VALUES (?, ?)
                ''', (crawl_id, keyword))
            
            conn.commit()
            return {"status": "success"}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
            
    
    def add_email(self, email):
        """Add an email to the database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO emails (email)
                VALUES (?)
                ''', (email,))
            conn.commit()
        except sqlite3.IntegrityError:
            return {"status": "error", "message": "Email already exists"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
            
            
    def get_email(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor() 
        
        try:
            cursor.execute('SELECT id, email FROM emails')
            emails = [{"id": row[0], "email": row[1]} for row in cursor.fetchall()]
            return emails
        finally:
            conn.close()
    
    
    def delete_email(self, email_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM emails WHERE id = ?', (email_id,))
            conn.commit()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
            
    
    def get_email_settings(self):
        """Function to get the Email settings from the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            ### check if the table settings exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                ### Create the settings table if it doesn't exist
                cursor.execute("""
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    value TEXT
                )               
                """)
                conn.commit()
            
            ### Get email-time from settings    
            cursor.execute("SELECT value FROM settings WHERE name='email_time'")
            result = cursor.fetchone()
            
            ### Standard time if not set
            email_time = "15:30" if result is None else result[0]
            
            return {
                "status": "success",
                "email_time": email_time,
            }
            
        except Exception as e:
            logger.error(f"Error getting email settings: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
        finally:
            conn.close()
            
        
    def update_email_settings(self, email_time):
        """Function to update the Email settings in the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            ### check if the table settings exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                ### Create the settings table if it doesn't exist
                cursor.execute("""
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    value TEXT
                )               
                """)
            
            ### Chekc, if email_time already exists
            cursor.execute("SELECT id FROM settings WHERE name='email_time'")
            existing = cursor.fetchone()
            
            if existing:
                ### Update existing email_time
                cursor.execute("UPDATE settings SET value=? WHERE name='email_time'", (email_time,))
            else:
                ### Insert new email_time
                cursor.execute("INSERT INTO settings (name, value) VALUES ('email_time', ?)", (email_time,))
            
            conn.commit()
            
            return {
                "status": "success",
                "message": "Email settings updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error druing updating email settings: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            conn.close()
            
    
    def get_dashboard_stats(self):
        """Get statistics for the dashboard"""
        print("=== DEBUG: database.get_dashboard_stats() gestartet ===")
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            stats = {}
            today = datetime.now().strftime('%Y-%m-%d')

            # Active jobs count
            cursor.execute("SELECT COUNT(*) FROM crawl_results")
            stats['active_jobs'] = cursor.fetchone()[0]

            # New jobs today
            cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE DATE(crawl_date) = ?", (today,))
            stats['new_jobs_today'] = cursor.fetchone()[0]

            # Removed jobs today
            cursor.execute("SELECT COUNT(*) FROM removed_jobs WHERE DATE(removal_date) = ?", (today,))
            stats['removed_jobs_today'] = cursor.fetchone()[0]

            # Active crawls count
            cursor.execute("SELECT COUNT(*) FROM crawls")
            stats['active_crawls'] = cursor.fetchone()[0]

            # Jobs per website
            cursor.execute("""
                SELECT cr.crawl_url, COUNT(cr.id) 
                FROM crawl_results cr
                GROUP BY cr.crawl_url
                ORDER BY COUNT(cr.id) DESC
                LIMIT 10
            """)
            stats['jobs_per_website'] = cursor.fetchall()

            # Failed crawls
            cursor.execute("""
                SELECT c.title, 
                       COALESCE(MAX(fc.failure_date), 'Never') as last_activity,
                       CASE 
                           WHEN fc.id IS NOT NULL THEN 0  -- Hat Eintrag in failed_crawls → Fehlgeschlagen
                           ELSE 1  -- Kein Eintrag in failed_crawls → Erfolgreich
                       END as success
                FROM crawls c
                LEFT JOIN failed_crawls fc ON c.id = fc.crawl_id
                GROUP BY c.id, c.title
                ORDER BY last_activity DESC
                LIMIT 20
            """)
            stats['recent_crawls'] = cursor.fetchall()

            # Job trends for the last 7 days
            dates = []
            new_jobs = []
            removed_jobs = []

            for i in range(29, -1, -1):
                date = (datetime.now() - timedelta(days=i))
                date_str = date.strftime('%Y-%m-%d')
                dates.append(date.strftime('%d.%m'))

                # New jobs for this date
                cursor.execute("SELECT COUNT(*) FROM crawl_results WHERE DATE(crawl_date) = ?", (date_str,))
                new_jobs.append(cursor.fetchone()[0])

                # Removed jobs for this date
                cursor.execute("SELECT COUNT(*) FROM removed_jobs WHERE DATE(removal_date) = ?", (date_str,))
                removed_jobs.append(cursor.fetchone()[0])

            stats['job_trends'] = {
                'dates': dates,
                'new_jobs': new_jobs,
                'removed_jobs': removed_jobs
            }

            return stats

        except Exception as e:
            print(f"=== ERROR in database.get_dashboard_stats: {e} ===")
            import traceback
            print(f"=== DATABASE TRACEBACK: {traceback.format_exc()} ===")
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                'active_jobs': 0,
                'new_jobs_today': 0,
                'removed_jobs_today': 0,
                'active_crawls': 0,
                'jobs_per_website': [],
                'recent_crawls': [],
                'job_trends': {'dates': [], 'new_jobs': [], 'removed_jobs': []}
            }
        finally:
            conn.close()
            
            
    def add_failed_crawl(self, crawl_id, crawl_url, error_message, error_type, traceback_str):
        """Add a failed crawl to the database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO failed_crawls (crawl_id, crawl_url, error_message, error_type, failure_date, traceback)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                crawl_id,
                crawl_url, 
                error_message,
                error_type,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                traceback_str
            ))
            conn.commit()
            logger.info(f"Failed crawl recorded for crawl_id {crawl_id}")
            return {"status": "success"}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error recording failed crawl: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    
    
    def close(self):
        """Properly close the connection to the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.close()
            logger.info('Database connection closed')
        except Exception as e:
            logger.error(f'Error closing database connection: {e}')
            
    
    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close()