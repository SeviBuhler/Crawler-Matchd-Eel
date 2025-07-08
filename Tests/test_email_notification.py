import sys
import os
from datetime import datetime, timedelta

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import sqlite3
from database_config import get_db_path
from email_notification import EmailNotifier

def setup_test_email_data():
    """Setup test data for email notification test"""
    print("=== SETUP EMAIL TEST DATA ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Clean up existing test data
    cursor.execute("DELETE FROM crawl_results WHERE company LIKE 'EmailTest%'")
    cursor.execute("DELETE FROM removed_jobs WHERE company LIKE 'EmailTest%'")
    cursor.execute("DELETE FROM keywords WHERE crawl_id IN (SELECT id FROM crawls WHERE title LIKE 'EmailTest%')")
    cursor.execute("DELETE FROM crawls WHERE title LIKE 'EmailTest%'")
    
    # Create test crawl configurations
    test_crawls = [
        ("EmailTest Jobs.ch", "https://jobs.ch/test", "09:00", "monday,tuesday,wednesday,thursday,friday"),
        ("EmailTest Indeed", "https://indeed.ch/test", "10:00", "monday,tuesday,wednesday,thursday,friday"),
        ("EmailTest StepStone", "https://stepstone.ch/test", "11:00", "monday,tuesday,wednesday,thursday,friday")
    ]
    
    crawl_ids = []
    for title, url, schedule_time, schedule_day in test_crawls:
        cursor.execute('''
            INSERT INTO crawls (title, url, scheduleTime, scheduleDay)
            VALUES (?, ?, ?, ?)
        ''', (title, url, schedule_time, schedule_day))
        crawl_id = cursor.lastrowid
        crawl_ids.append(crawl_id)
        
        # Add keywords for each crawl
        test_keywords = ['python', 'java', 'javascript']
        for keyword in test_keywords:
            cursor.execute('''
                INSERT INTO keywords (crawl_id, keyword)
                VALUES (?, ?)
            ''', (crawl_id, keyword))
    
    # Create test jobs - NEW JOBS (heute gefunden)
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_jobs = [
        # Jobs.ch neue Jobs
        (crawl_ids[0], "Senior Python Developer", "EmailTestCorp A", "Zurich", "https://jobs.ch/job1", today),
        (crawl_ids[0], "Full Stack Engineer", "EmailTestCorp B", "Basel", "https://jobs.ch/job2", today),
        (crawl_ids[0], "DevOps Specialist", "EmailTestCorp C", "Bern", "https://jobs.ch/job3", today),
        
        # Indeed neue Jobs
        (crawl_ids[1], "Java Backend Developer", "EmailTestCorp D", "Geneva", "https://indeed.ch/job1", today),
        (crawl_ids[1], "React Frontend Developer", "EmailTestCorp E", "Lausanne", "https://indeed.ch/job2", today),
        
        # StepStone neue Jobs
        (crawl_ids[2], "Data Scientist", "EmailTestCorp F", "Zurich", "https://stepstone.ch/job1", today),
        (crawl_ids[2], "Machine Learning Engineer", "EmailTestCorp G", "St. Gallen", "https://stepstone.ch/job2", today),
    ]
    
    job_ids = []
    for crawl_id, title, company, location, link, crawl_date in new_jobs:
        cursor.execute('''
            INSERT INTO crawl_results 
            (crawl_id, crawl_url, title, company, location, link, crawl_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (crawl_id, "https://test.com", title, company, location, link, crawl_date))
        job_ids.append(cursor.lastrowid)
    
    # Create REMOVED JOBS (noch nicht notified)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    removed_jobs = [
        # Jobs.ch entfernte Jobs
        (101, crawl_ids[0], "Python Developer (OLD)", "EmailTestCorp X", "Zurich", "https://jobs.ch/old1", yesterday, 0),
        (102, crawl_ids[0], "Software Engineer (OLD)", "EmailTestCorp Y", "Basel", "https://jobs.ch/old2", yesterday, 0),
        
        # Indeed entfernte Jobs  
        (103, crawl_ids[1], "Java Developer (OLD)", "EmailTestCorp Z", "Geneva", "https://indeed.ch/old1", yesterday, 0),
        
        # StepStone entfernte Jobs
        (104, crawl_ids[2], "Data Analyst (OLD)", "EmailTestCorp W", "Bern", "https://stepstone.ch/old1", yesterday, 0),
        (105, crawl_ids[2], "ML Researcher (OLD)", "EmailTestCorp V", "Lausanne", "https://stepstone.ch/old2", yesterday, 0),
    ]
    
    for job_id, crawl_id, title, company, location, link, removal_date, notified in removed_jobs:
        cursor.execute('''
            INSERT INTO removed_jobs
            (job_id, crawl_id, title, company, location, link, removal_date, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, crawl_id, title, company, location, link, removal_date, notified))
    
    conn.commit()
    conn.close()
    
    print("Test-Daten erstellt:")
    print(f"✅ {len(test_crawls)} Test-Crawls erstellt")
    print(f"✅ {len(new_jobs)} neue Jobs (heute) erstellt")
    print(f"✅ {len(removed_jobs)} entfernte Jobs (nicht notified) erstellt")
    print()
    
    return crawl_ids

def check_test_data(crawl_ids):
    """Check what test data was created"""
    print("=== TEST DATA VERIFICATION ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check neue Jobs (heute)
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT cr.title, cr.company, cr.location, c.title as crawl_name
        FROM crawl_results cr
        JOIN crawls c ON cr.crawl_id = c.id
        WHERE DATE(cr.crawl_date) = ? AND cr.company LIKE 'EmailTest%'
        ORDER BY c.title, cr.title
    ''', (today,))
    
    new_jobs = cursor.fetchall()
    print("NEUE JOBS (heute):")
    current_crawl = None
    for title, company, location, crawl_name in new_jobs:
        if crawl_name != current_crawl:
            print(f"\n  📊 {crawl_name}:")
            current_crawl = crawl_name
        print(f"    • {title} bei {company} in {location}")
    
    # Check entfernte Jobs (nicht notified)
    cursor.execute('''
        SELECT r.title, r.company, r.location, c.title as crawl_name, r.removal_date
        FROM removed_jobs r
        LEFT JOIN crawls c ON r.crawl_id = c.id
        WHERE r.notified = 0 AND r.company LIKE 'EmailTest%'
        ORDER BY c.title, r.title
    ''', )
    
    removed_jobs = cursor.fetchall()
    print(f"\n\nENTFERNTE JOBS (nicht notified):")
    current_crawl = None
    for title, company, location, crawl_name, removal_date in removed_jobs:
        if crawl_name != current_crawl:
            print(f"\n  🗑️ {crawl_name}:")
            current_crawl = crawl_name
        print(f"    • {title} bei {company} in {location} (entfernt: {removal_date})")
    
    conn.close()
    
    return len(new_jobs), len(removed_jobs)

def test_email_formatting():
    """Test the email formatting without sending"""
    print("\n=== EMAIL FORMATTING TEST ===\n")
    
    try:
        # Create EmailNotifier instance
        notifier = EmailNotifier()
        
        # Get today's results (our test data)
        results = notifier.get_todays_results()
        print(f"✅ Gefundene neue Jobs: {len(results)}")
        
        # Get removed jobs (without marking as notified)
        removed_jobs = notifier.get_removed_jobs(mark_as_notified=False)
        print(f"✅ Gefundene entfernte Jobs: {len(removed_jobs)}")
        
        # Format email content
        html_content = notifier.format_email_content(results, removed_jobs)
        
        # Save to file for inspection
        test_email_file = "test_email_output.html"
        with open(test_email_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Email-Inhalt formatiert und gespeichert in: {test_email_file}")
        print(f"✅ HTML-Länge: {len(html_content)} Zeichen")
        
        # Show preview of content
        print("\n--- EMAIL PREVIEW (erste 500 Zeichen) ---")
        print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        print("--- END PREVIEW ---\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Email-Formatting: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_send_email(actually_send=False):
    """Test sending the email (optional)"""
    print(f"=== EMAIL SENDING TEST (Send: {actually_send}) ===\n")
    
    if not actually_send:
        print("⚠️ Email wird NICHT gesendet (actually_send=False)")
        print("   Ändern Sie actually_send=True um tatsächlich zu senden")
        return True
    
    try:
        # Check if we have recipients
        notifier = EmailNotifier()
        recipients = notifier.get_recipient_emails()
        
        if not recipients:
            print("⚠️ Keine Email-Empfänger in der Datenbank gefunden!")
            print("   Fügen Sie Empfänger über das Web-Interface hinzu")
            return False
        
        print(f"📧 Empfänger gefunden: {recipients}")
        
        # Send the daily report
        notifier.send_daily_report()
        print("✅ Email erfolgreich gesendet!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Email-Senden: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_removed_jobs_marked():
    """Check if removed jobs were marked as notified"""
    print("\n=== CHECK NOTIFIED STATUS ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN notified = 1 THEN 1 ELSE 0 END) as notified,
               SUM(CASE WHEN notified = 0 THEN 1 ELSE 0 END) as not_notified
        FROM removed_jobs 
        WHERE company LIKE 'EmailTest%'
    ''')
    
    total, notified, not_notified = cursor.fetchone()
    
    print(f"📊 Removed Jobs Status:")
    print(f"   • Total: {total}")
    print(f"   • Notified: {notified}")
    print(f"   • Not Notified: {not_notified}")
    
    conn.close()
    
    return notified, not_notified

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== CLEANUP TEST DATA ===")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM crawl_results WHERE company LIKE 'EmailTest%'")
    results_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM removed_jobs WHERE company LIKE 'EmailTest%'")
    removed_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM keywords WHERE crawl_id IN (SELECT id FROM crawls WHERE title LIKE 'EmailTest%')")
    keywords_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM crawls WHERE title LIKE 'EmailTest%'")
    crawls_deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"🧹 Gelöscht:")
    print(f"   • {results_deleted} crawl_results")
    print(f"   • {removed_deleted} removed_jobs")
    print(f"   • {keywords_deleted} keywords")
    print(f"   • {crawls_deleted} crawls")

def main():
    """Run the complete email test"""
    print("=== EMAIL NOTIFICATION TEST ===\n")
    
    try:
        # 1. Setup test data
        crawl_ids = setup_test_email_data()
        
        # 2. Verify test data
        new_count, removed_count = check_test_data(crawl_ids)
        
        # 3. Test email formatting
        format_success = test_email_formatting()
        
        if not format_success:
            print("❌ Email-Formatting fehlgeschlagen - Test abgebrochen")
            return False
        
        # 4. Optional: Actually send email
        send_email = input("\n🤔 Soll das Email tatsächlich gesendet werden? (y/N): ").lower().strip()
        actually_send = send_email in ['y', 'yes', 'ja', 'j']
        
        if actually_send:
            send_success = test_send_email(actually_send=True)
            
            if send_success:
                # 5. Check if removed jobs were marked as notified
                check_removed_jobs_marked()
        else:
            print("📧 Email-Test übersprungen")
        
        # 6. Cleanup
        cleanup_choice = input("\n🧹 Test-Daten löschen? (Y/n): ").lower().strip()
        if cleanup_choice not in ['n', 'no', 'nein']:
            cleanup_test_data()
        else:
            print("🔒 Test-Daten beibehalten für weitere Tests")
        
        print(f"\n=== EMAIL TEST ABGESCHLOSSEN ===")
        print(f"✅ {new_count} neue Jobs getestet")
        print(f"✅ {removed_count} entfernte Jobs getestet") 
        print(f"✅ Email-Formatting funktioniert")
        if actually_send:
            print(f"✅ Email wurde gesendet")
        
        return True
        
    except Exception as e:
        print(f"❌ EMAIL TEST FEHLER: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main()