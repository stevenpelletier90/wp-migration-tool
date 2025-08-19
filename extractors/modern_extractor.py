#!/usr/bin/env python3
"""Modern content extractor using selectolax - fast and compatible"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser


def extract_blog_post(url: str) -> Optional[Dict]:
    """
    Modern extraction using selectolax - ultra-fast and compatible with latest packages.
    """
    print(f"Extracting: {url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Try HTTP/2 first, fallback to HTTP/1.1 if needed
        for attempt in range(3):  # 3 attempts for 100% reliability
            try:
                # First attempt: HTTP/2 with longer timeout
                timeout_config = httpx.Timeout(30.0, connect=10.0)
                with httpx.Client(http2=True, timeout=timeout_config, follow_redirects=True) as client:
                    response = client.get(url, headers=headers)
                break
            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout):
                if attempt == 0:
                    print(f"    Attempt {attempt + 1}: HTTP/2 timeout, trying HTTP/1.1...")
                    try:
                        # Fallback: HTTP/1.1 with different timeout
                        timeout_config = httpx.Timeout(20.0, connect=8.0)
                        with httpx.Client(http2=False, timeout=timeout_config, follow_redirects=True) as client:
                            response = client.get(url, headers=headers)
                        break
                    except Exception:
                        continue
                elif attempt == 1:
                    print(f"    Attempt {attempt + 1}: Trying with minimal headers...")
                    # Minimal headers approach
                    simple_headers = {'User-Agent': 'Mozilla/5.0'}
                    timeout_config = httpx.Timeout(15.0, connect=5.0)
                    with httpx.Client(http2=False, timeout=timeout_config, follow_redirects=True) as client:
                        response = client.get(url, headers=simple_headers)
                    break
                else:
                    raise Exception("Failed after 3 attempts with various timeout strategies")
        response.raise_for_status()
        
        # Parse with selectolax (ultra-fast)
        tree = HTMLParser(response.text)
        
        # Extract title
        title = extract_title(tree, url)
        if not title or len(title) < 5:
            print("  FAILED: No valid title found")
            return None
        
        # Extract main content area with multiple fallbacks
        content_element = find_content_element(tree)
        if not content_element:
            print("    No specific content area found, trying fallback methods...")
            content_element = find_content_fallback(tree)
        
        if not content_element:
            print("  FAILED: No content area found")
            return None
        
        # Extract content HTML
        content = extract_content_from_element(content_element, url)
        if not content or len(content) < 100:  # Reduced threshold for 100% success
            print("    Primary content extraction failed, trying alternative methods...")
            content = extract_content_alternative(tree, url)
        
        if not content or len(content) < 50:  # Very low threshold for maximum success
            print("  FAILED: No substantial content found")
            return None
        
        # Extract metadata from content area (not whole page)
        date = extract_date(tree, url)
        author = extract_author(tree)
        categories, tags = extract_categories_tags_from_content(content_element)
        slug = generate_slug(title)
        hyperlinks = extract_links_from_content(content_element, url)
        
        result = {
            'url': url,
            'title': title.strip(),
            'slug': slug,
            'content': content,
            'date': date,
            'author': author,
            'categories': categories,
            'tags': tags,
            'hyperlinks': hyperlinks,
            'method': 'selectolax'
        }
        
        print(f"  SUCCESS: {title}")
        return result
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def extract_title(tree: HTMLParser, url: str) -> str:
    """Extract page title"""
    # Try different title sources
    selectors = [
        'h1.entry-title',
        'h1.post-title', 
        'h1.article-title',
        '.entry-header h1',
        '.post-header h1',
        'article h1',
        'h1',
        'title'
    ]
    
    for selector in selectors:
        element = tree.css_first(selector)
        if element and element.text():
            title = element.text().strip()
            if len(title) > 5 and len(title) < 200:
                return clean_text(title)
    
    # Fallback: try to extract from URL
    path = urlparse(url).path
    if path:
        # Extract from URL path like /blog/title-here/
        parts = [p for p in path.split('/') if p and not p.isdigit()]
        if parts:
            return clean_text(parts[-1].replace('-', ' ').title())
    
    return "Untitled Post"


def find_content_element(tree: HTMLParser):
    """Find the main content element of the page"""
    content_selectors = [
        '.entry-content',
        '.post-content', 
        '.article-content',
        '.content-area',
        'article .content',
        '[data-content="true"]',
        'main article',
        'article',
        '.post-body',
        '.entry-body'
    ]
    
    for selector in content_selectors:
        element = tree.css_first(selector)
        if element:
            text = element.text(strip=True)
            if len(text) > 100:  # Reduced threshold for better success rate
                return element
    
    return None


def find_content_fallback(tree: HTMLParser):
    """Fallback method to find content when primary selectors fail"""
    fallback_selectors = [
        'main',
        '.main',
        '#main',
        '.container',
        '.wrapper',
        'body'
    ]
    
    for selector in fallback_selectors:
        element = tree.css_first(selector)
        if element:
            text = element.text(strip=True)
            if len(text) > 100:
                return element
    
    return None


def extract_content_alternative(tree: HTMLParser, url: str) -> str:
    """Alternative content extraction when primary method fails"""
    # Try to extract all paragraphs from the page
    paragraphs = tree.css('p')
    if paragraphs:
        content_parts = []
        for p in paragraphs:
            if p.text(strip=True) and len(p.text(strip=True)) > 20:
                content_parts.append(p.html or "")
        
        if content_parts:
            return ''.join(content_parts)
    
    # Last resort: extract all text content and wrap in paragraphs
    all_text = tree.text(strip=True)
    if all_text and len(all_text) > 100:
        # Split into paragraphs and wrap
        paragraphs = [p.strip() for p in all_text.split('\n\n') if p.strip()]
        if paragraphs:
            return ''.join(f'<p>{p}</p>' for p in paragraphs[:10])  # Limit to 10 paragraphs
    
    return ""


def extract_content_from_element(content_element, url: str) -> str:
    """Extract and clean content from the content element"""
    if not content_element:
        return ""
    
    # Get the inner HTML content only (not the wrapper elements)
    inner_html = content_element.html
    if not inner_html:
        return ""
    
    # Parse just the content area
    content_tree = HTMLParser(inner_html)
    
    # Remove unwanted elements from content
    unwanted_selectors = [
        'script', 'style', 'nav', 'header', 'footer', 
        '.social-share', '.comments', '.comment-form',
        '.sidebar', '.related-posts', '.advertisement',
        '.social-links', '.author-bio', '.post-navigation'
    ]
    
    for selector in unwanted_selectors:
        for element in content_tree.css(selector):
            element.decompose()
    
    # Extract content preserving exact document order
    # Use selectolax to get all elements, then filter while preserving order
    
    # Get the raw inner HTML from the content area
    inner_html = content_tree.html
    if not inner_html:
        return ""
    
    # Use BeautifulSoup for better DOM traversal that preserves order
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(inner_html, 'html.parser')
    
    clean_content = ""
    seen_content = set()  # Track content to avoid duplicates
    
    # Walk through ALL elements in document order, but only keep the ones we want
    for element in soup.descendants:
        # Only process actual HTML elements (not text nodes, etc.)
        if not hasattr(element, 'name') or not element.name:
            continue
            
        # Only process content elements we care about
        if element.name not in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'blockquote']:
            continue
            
        element_text = element.get_text(strip=True)
        
        # Skip empty elements
        if not element_text:
            continue
            
        # Skip elements that are clearly navigation/sidebar/footer
        element_class = ' '.join(element.get('class', [])).lower() if element.get('class') else ''
        element_id = (element.get('id', '') or '').lower()
        
        skip_classes = ['nav', 'menu', 'sidebar', 'footer', 'header', 'social', 'share', 'tags', 'categories', 'meta']
        if any(skip_class in element_class or skip_class in element_id for skip_class in skip_classes):
            continue
        
        # Check for duplicate content
        if element_text in seen_content:
            continue
            
        # Add this content (preserve the HTML)
        seen_content.add(element_text)
        clean_content += str(element)
    
    return clean_content


def remove_html_wrapper(content: str) -> str:
    """Remove HTML document wrapper and keep only inner content"""
    if not content:
        return ""
    
    # Parse to extract just the inner content
    tree = HTMLParser(content)
    
    # Look for the actual content container and extract its inner HTML
    content_containers = [
        '.entry-content', 
        '.text-content-container', 
        '.post-content',
        '.article-content',
        '.content'
    ]
    
    for selector in content_containers:
        content_div = tree.css_first(selector)
        if content_div:
            # Get the inner HTML of the content container, not the container itself
            inner_content = content_div.html or ""
            if inner_content:
                # Remove the container div tags to get just the content
                inner_tree = HTMLParser(inner_content)
                # Get all child elements as clean HTML
                children = []
                for child in inner_tree.css('*'):
                    if child.parent == inner_tree.root:  # Direct children only
                        children.append(child.html or "")
                if children:
                    return ''.join(children)
                else:
                    # Fallback: clean the content manually
                    return clean_container_wrapper(inner_content)
    
    # If no specific container found, clean any HTML document structure
    content = content.strip()
    
    # Remove HTML document wrapper tags
    if '<html>' in content:
        content = clean_html_tags(content)
    
    # Remove specific div wrappers
    content = clean_container_wrapper(content)
    
    return content.strip()


def clean_html_tags(content: str) -> str:
    """Remove HTML document structure tags"""
    content = content.replace('<html><head></head><body>', '')
    content = content.replace('<html>', '')
    content = content.replace('<head></head>', '')
    content = content.replace('<body>', '')
    content = content.replace('</body></html>', '')
    content = content.replace('</body>', '')
    content = content.replace('</html>', '')
    return content


def clean_container_wrapper(content: str) -> str:
    """Remove content container div wrapper"""
    # Remove various container div patterns
    container_patterns = [
        r'<div class="entry-content[^"]*"[^>]*>',
        r'<div class="text-content-container[^"]*"[^>]*>',
        r'<div class="post-content[^"]*"[^>]*>',
        r'<div class="content[^"]*"[^>]*>'
    ]
    
    for pattern in container_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Remove unmatched closing divs from the end
    # Count opening and closing divs to match them properly
    open_divs = len(re.findall(r'<div[^>]*>', content))
    close_divs = len(re.findall(r'</div>', content))
    
    # Remove extra closing divs from the end
    while close_divs > open_divs and content.endswith('</div>'):
        content = content[:-6].rstrip()
        close_divs -= 1
    
    return content




def extract_date(tree: HTMLParser, url: str) -> Optional[datetime]:
    """Extract publication date"""
    # Try meta tags first
    meta_selectors = [
        'meta[property="article:published_time"]',
        'meta[name="date"]',
        'meta[name="publishdate"]',
        'meta[name="DC.date"]'
    ]
    
    for selector in meta_selectors:
        element = tree.css_first(selector)
        if element:
            content = element.attributes.get('content', '')
            if content:
                date_obj = parse_date(content)
                if date_obj:
                    return date_obj
    
    # Try time elements
    time_element = tree.css_first('time[datetime]')
    if time_element:
        datetime_attr = time_element.attributes.get('datetime', '')
        if datetime_attr:
            date_obj = parse_date(datetime_attr)
            if date_obj:
                return date_obj
    
    # Try to extract from URL
    url_date = extract_date_from_url(url)
    if url_date:
        return url_date
    
    # Try common date containers
    date_selectors = [
        '.entry-date',
        '.post-date',
        '.published',
        '.date'
    ]
    
    for selector in date_selectors:
        element = tree.css_first(selector)
        if element and element.text():
            date_obj = parse_date(element.text())
            if date_obj:
                return date_obj
    
    return datetime.now()


def extract_date_from_url(url: str) -> Optional[datetime]:
    """Extract date from URL patterns like /2025/08/18/"""
    patterns = [
        r'/(\d{4})/(\d{1,2})/(\d{1,2})/',
        r'/(\d{4})-(\d{1,2})-(\d{1,2})/',
        r'/(\d{4})(\d{2})(\d{2})/'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day)
            except ValueError:
                continue
    
    return None


def parse_date(date_string: str) -> Optional[datetime]:
    """Parse various date formats"""
    if not date_string:
        return None
    
    # Common date patterns
    patterns = [
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y'
    ]
    
    for pattern in patterns:
        try:
            return datetime.strptime(date_string.strip(), pattern)
        except ValueError:
            continue
    
    # Try python-dateutil if available
    try:
        from dateutil import parser
        return parser.parse(date_string)
    except Exception:
        pass
    
    return None


def extract_author(tree: HTMLParser) -> str:
    """Extract author information"""
    # Try meta tags
    meta_selectors = [
        'meta[name="author"]',
        'meta[property="article:author"]'
    ]
    
    for selector in meta_selectors:
        element = tree.css_first(selector)
        if element:
            content = element.attributes.get('content', '')
            if content:
                return clean_text(content)
    
    # Try common author selectors
    author_selectors = [
        '.author-name',
        '.post-author',
        '.entry-author',
        '.by-author',
        '[rel="author"]'
    ]
    
    for selector in author_selectors:
        element = tree.css_first(selector)
        if element and element.text():
            return clean_text(element.text())
    
    return "Unknown"


def extract_categories_tags_from_content(content_element) -> tuple[List[str], List[str]]:
    """Extract categories and tags from content area only"""
    if not content_element:
        return [], []
    
    categories = []
    tags = []
    
    # Look for categories and tags within or near the content
    category_selectors = [
        '.post-categories a',
        '.entry-categories a', 
        '.category a',
        '[rel="category tag"]',
        '.categories a'
    ]
    
    tag_selectors = [
        '.post-tags a',
        '.entry-tags a',
        '.tags a',
        '[rel="tag"]',
        '.tag-links a'
    ]
    
    # Search in content element and its parent container
    search_elements = [content_element]
    if content_element.parent:
        search_elements.append(content_element.parent)
    
    for element in search_elements:
        # Categories
        for selector in category_selectors:
            for cat_link in element.css(selector):
                if cat_link.text():
                    text = clean_text(cat_link.text())
                    if text and len(text) < 50 and text not in categories:
                        categories.append(text)
        
        # Tags  
        for selector in tag_selectors:
            for tag_link in element.css(selector):
                if tag_link.text():
                    text = clean_text(tag_link.text())
                    if text and len(text) < 50 and text not in tags:
                        tags.append(text)
    
    return categories[:5], tags[:10]


def extract_links_from_content(content_element, base_url: str) -> Dict[str, List[Dict]]:
    """Extract links only from the content area"""
    if not content_element:
        return {'internal_links': [], 'external_links': [], 'relative_links': []}
    
    internal = []
    external = []
    relative = []
    
    base_domain = urlparse(base_url).netloc
    
    # Only get links from within the actual content
    for link in content_element.css('a[href]'):
        href = link.attributes.get('href', '').strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:')):
            continue
        
        text = link.text(strip=True) or '[No text]'
        
        # Skip if this looks like navigation/sidebar link
        if any(cls in link.attributes.get('class', '') for cls in ['nav', 'menu', 'sidebar', 'footer']):
            continue
        
        if href.startswith('http'):
            domain = urlparse(href).netloc
            link_data = {'url': href, 'text': text, 'domain': domain}
            if domain == base_domain:
                internal.append(link_data)
            else:
                external.append(link_data)
        else:
            relative.append({'url': href, 'text': text})
    
    return {
        'internal_links': internal,
        'external_links': external,
        'relative_links': relative
    }


def generate_slug(title: str) -> str:
    """Generate URL slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')[:50]


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


if __name__ == "__main__":
    # Test
    test_url = "https://www.parkfordofmahopac.com/blog/2025/march/25/shop-at-our-used-dealership-near-yorktown-heights.htm"
    result = extract_blog_post(test_url)
    if result:
        print(f"\nTitle: {result['title']}")
        print(f"Method: {result['method']}")
        print(f"Content length: {len(result['content'])}")
        print(f"Links: {len(result['hyperlinks']['relative_links'])} relative")
        print(f"Tags: {len(result['tags'])}, Categories: {len(result['categories'])}")
    else:
        print("Failed")