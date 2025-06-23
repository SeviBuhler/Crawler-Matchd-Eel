import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database_config import get_db_path
from datetime import datetime, timedelta
from schedule import CrawlerScheduler

def setup_test_environment():
    """Setup test data and environment"""
    print("=== SETUP TEST ENVIRONMENT ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Clean up existing test data
    cursor.execute("DELETE FROM crawl_results WHERE company LIKE 'TestCorp%'")
    cursor.execute("DELETE FROM removed_jobs WHERE company LIKE 'TestCorp%'")
    cursor.execute("DELETE FROM keywords WHERE crawl_id IN (SELECT id FROM crawls WHERE title = 'Test Crawl')")
    cursor.execute("DELETE FROM crawls WHERE title = 'Test Crawl'")
    
    # Create test crawl configuration
    cursor.execute('''
        INSERT INTO crawls (title, url, scheduleTime, scheduleDay)
        VALUES ('Test Crawl', 'http://test-jobs.com', '09:00', 'monday,tuesday,wednesday,thursday,friday')
    ''')
    test_crawl_id = cursor.lastrowid
    
    # Add keywords for the test crawl
    test_keywords = ['python', 'java']
    for keyword in test_keywords:
        cursor.execute('''
            INSERT INTO keywords (crawl_id, keyword)
            VALUES (?, ?)
        ''', (test_crawl_id, keyword))
    
    # Create initial test jobs - NEUE STRUKTUR (ohne is_active, last_seen)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    test_jobs = [
        (test_crawl_id, "Senior Python Developer", "TestCorp A", "Zurich", "http://test1.com"),    # Will be found again
        (test_crawl_id, "Java Engineer", "TestCorp B", "Basel", "http://test2.com"),               # Will be removed  
        (test_crawl_id, "Frontend Developer", "TestCorp D", "Geneva", "http://test4.com"),         # Will be removed
    ]
    
    for crawl_id, title, company, location, link in test_jobs:
        cursor.execute('''
            INSERT INTO crawl_results 
            (crawl_id, crawl_url, title, company, location, link, crawl_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (crawl_id, "http://test-jobs.com", title, company, location, link, yesterday))
    
    conn.commit()
    conn.close()
    
    print(f"Created test crawl with ID: {test_crawl_id}")
    print("Initial test jobs:")
    print("  1. Senior Python Developer (TestCorp A) - will be found again")
    print("  2. Java Engineer (TestCorp B) - will be removed") 
    print("  3. Frontend Developer (TestCorp D) - will be removed")
    
    return test_crawl_id

def mock_crawler_results():
    """Simulate crawler results - only some jobs found"""
    return [
        {
            'title': 'Senior Python Developer',
            'company': 'TestCorp A',
            'location': 'Zurich',
            'link': 'http://test1.com'  # Existing job - will be updated
        },
        {
            'title': 'Full Stack Developer', 
            'company': 'TestCorp E',
            'location': 'Lausanne',
            'link': 'http://test5.com'  # New job - will be inserted
        }
    ]

def check_database_before_crawl(test_crawl_id):
    """Check database state before crawl"""
    print("\n=== DATABASE STATE BEFORE CRAWL ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check crawl_results - OHNE is_active
    cursor.execute('''
        SELECT title, company, link 
        FROM crawl_results 
        WHERE crawl_id = ? AND company LIKE 'TestCorp%'
        ORDER BY title
    ''', (test_crawl_id,))
    
    print("CRAWL_RESULTS:")
    crawl_results = cursor.fetchall()
    for title, company, link in crawl_results:
        print(f"  - {title} ({company}): {link}")
    
    # Check removed_jobs
    cursor.execute('''
        SELECT title, company, removal_date
        FROM removed_jobs 
        WHERE company LIKE 'TestCorp%'
        ORDER BY title
    ''')
    
    print(f"\nREMOVED_JOBS:")
    removed_jobs = cursor.fetchall()
    if removed_jobs:
        for title, company, removal_date in removed_jobs:
            print(f"  - {title} ({company}): {removal_date}")
    else:
        print("  (keine Einträge)")
    
    conn.close()
    
    return {
        'total_jobs': len(crawl_results),
        'removed_jobs': len(removed_jobs)
    }

def patch_crawler_for_test():
    """Temporarily patch the Crawler class to return test data"""
    from crawler import Crawler
    
    # Store original method
    original_crawl = Crawler.crawl
    
    # Replace with mock
    def mock_crawl(self, start_url, keywords, max_pages=30):
        print(f"MOCK CRAWLER: Simulating crawl of {start_url} with keywords {keywords}")
        return mock_crawler_results()
    
    Crawler.crawl = mock_crawl
    
    return original_crawl

def restore_crawler(original_crawl):
    """Restore original crawler method"""
    from crawler import Crawler
    Crawler.crawl = original_crawl

def execute_test_crawl(test_crawl_id):
    """Execute the actual crawl using the scheduler"""
    print("\n=== EXECUTING TEST CRAWL ===\n")
    
    # Patch crawler to return test data
    original_crawl = patch_crawler_for_test()
    
    try:
        # Create scheduler and execute crawl
        scheduler = CrawlerScheduler()
        
        # Execute the crawl
        scheduler.execute_crawl(
            crawl_id=test_crawl_id,
            url="http://test-jobs.com", 
            keywords=["python", "java"]
        )
        
        print("Test crawl completed!")
        
    finally:
        # Restore original crawler
        restore_crawler(original_crawl)

def check_database_after_crawl(test_crawl_id, before_stats):
    """Check database state after crawl and analyze results"""
    print("\n=== DATABASE STATE AFTER CRAWL ===\n")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check crawl_results - OHNE is_active
    cursor.execute('''
        SELECT title, company, link 
        FROM crawl_results 
        WHERE crawl_id = ? AND company LIKE 'TestCorp%'
        ORDER BY title
    ''', (test_crawl_id,))
    
    print("CRAWL_RESULTS:")
    crawl_results = cursor.fetchall()
    for title, company, link in crawl_results:
        print(f"  - {title} ({company}): {link}")
    
    # Check removed_jobs
    cursor.execute('''
        SELECT job_id, title, company, removal_date, notified
        FROM removed_jobs 
        WHERE company LIKE 'TestCorp%'
        ORDER BY title
    ''')
    
    print(f"\nREMOVED_JOBS:")
    removed_jobs = cursor.fetchall()
    if removed_jobs:
        for job_id, title, company, removal_date, notified in removed_jobs:
            print(f"  - {title} ({company}): {removal_date} (notified: {notified})")
    else:
        print("  (keine Einträge)")
    
    # Check for duplicates in removed_jobs
    cursor.execute('''
        SELECT job_id, COUNT(*) as count
        FROM removed_jobs 
        WHERE company LIKE 'TestCorp%'
        GROUP BY job_id
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    print(f"\nDUPLIKATE IN REMOVED_JOBS:")
    if duplicates:
        for job_id, count in duplicates:
            print(f"  ❌ Job ID {job_id}: {count} Einträge")
    else:
        print("  ✅ Keine Duplikate gefunden")
    
    conn.close()
    
    # Calculate stats
    after_stats = {
        'total_jobs': len(crawl_results),
        'removed_jobs': len(removed_jobs),
        'duplicates': len(duplicates)
    }
    
    return after_stats

def analyze_results(before_stats, after_stats):
    """Analyze the crawl results"""
    print("\n=== ERGEBNIS-ANALYSE ===\n")
    
    print("ERWARTETE ERGEBNISSE (NACH MIGRATION):")
    print("  - Senior Python Developer: BLEIBT in crawl_results (gefunden, updated)")
    print("  - Java Engineer: GELÖSCHT aus crawl_results → removed_jobs")
    print("  - Frontend Developer: GELÖSCHT aus crawl_results → removed_jobs")
    print("  - Full Stack Developer: NEU in crawl_results (neu hinzugefügt)")
    
    print(f"\nSTATISTIK-VERGLEICH:")
    print(f"  Jobs vor Crawl:  {before_stats['total_jobs']} gesamt")
    print(f"  Jobs nach Crawl: {after_stats['total_jobs']} gesamt")
    print(f"  Removed Jobs:    {before_stats['removed_jobs']} → {after_stats['removed_jobs']}")
    
    print(f"\nERWARTUNG vs. REALITÄT:")
    
    # Expected: 2 jobs in crawl_results (1 updated + 1 new)
    if after_stats['total_jobs'] == 2:
        print("  ✅ Crawl Results: Korrekt (2 verbleibend)")
    else:
        print(f"  ❌ Crawl Results: Falsch ({after_stats['total_jobs']} statt 2)")
    
    # Expected: 2 removed jobs (2 nicht gefunden)
    if after_stats['removed_jobs'] == 2:
        print("  ✅ Removed Jobs: Korrekt (2 erwartet)")
    else:
        print(f"  ❌ Removed Jobs: Falsch ({after_stats['removed_jobs']} statt 2)")
    
    # Expected: 0 duplicates
    if after_stats['duplicates'] == 0:
        print("  ✅ Duplikate: Keine gefunden")
    else:
        print(f"  ❌ Duplikate: {after_stats['duplicates']} gefunden!")
    
    # Overall success
    success = (after_stats['total_jobs'] == 2 and 
              after_stats['removed_jobs'] == 2 and 
              after_stats['duplicates'] == 0)
    
    if success:
        print(f"\n🎉 TEST ERFOLGREICH: execute_crawl funktioniert nach Migration korrekt!")
    else:
        print(f"\n❌ TEST FEHLGESCHLAGEN: execute_crawl hat nach Migration Probleme!")
    
    return success

def cleanup_test_data(test_crawl_id):
    """Clean up test data"""
    print(f"\n=== CLEANUP TEST DATA ===")
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM crawl_results WHERE company LIKE 'TestCorp%'")
    results_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM removed_jobs WHERE company LIKE 'TestCorp%'")
    removed_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM keywords WHERE crawl_id = ?", (test_crawl_id,))
    keywords_deleted = cursor.rowcount
    
    cursor.execute("DELETE FROM crawls WHERE id = ?", (test_crawl_id,))
    crawls_deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Gelöscht: {results_deleted} crawl_results, {removed_deleted} removed_jobs, {keywords_deleted} keywords, {crawls_deleted} crawls")

def main():
    """Run the complete test"""
    print("=== EXECUTE_CRAWL TEST NACH MIGRATION ===\n")
    
    try:
        # 1. Setup
        test_crawl_id = setup_test_environment()
        
        # 2. Check before
        before_stats = check_database_before_crawl(test_crawl_id)
        
        # 3. Execute crawl
        execute_test_crawl(test_crawl_id)
        
        # 4. Check after
        after_stats = check_database_after_crawl(test_crawl_id, before_stats)
        
        # 5. Analyze
        success = analyze_results(before_stats, after_stats)
        
        # 6. Cleanup
        cleanup_test_data(test_crawl_id)
        
        print(f"\n=== TEST ABGESCHLOSSEN ===")
        return success
        
    except Exception as e:
        print(f"❌ TEST FEHLER: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main()