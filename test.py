#!/usr/bin/env python3
"""Simple test script"""

from browser_scraper import BrowserScraper

def test():
    """Test with first 3 URLs from urls.txt"""
    # Get first 3 URLs
    urls = []
    with open("urls.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
                if len(urls) >= 3:
                    break
    
    print(f"Testing {len(urls)} URLs...")
    
    scraper = BrowserScraper(headless=True, wait_time=10)
    
    try:
        scraper.setup_driver()
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/3] Processing...")
            post = scraper.extract_content(url)
            
            if post:
                scraper.posts.append(post)
                print(f"SUCCESS: {post['title']}")
                print(f"Date: {post['date']}")
                print(f"Categories: {post['categories']}")
            else:
                print("FAILED")
        
        # Generate XML if we got posts
        if scraper.posts:
            scraper.save_results("test_output.xml")
            print(f"\nCreated WordPress XML with {len(scraper.posts)} posts")
            print("File: test_output.xml")
        
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test()