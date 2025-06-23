import sys
import os

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from crawler import Crawler

def test_crawl():
    print("=== CRAWLER TEST ===\n")
    
    # Create crawler instance
    crawler = Crawler()
    
    # Test parameters
    test_url = "https://www.hostpoint.ch/jobs/"
    test_keywords = ['praktikant', 'praktikum', 'werkstudent', 'lehrstelle']
    
    print(f"Testing URL: {test_url}")
    print(f"Keywords: {test_keywords}")
    print("\n" + "="*50)
    
    try:
        # Execute crawl
        results = crawler.crawl(test_url, test_keywords, max_pages=2)
        
        # Analyze results
        if results is not None:
            print(f"\n✅ Crawl successful!")
            print(f"📊 Found {len(results)} jobs")
            
            if results:
                print("\n📋 Job Details:")
                for i, job in enumerate(results, 1):
                    print(f"\n{i}. {job['title']}")
                    print(f"   Company: {job['company']}")
                    print(f"   Location: {job['location']}")
                    print(f"   Link: {job['link']}")
            else:
                print("\n📭 No jobs found matching keywords")
        else:
            print("\n❌ Crawl failed - returned None")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    print(f"\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_crawl()
    