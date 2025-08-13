#!/usr/bin/env python3
"""
Fully automated scraper - no interaction required
Just run: python run_scraper.py
"""

import os
import sys
import time
from browser_scraper import BrowserScraper


def main():
    print("=" * 60)
    print("AUTOMATED BLOG SCRAPER")
    print("=" * 60)
    
    # Load URLs
    urls = []
    if os.path.exists("urls.txt"):
        with open("urls.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    
    if not urls:
        print("No URLs found in urls.txt")
        return
    
    print(f"\nFound {len(urls)} URLs to process")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    # Create scraper (headless by default for automation)
    print("\nInitializing Chrome browser (headless mode)...")
    scraper = BrowserScraper(headless=True, wait_time=10)
    
    try:
        # Setup browser
        scraper.setup_driver()
        print("Browser initialized successfully\n")
        
        # Process each URL
        print(f"Processing {len(urls)} URLs...")
        print("This will take approximately {len(urls) * 5} seconds\n")
        
        successful = 0
        failed = []
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Processing...")
            print(f"  URL: {url[:80]}...")
            
            try:
                post = scraper.extract_content(url)
                
                if post:
                    scraper.posts.append(post)
                    successful += 1
                    print(f"  SUCCESS: {post['title'][:60]}...")
                else:
                    failed.append(url)
                    print(f"  FAILED: Could not extract content")
            except Exception as e:
                failed.append(url)
                print(f"  ERROR: {str(e)[:60]}")
            
            # Progress indicator
            progress = (i / len(urls)) * 100
            print(f"  Progress: {progress:.1f}% complete\n")
            
            # Respectful delay
            if i < len(urls):
                time.sleep(3)
        
        # Results summary
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Successfully extracted: {successful}/{len(urls)} posts")
        
        if scraper.posts:
            # Save WordPress XML
            output_file = "wordpress_import.xml"
            scraper.save_results(output_file)
            
            print(f"\nWordPress import file created: {output_file}")
            print("\nTo import into WordPress:")
            print("1. Go to WordPress Admin -> Tools -> Import")
            print("2. Select 'WordPress' importer")
            print("3. Upload wordpress_import.xml")
            print("4. Assign authors and import")
        
        if failed:
            print(f"\nFailed to extract {len(failed)} URLs:")
            for url in failed[:5]:  # Show first 5
                print(f"  - {url}")
            if len(failed) > 5:
                print(f"  ... and {len(failed) - 5} more")
            
            # Save failed URLs
            with open("failed_urls.txt", "w") as f:
                for url in failed:
                    f.write(url + "\n")
            print("\nFailed URLs saved to: failed_urls.txt")
            print("You can retry these URLs later")
    
    except Exception as e:
        print(f"\nError during processing: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Google Chrome is installed")
        print("2. Download ChromeDriver from: https://chromedriver.chromium.org/")
        print("3. Place chromedriver.exe in this directory or in PATH")
    
    finally:
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass
        print("\nProcessing complete!")


if __name__ == "__main__":
    main()