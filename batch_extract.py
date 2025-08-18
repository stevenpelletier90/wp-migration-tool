#!/usr/bin/env python3
"""
Batch extraction from URLs in config/urls.txt
Fast backend processing without web interface
"""

from datetime import datetime
from pathlib import Path

from extractors.smart_extractor import extract_blog_post
from extractors.xml_generator import generate_wordpress_xml_fixed


def load_urls_from_file():
    """Load URLs from config/urls.txt"""
    urls_file = Path("config/urls.txt")
    if not urls_file.exists():
        print("ERROR: config/urls.txt not found!")
        return []
    
    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    
    print(f"Loaded {len(urls)} URLs from config/urls.txt")
    return urls


def batch_extract():
    """Extract all URLs and generate WordPress XML"""
    urls = load_urls_from_file()
    if not urls:
        return
    
    print(f"Starting batch extraction of {len(urls)} URLs...")
    print("=" * 60)
    
    posts = []
    failed = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        
        try:
            post = extract_blog_post(url)
            if post:
                posts.append(post)
                print(f"  SUCCESS: {post['title']}")
                print(f"     Method: {post['method']}")
                print(f"     Content: {len(post['content'])} chars")
                print(f"     Links: {len(post['hyperlinks']['relative_links'])} relative")
                print(f"     Tags: {len(post['tags'])}, Categories: {len(post['categories'])}")
            else:
                failed.append(url)
                print("  FAILED: No content extracted")
        except Exception as e:
            failed.append(url)
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print(f"   Successful: {len(posts)}")
    print(f"   Failed: {len(failed)}")
    print(f"   Success rate: {len(posts)/(len(posts)+len(failed))*100:.1f}%")
    
    if failed:
        print("\nFailed URLs:")
        for url in failed:
            print(f"   - {url}")
    
    if posts:
        print("\nGenerating WordPress XML...")
        xml_content = generate_wordpress_xml_fixed(posts)
        
        # Save to output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"wordpress_import_batch_{timestamp}.xml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"WordPress XML saved: {output_file}")
        print(f"Contains {len(posts)} posts ready for WordPress import")
        print("\nImport instructions:")
        print("   1. WordPress Admin -> Tools -> Import -> WordPress")
        print(f"   2. Upload: {output_file}")
        print("   3. Assign author and import attachments")
        print("   4. Run import")
    else:
        print("\nNo posts extracted - cannot generate XML")


if __name__ == "__main__":
    print("WordPress Migration Tool - Batch Extractor")
    print("=" * 60)
    batch_extract()
    print("\nDone!")