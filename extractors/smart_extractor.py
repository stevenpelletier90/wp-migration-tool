#!/usr/bin/env python3
"""Smart hybrid extractor - simple and reliable"""

from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import newspaper
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from trafilatura import extract, extract_metadata


def extract_blog_post(url: str) -> Optional[Dict]:
    """
    Smart extraction: try trafilatura first (fast), fallback to newspaper3k if needed.
    Simple and reliable.
    """
    print(f"Extracting: {url}")
    
    # Try trafilatura first (faster)
    result = try_trafilatura(url)
    if is_good_quality(result):
        print(f"  [trafilatura] SUCCESS: {result['title']}")
        return result
    
    # Fallback to newspaper3k
    print("  [trafilatura] Poor quality, trying newspaper3k")
    result = try_newspaper3k(url)
    if is_good_quality(result):
        print(f"  [newspaper3k] SUCCESS: {result['title']}")
        return result
    
    print("  [FAILED] Both methods failed")
    return None


def is_good_quality(result: Optional[Dict]) -> bool:
    """Check if extraction result is good quality"""
    if not result:
        return False
    
    title = result.get('title', '')
    content = result.get('content', '')
    
    # Basic quality checks
    return (
        len(title) > 5 and len(title) < 200 and
        len(content) > 300 and
        '<' in content  # Has HTML content
    )


def try_trafilatura(url: str) -> Optional[Dict]:
    """Try extraction with trafilatura"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        content = extract(response.text, include_links=True, include_tables=True, output_format='html')
        metadata = extract_metadata(response.text)
        
        if not content or not metadata or not metadata.title:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tags, categories = extract_tags_categories(soup)
        hyperlinks = extract_links(content, url)
        
        # Generate slug from title
        slug = metadata.title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:50]
        
        return {
            'url': url,
            'title': metadata.title.strip(),
            'slug': slug,
            'content': content,
            'date': metadata.date or extract_date(soup),
            'author': metadata.author or 'Unknown',
            'categories': categories,
            'tags': tags,
            'hyperlinks': hyperlinks,
            'method': 'trafilatura'
        }
    except Exception as e:
        print(f"    trafilatura error: {e}")
        return None


def try_newspaper3k(url: str) -> Optional[Dict]:
    """Try extraction with newspaper3k"""
    try:
        config = newspaper.Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        config.request_timeout = 12
        
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        if not article.title or not article.html:
            return None
        
        soup = BeautifulSoup(article.html, 'html.parser')
        tags, categories = extract_tags_categories(soup)
        
        # Get clean content from article
        content_area = find_content_area(soup)
        clean_content = clean_html_content(content_area) if content_area else article.text
        
        hyperlinks = extract_links(str(content_area) if content_area else article.html, url)
        
        # Generate slug from title
        slug = article.title.lower().replace(' ', '-').replace('&', 'and')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:50]
        
        return {
            'url': url,
            'title': article.title.strip(),
            'slug': slug,
            'content': clean_content,
            'date': article.publish_date or extract_date(soup),
            'author': ', '.join(article.authors) if article.authors else 'Unknown',
            'categories': categories,
            'tags': tags,
            'hyperlinks': hyperlinks,
            'method': 'newspaper3k'
        }
    except Exception as e:
        print(f"    newspaper3k error: {e}")
        return None


def find_content_area(soup: BeautifulSoup):
    """Find main content area"""
    selectors = ['.entry-content', '.post-content', '.article-content', 'article', 'main']
    for selector in selectors:
        area = soup.select_one(selector)
        if area and len(area.get_text(strip=True)) > 100:
            return area
    return None


def clean_html_content(content_area) -> str:
    """Clean HTML content while preserving links"""
    if not content_area:
        return ""
    
    # Remove scripts, styles
    for tag in content_area.find_all(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    
    # Keep only essential attributes
    for element in content_area.find_all(True):
        if hasattr(element, 'attrs'):
            allowed = {}
            if element.name == 'a' and 'href' in element.attrs:
                allowed['href'] = element.attrs['href']
            elif element.name == 'img' and 'src' in element.attrs:
                allowed['src'] = element.attrs['src']
                if 'alt' in element.attrs:
                    allowed['alt'] = element.attrs['alt']
            element.attrs = allowed
    
    return str(content_area)


def extract_tags_categories(soup: BeautifulSoup) -> tuple[List[str], List[str]]:
    """Extract tags and categories"""
    tags = []
    categories = []
    
    # Find tags
    for selector in ['.tags a', '.post-tags a', '.entry-tags a']:
        for link in soup.select(selector):
            text = link.get_text(strip=True)
            if text and len(text) < 50:
                tags.append(text)
    
    # Find categories  
    for selector in ['.categories a', '.post-categories a']:
        for link in soup.select(selector):
            text = link.get_text(strip=True)
            if text and len(text) < 50:
                categories.append(text)
    
    return list(set(tags))[:10], list(set(categories))[:5]


def extract_links(content: str, base_url: str) -> Dict[str, List[Dict]]:
    """Extract and categorize hyperlinks"""
    soup = BeautifulSoup(content, 'html.parser')
    internal = []
    external = []
    relative = []
    
    base_domain = urlparse(base_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:')):
            continue
        
        text = link.get_text(strip=True) or '[No text]'
        
        if href.startswith('http'):
            domain = urlparse(href).netloc
            if domain == base_domain:
                internal.append({'url': href, 'text': text, 'domain': domain})
            else:
                external.append({'url': href, 'text': text, 'domain': domain})
        else:
            relative.append({'url': href, 'text': text})
    
    return {
        'internal_links': internal,
        'external_links': external, 
        'relative_links': relative
    }


def extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    """Extract publication date"""
    for selector in ['meta[property="article:published_time"]', 'meta[name="date"]', 'time[datetime]']:
        element = soup.select_one(selector)
        if element:
            date_str = element.get('content') or element.get('datetime')
            if date_str:
                try:
                    from dateutil import parser
                    return parser.parse(date_str)
                except Exception:
                    continue
    return None


if __name__ == "__main__":
    # Test
    test_url = "https://www.parkfordofmahopac.com/blog/2025/march/25/shop-at-our-used-dealership-near-yorktown-heights.htm"
    result = extract_blog_post(test_url)
    if result:
        print(f"\nTitle: {result['title']}")
        print(f"Method: {result['method']}")
        print(f"Content length: {len(result['content'])}")
        print(f"Links: {len(result['hyperlinks']['relative_links'])} relative")
    else:
        print("Failed")