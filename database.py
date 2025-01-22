import sqlite3
import logging
import os
from localities_data import LOCALITIES_DATA 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file='crawls.db'):
        self.db_file = db_file
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize the database with tables and populate localities"""
        db_exists = os.path.exists(self.db_file)
        conn =sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            ### Create tables
            self.create_tables(cursor)
            
            ### If this is a new database, popiulate localities
            if not db_exists:
                self.populate_localities(cursor)
                
            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
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
            title TEXT,
            company TEXT,
            location TEXT,
            link TEXT,
            crawl_date DATETIME DEFAULT CURRENT_TIMESTAMP,
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