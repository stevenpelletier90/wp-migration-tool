#!/usr/bin/env python3
"""
Browser-based scraper using Selenium to handle JavaScript-heavy and protected sites
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BrowserScraper:
    def __init__(self, headless: bool = False, wait_time: int = 10):
        """
        Initialize the browser scraper
        
        Args:
            headless: Run browser in headless mode (no GUI)
            wait_time: Default wait time for page loads
        """
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.posts = []
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        options = Options()
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Set user agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            # Additional anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("Browser initialized successfully")
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            print("\nPlease ensure Chrome and ChromeDriver are installed:")
            print("1. Install Google Chrome")
            print("2. Download ChromeDriver from: https://chromedriver.chromium.org/")
            print("3. Add ChromeDriver to your PATH or place it in this directory")
            raise
    
    def extract_content(self, url: str) -> Optional[Dict]:
        """Extract content from a single URL using browser"""
        if not self.driver:
            self.setup_driver()
        
        print(f"\nProcessing: {url}")
        
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for content to load
            time.sleep(3)  # Initial wait for JavaScript
            
            # Try to wait for specific content elements
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        '.et_pb_post_content, .entry-content, .post-content, article, main'))
                )
            except TimeoutException:
                print("  Warning: Content elements not found within timeout")
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract title
            title = None
            title_selectors = [
                'h1.entry-title',
                'h1.post-title', 
                'h1[itemprop="headline"]',
                '.et_pb_title_featured_container h1',
                'article h1',
                'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:  # Valid title
                        break
            
            if not title:
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Clean common suffixes
                    title = re.sub(r'\s*[-|]\s*.*$', '', title)
            
            # Extract date
            pub_date = None
            
            # Try et_pb_title_meta_container first (Divi theme)
            meta_container = soup.select_one('.et_pb_title_meta_container')
            if meta_container:
                meta_text = meta_container.get_text()
                date_patterns = [
                    r'(\w+ \d{1,2}, \d{4})',  # January 15, 2024
                    r'(\d{1,2}/\d{1,2}/\d{4})',  # 01/15/2024
                    r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, meta_text)
                    if date_match:
                        try:
                            from dateutil import parser
                            pub_date = parser.parse(date_match.group(1))
                            break
                        except Exception:
                            pass
            
            # Try other date selectors
            if not pub_date:
                date_selectors = [
                    'time[datetime]',
                    '.entry-date',
                    '.post-date',
                    '.published',
                    'span.date'
                ]
                
                for selector in date_selectors:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                        try:
                            from dateutil import parser
                            pub_date = parser.parse(date_text)
                            break
                        except Exception:
                            pass
            
            # Extract categories
            categories = []
            
            # Check meta container for categories (Divi)
            if meta_container:
                cat_links = meta_container.find_all('a', href=lambda x: x and '/category/' in x)
                for link in cat_links:
                    cat_text = link.get_text(strip=True)
                    if cat_text and len(cat_text) < 50:
                        categories.append(cat_text)
            
            # Try other category selectors
            if not categories:
                cat_selectors = [
                    '.categories a',
                    '.category-list a',
                    '.post-categories a',
                    'a[rel="category"]'
                ]
                
                for selector in cat_selectors:
                    cat_links = soup.select(selector)
                    for link in cat_links:
                        cat_text = link.get_text(strip=True)
                        if cat_text and len(cat_text) < 50:
                            categories.append(cat_text)
                    if categories:
                        break
            
            # Extract main content
            content_area = None
            content_selectors = [
                '.et_pb_module.et_pb_post_content',
                '.et_pb_post_content_0_tb_body',
                '.et_pb_post_content',
                '.fl-darklinks',
                '.entry-content',
                '.post-content',
                '.article-content',
                'article .content',
                '[itemprop="articleBody"]',
                'article',
                'main'
            ]
            
            for selector in content_selectors:
                content_area = soup.select_one(selector)
                if content_area and len(content_area.get_text(strip=True)) > 100:
                    break
            
            if not content_area:
                print("  Could not find main content area")
                return None
            
            # Clean and extract content
            clean_html = self.clean_content(content_area)
            
            # Generate slug
            slug = url.split('/')[-1] or url.split('/')[-2]
            slug = re.sub(r'\.html?$', '', slug)
            slug = re.sub(r'[^a-z0-9-]', '-', slug.lower())
            
            post = {
                'url': url,
                'title': title or 'Untitled',
                'content': clean_html,  # Remove wrapper div for WordPress visual editor
                'date': pub_date or datetime.now(),
                'author': 'Unknown',
                'slug': slug or 'post',
                'categories': categories,
                'tags': [],
                'method': 'browser_automation'
            }
            
            print(f"  Extracted: {post['title'][:50]}...")
            return post
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def title_case(self, text):
        """Convert text to Title Case"""
        if not text:
            return text
        
        # Words that should stay lowercase unless they're the first/last word
        articles = ['a', 'an', 'the']
        prepositions = ['of', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from', 'up', 'out', 'off', 'over']
        conjunctions = ['and', 'but', 'or', 'nor', 'so', 'yet']
        lowercase_words = articles + prepositions + conjunctions
        
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            # Always capitalize first and last word
            if i == 0 or i == len(words) - 1:
                result.append(word.capitalize())
            # Keep lowercase words lowercase unless they start with capital (proper noun)
            elif word.lower() in lowercase_words and not word[0].isupper():
                result.append(word.lower())
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)

    def clean_content(self, content_area) -> str:
        """Clean extracted content"""
        # Clone to avoid modifying original
        content = BeautifulSoup(str(content_area), 'html.parser')
        
        # Remove unwanted elements
        for element in content.find_all(['script', 'style', 'noscript', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Remove share buttons and social elements
        for element in content.find_all(class_=re.compile(r'share|social|comment|sidebar|widget')):
            element.decompose()
        
        clean_html = ""
        
        # Extract text elements
        for elem in content.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'blockquote']):
            if elem.get_text(strip=True):
                # Clean attributes but keep links
                for tag in elem.find_all(True):
                    if tag.name == 'a' and 'href' in tag.attrs:
                        tag.attrs = {'href': tag.attrs['href']}
                    elif tag.name == 'img':
                        if 'src' in tag.attrs:
                            tag.attrs = {
                                'src': tag.attrs['src'],
                                'alt': tag.attrs.get('alt', '')
                            }
                    else:
                        tag.attrs = {}
                
                clean_html += str(elem) + "\n\n"
        
        # Add images
        images = content_area.find_all('img', src=True)
        if images:
            clean_html += "\n<!-- Images from original post -->\n"
            for img in images:
                src = img.get('src', '')
                alt = img.get('alt', '')
                # Skip tracking pixels
                if src and not any(tracker in src.lower() for tracker in 
                                  ['analytics', 'pixel', 'tracking', 'doubleclick', 'google-analytics']):
                    clean_html += f'<img src="{src}" alt="{alt}" />\n'
        
        return clean_html
    
    def process_urls(self, urls: List[str], delay: int = 2) -> List[Dict]:
        """Process multiple URLs with delay between requests"""
        self.posts = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing URL...")
            
            post = self.extract_content(url)
            if post:
                self.posts.append(post)
            
            # Delay between requests to be respectful
            if i < len(urls):
                print(f"  Waiting {delay} seconds before next request...")
                time.sleep(delay)
        
        return self.posts
    
    def save_results(self, output_file: str = "browser_export.xml"):
        """Save extracted posts to WordPress XML"""
        if not self.posts:
            print("No posts to save")
            return
        
        # Use fixed XML generation to avoid double-encoding
        from .fixed_extractor import generate_wordpress_xml_fixed
        xml_content = generate_wordpress_xml_fixed(self.posts)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"\nSaved {len(self.posts)} posts to {output_file}")
        
        # Also save as JSON for debugging
        json_file = output_file.replace('.xml', '.json')
        posts_json = []
        for post in self.posts:
            post_copy = post.copy()
            if post_copy.get('date'):
                post_copy['date'] = post_copy['date'].isoformat()
            posts_json.append(post_copy)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(posts_json, f, indent=2)
        
        print(f"Debug data saved to {json_file}")
    
    def cleanup(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\nBrowser closed")


def main():
    """Automated browser scraper - reads from config/urls.txt"""
    print("=" * 60)
    print("AUTOMATED BROWSER SCRAPER")
    print("=" * 60)
    
    # Load URLs from config
    urls = []
    urls_file = os.path.join(os.path.dirname(__file__), "..", "config", "urls.txt")
    
    if os.path.exists(urls_file):
        with open(urls_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    
    if not urls:
        print(f"No URLs found in {urls_file}")
        print("Add URLs to config/urls.txt (one per line)")
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
        print(f"This will take approximately {len(urls) * 5} seconds\n")
        
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
                    print("  FAILED: Could not extract content")
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
            output_file = os.path.join(os.path.dirname(__file__), "..", "output", "wordpress_import.xml")
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
            failed_file = os.path.join(os.path.dirname(__file__), "..", "output", "failed_urls.txt")
            with open(failed_file, "w") as f:
                for url in failed:
                    f.write(url + "\n")
            print(f"\nFailed URLs saved to: {failed_file}")
            print("You can retry these URLs later")
    
    except Exception as e:
        print(f"\nError during processing: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Google Chrome is installed")
        print("2. Download ChromeDriver from: https://chromedriver.chromium.org/")
        print("3. Place chromedriver.exe in config/ directory or in PATH")
    
    finally:
        # Cleanup
        try:
            scraper.cleanup()
        except Exception:
            pass
        print("\nProcessing complete!")


if __name__ == "__main__":
    main()