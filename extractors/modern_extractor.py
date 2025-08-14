#!/usr/bin/env python3
"""Modern content extraction using newspaper3k and trafilatura libraries"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import newspaper
import requests
from bs4 import BeautifulSoup, Tag
from newspaper import Article
from trafilatura import extract, extract_metadata, fetch_url


def extract_blog_post(url: str) -> Optional[Dict]:
    """
    Extract blog post content using modern libraries.
    
    Tries newspaper3k first, falls back to trafilatura if needed.
    This replaces the complex custom extraction logic.
    """
    print(f"Extracting: {url}")
    
    # Try newspaper3k first (better for full HTML)
    try:
        # Configure with better headers to avoid blocking
        config = newspaper.Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config.request_timeout = 10
        
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        # Also try to get the article's HTML content directly if available
        article_html = article.article_html if hasattr(article, 'article_html') else None
        
        if article.title and article.html:
            # Get HTML for tag/category extraction
            html_content = article.html
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to extract date from et_pb_title_meta_container if present
            meta_container = soup.select_one('.et_pb_title_meta_container')
            if meta_container and not article.publish_date:
                # Look for date patterns in the meta container
                meta_text = meta_container.get_text()
                # Common date patterns
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
                            article.publish_date = parser.parse(date_match.group(1))
                            break
                        except Exception:
                            pass
            
            # Extract tags and categories (including from et_pb_title_meta_container)
            tags, categories = extract_tags_and_categories(soup, url)
            
            # newspaper3k extracts clean content, use that for link analysis
            # This avoids navigation/sidebar links and focuses on actual article content
            content_soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find the main content area first
            content_area = None
            
            # Extended list of selectors for better compatibility
            selectors = [
                '.et_pb_module.et_pb_post_content',  # Specific Divi module selector
                '.et_pb_post_content_0_tb_body',  # Specific Divi TB body selector
                '.et_pb_post_content', '.et_pb_text_inner',  # Divi/Elegant Themes
                '.fl-darklinks',  # Florida/Beaver Builder dark links container
                '.entry-content', '.post-content', '.article-content', 
                'article .content', 'article', 'main article', 'main',
                'div[itemprop="articleBody"]', '.single-content', 
                '.blog-post-content', '.content-area', '#content'
            ]
            
            for selector in selectors:
                content_area = content_soup.select_one(selector)
                if content_area and len(content_area.get_text(strip=True)) > 100:
                    break
            
            # If still no content area, try to use article_html if available
            if not content_area and article_html:
                content_area = BeautifulSoup(article_html, 'html.parser')
            
            # Use content area if found, otherwise use the cleaned article HTML
            link_extraction_content = str(content_area) if content_area else html_content
            
            # Extract hyperlinks from content only
            hyperlinks = extract_hyperlinks_from_content(link_extraction_content, url)
            
            # Build clean HTML while preserving hyperlinks and images
            clean_html = ""
            
            # Don't add H1 - WordPress will use the title field
            
            # If we have the content area, extract and clean it
            if content_area:
                # Clone the content area to avoid modifying original
                content_copy = BeautifulSoup(str(content_area), 'html.parser')
                
                # Remove script and style tags
                for script in content_copy.find_all(['script', 'style', 'noscript']):
                    script.decompose()
                
                # Remove all attributes except essential ones for links and images
                for element in content_copy.find_all(True):
                    if hasattr(element, 'attrs') and getattr(element, 'attrs', None):
                        allowed_attrs = {}
                        if element.name == 'a' and 'href' in element.attrs:
                            allowed_attrs['href'] = element.attrs['href']
                        elif element.name == 'img':
                            if 'src' in element.attrs:
                                allowed_attrs['src'] = element.attrs['src']
                            if 'alt' in element.attrs:
                                allowed_attrs['alt'] = element.attrs['alt']
                        element.attrs.clear()
                        element.attrs.update(allowed_attrs)
                
                # Remove ALL spans and styling elements from entire content first
                for unwanted in content_copy.find_all(['span', 'font', 'b', 'i', 'u', 'center']):
                    if unwanted.name in ['b', 'i', 'u']:
                        # Convert to proper semantic tags
                        if unwanted.name == 'b':
                            unwanted.name = 'strong'
                        elif unwanted.name == 'i':
                            unwanted.name = 'em'
                        elif unwanted.name == 'u':
                            unwanted.unwrap()  # Remove underline
                    else:
                        unwanted.unwrap()  # Remove span, font, center

                # Convert divs and sections to paragraphs, preserve existing paragraphs
                for tag in content_copy.find_all(['div', 'section']):
                    # Only convert if it doesn't contain block elements
                    if not tag.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol']):
                        tag.name = 'p'
                
                # Get all content elements
                for elem in content_copy.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'blockquote', 'div']):
                    # Skip empty elements
                    if elem.get_text(strip=True):
                        # If it's a div with mixed content (headings and text), process it differently
                        if elem.name == 'div' and elem.find_all(['h2', 'h3', 'h4']):
                            # Process headings and text separately
                            for child in elem.children:
                                if hasattr(child, 'name'):
                                    if child.name in ['h2', 'h3', 'h4']:
                                        clean_html += str(child) + "\n\n"
                                    elif child.get_text(strip=True):
                                        # Wrap text content in paragraph
                                        if child.name not in ['p', 'ul', 'ol']:
                                            clean_html += f"<p>{child.get_text(strip=True)}</p>\n\n"
                                        else:
                                            clean_html += str(child) + "\n\n"
                                elif child.strip():  # Text node
                                    clean_html += f"<p>{child.strip()}</p>\n\n"
                        else:
                            # Clean up nested paragraphs and unwrap unnecessary spans
                            for nested_p in elem.find_all('p'):
                                if elem != nested_p:  # Don't unwrap the element itself
                                    nested_p.unwrap()
                            
                            # Spans already removed globally above
                            
                            # Add the cleaned element with links preserved
                            if elem.name == 'div':
                                # Convert remaining divs to paragraphs
                                elem.name = 'p'
                            
                            # Add extra newline for paragraph spacing
                            clean_html += str(elem) + "\n\n"
                
                # Add images separately at the end
                images = content_area.find_all('img', src=True)
                if images:
                    clean_html += "\n<!-- Images from original post -->\n"
                    for img in images:
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        if src and not any(tracker in src.lower() for tracker in ['analytics', 'pixel', 'tracking', 'doubleclick', 'google']):
                            clean_html += f'<img src="{src}" alt="{alt}" />\n'
            
            elif article.text:
                # Fallback: Try to get the page directly with requests to preserve links
                try:
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    direct_soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find content with various selectors
                    found_content = False
                    for selector in selectors:
                        direct_content = direct_soup.select_one(selector)
                        if direct_content and len(direct_content.get_text(strip=True)) > 100:
                            # Extract and clean this content
                            for script in direct_content.find_all(['script', 'style', 'noscript']):
                                script.decompose()
                            
                            # Process paragraphs and preserve links
                            for elem in direct_content.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol']):
                                if elem.get_text(strip=True):
                                    # Keep only essential attributes
                                    for tag in elem.find_all(True):
                                        if hasattr(tag, 'attrs'):
                                            if tag.name == 'a' and 'href' in tag.attrs:
                                                href = tag.attrs['href']
                                                tag.attrs.clear()
                                                tag.attrs['href'] = href
                                            elif tag.name != 'a':
                                                tag.attrs.clear()
                                    clean_html += str(elem) + "\n\n"  # Double newline for spacing
                            found_content = True
                            break
                    
                    if not found_content:
                        # Ultimate fallback: use plain text
                        paragraphs = article.text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if para:
                                clean_html += f"<p>{para}</p>\n\n"
                except Exception:
                    # If direct fetch fails, use plain text
                    paragraphs = article.text.split('\n\n')
                    for para in paragraphs:
                        para = para.strip()
                        if para:
                            clean_html += f"<p>{para}</p>\n\n"
            
            # Clean up extra whitespace and ensure proper spacing
            clean_html = clean_html.strip()
            
            # Wrap in a content div
            clean_html = f"<div class='post-content'>\n{clean_html}\n</div>"
            
            # Convert internal links to relative URLs in the clean content
            processed_content = convert_internal_links_to_relative(clean_html, url)
            
            # Extract slug from URL (same logic as before)
            slug = extract_slug_from_url(url)
            
            # Parse date - newspaper3k is good at this
            pub_date = article.publish_date
            if not pub_date:
                # Fallback to URL-based date extraction
                pub_date = extract_date_from_url(url)
            
            result = {
                'url': url,
                'title': clean_title(article.title),
                'content': processed_content,
                'text_content': article.text,
                'date': pub_date,
                'author': ', '.join(article.authors) if article.authors else 'Unknown',
                'slug': slug,
                'tags': tags,
                'categories': categories,
                'hyperlinks': hyperlinks,
                'method': 'newspaper3k'
            }
            
            print(f"  [newspaper3k] SUCCESS: {result['title'][:50]}...")
            return result
            
    except Exception as e:
        print(f"  [newspaper3k] FAILED: {e}")
    
    # Fallback to trafilatura
    try:
        # Try manual download with better headers if fetch_url fails
        downloaded = fetch_url(url)
        if not downloaded:
            # Try manual download with headers
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                downloaded = response.text
            except Exception as e:
                print(f"  [trafilatura] FAILED: Could not download - {e}")
                return None
            
        # Extract as XML to preserve links but avoid styling
        content = extract(downloaded, include_comments=False, include_tables=True, output_format='xml')
        metadata = extract_metadata(downloaded)
        
        if content and metadata and metadata.title:
            # Get original HTML for tag/category extraction
            soup = BeautifulSoup(downloaded, 'html.parser')
            tags, categories = extract_tags_and_categories(soup, url)
            
            # Convert XML content to clean HTML (no H1 - WordPress uses title field)
            clean_html = ""
            
            # Parse the XML content and convert to HTML
            if content:
                try:
                    # trafilatura XML output, parse and convert to HTML
                    content_soup = BeautifulSoup(content, 'xml')
                    # Extract paragraphs and preserve links
                    for p in content_soup.find_all('p'):
                        para_html = str(p).replace('<p>', '<p>').replace('</p>', '</p>')
                        clean_html += para_html + "\n\n"
                except Exception:
                    # Fallback to plain text paragraphs if XML parsing fails
                    paragraphs = content.split('\n\n') if isinstance(content, str) else []
                    for para in paragraphs:
                        para = para.strip()
                        if para:
                            clean_html += f"<p>{para}</p>\n\n"
            
            # Try to get images from content area
            content_area = None
            for selector in ['.entry-content', '.post-content', '.article-content', 'article', 'main']:
                content_area = soup.select_one(selector)
                if content_area:
                    break
            
            if content_area:
                images = content_area.find_all('img', src=True)
                if images:
                    clean_html += "\n<!-- Images from original post -->\n"
                    for img in images:
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        if src and not any(tracker in src.lower() for tracker in ['analytics', 'pixel', 'tracking', 'doubleclick']):
                            clean_html += f'<img src="{src}" alt="{alt}" />\n'
            
            # Wrap content in div for consistency
            wrapped_content = f"<div class='post-content'>\n{clean_html}\n</div>"
            
            # Extract hyperlinks before converting to relative
            hyperlinks = extract_hyperlinks_from_content(wrapped_content, url)
            
            # Convert internal links to relative URLs
            processed_content = convert_internal_links_to_relative(wrapped_content, url)
            
            slug = extract_slug_from_url(url)
            
            # Parse date from metadata or URL
            pub_date = None
            if metadata.date:
                try:
                    pub_date = datetime.fromisoformat(metadata.date)
                except ValueError:
                    pass
            
            if not pub_date:
                pub_date = extract_date_from_url(url)
            
            result = {
                'url': url,
                'title': clean_title(metadata.title),
                'content': processed_content,
                'text_content': content,
                'date': pub_date,
                'author': metadata.author or 'Unknown',
                'slug': slug,
                'tags': tags,
                'categories': categories,
                'hyperlinks': hyperlinks,
                'method': 'trafilatura'
            }
            
            print(f"  [trafilatura] SUCCESS: {result['title'][:50]}...")
            return result
            
    except Exception as e:
        print(f"  [trafilatura] FAILED: {e}")
    
    print("  [BOTH] FAILED: Could not extract content")
    return None


def extract_slug_from_url(url: str) -> str:
    """Extract slug from URL - simplified version"""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Remove file extension
        if path.endswith('.htm') or path.endswith('.html'):
            path = path.rsplit('.', 1)[0]
        
        # Get the last part as slug
        slug = path.split('/')[-1]
        
        # Clean up slug
        slug = re.sub(r'[^a-zA-Z0-9-]', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        return slug or 'post'
        
    except Exception:
        return 'post'


def extract_date_from_url(url: str) -> Optional[datetime]:
    """Extract date from URL structure like /2024/september/3/"""
    try:
        # Look for patterns like /YYYY/month/DD/
        date_match = re.search(r'/(\d{4})/(january|february|march|april|may|june|july|august|september|october|november|december)/(\d{1,2})/', url.lower())
        
        if date_match:
            year = int(date_match.group(1))
            month_name = date_match.group(2)
            day = int(date_match.group(3))
            
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            month = month_map.get(month_name, 1)
            return datetime(year, month, day)
            
    except Exception:
        pass
    
    return None


def clean_title(title: str) -> str:
    """Clean up title - simplified version"""
    if not title:
        return "Unknown Title"
    
    # Remove common dealer suffixes
    title = re.sub(r'\s*[-|]\s*(Fitzgerald|Cadillac|Annapolis).*$', '', title, flags=re.IGNORECASE)
    
    return title.strip()


def generate_wordpress_xml(posts: List[Dict]) -> str:
    """
    Generate WordPress WXR XML - simplified version.
    This replaces the complex WXR generation logic.
    """
    if not posts:
        return ""
    
    # Create root element
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:excerpt", "http://wordpress.org/export/1.2/excerpt/")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:wfw", "http://wellformedweb.org/CommentAPI/")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    rss.set("xmlns:wp", "http://wordpress.org/export/1.2/")
    
    channel = ET.SubElement(rss, "channel")
    
    # Channel info
    ET.SubElement(channel, "title").text = "Migrated Blog"
    ET.SubElement(channel, "link").text = "https://newsite.com"
    ET.SubElement(channel, "description").text = "Migrated content"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(channel, "language").text = "en-US"
    ET.SubElement(channel, "wp:wxr_version").text = "1.2"
    ET.SubElement(channel, "wp:base_site_url").text = "https://newsite.com"
    ET.SubElement(channel, "wp:base_blog_url").text = "https://newsite.com"
    
    # Add posts
    for post in posts:
        item = ET.SubElement(channel, "item")
        
        # Basic info
        ET.SubElement(item, "title").text = post['title']
        ET.SubElement(item, "link").text = post['url']
        ET.SubElement(item, "pubDate").text = post['date'].strftime("%a, %d %b %Y %H:%M:%S +0000") if post['date'] else ""
        ET.SubElement(item, "dc:creator").text = post['author']
        ET.SubElement(item, "guid", isPermaLink="false").text = post['url']
        ET.SubElement(item, "description")
        
        # WordPress specific
        ET.SubElement(item, "wp:post_id").text = str(hash(post['url']) % 1000000)
        ET.SubElement(item, "wp:post_date").text = post['date'].strftime("%Y-%m-%d %H:%M:%S") if post['date'] else ""
        ET.SubElement(item, "wp:post_date_gmt").text = post['date'].strftime("%Y-%m-%d %H:%M:%S") if post['date'] else ""
        ET.SubElement(item, "wp:post_name").text = post['slug']
        ET.SubElement(item, "wp:status").text = "publish"
        ET.SubElement(item, "wp:post_type").text = "post"
        ET.SubElement(item, "wp:post_password").text = ""
        
        # Content with proper XML cleaning and CDATA wrapping
        content_elem = ET.SubElement(item, "content:encoded")
        cleaned_content = clean_xml_content(post['content'])
        content_elem.text = cleaned_content
        
        # Tags and Categories
        for tag in post.get('tags', []):
            tag_elem = ET.SubElement(item, "category", {"domain": "post_tag", "nicename": tag.lower().replace(" ", "-")})
            tag_elem.text = tag
            
        for category in post.get('categories', []):
            cat_elem = ET.SubElement(item, "category", {"domain": "category", "nicename": category.lower().replace(" ", "-")}) 
            cat_elem.text = category
        
        # Excerpt
        excerpt_elem = ET.SubElement(item, "excerpt:encoded")
        excerpt_elem.text = ""
    
    # Convert to string
    xml_str = ET.tostring(rss, encoding='unicode')
    
    # Add CDATA wrapping to content:encoded elements
    xml_str = add_cdata_to_content(xml_str)
    
    # Add XML declaration
    return f'<?xml version="1.0" encoding="UTF-8" ?>\n{xml_str}'

def add_cdata_to_content(xml_str):
    """Add CDATA wrapping to content:encoded elements"""
    # Pattern to find content:encoded elements
    pattern = r'<content:encoded>(.*?)</content:encoded>'
    
    def wrap_in_cdata(match):
        content = match.group(1)
        # Only wrap if not already wrapped
        if not content.startswith('<![CDATA['):
            return f'<content:encoded><![CDATA[{content}]]></content:encoded>'
        return match.group(0)
    
    # Replace all content:encoded with CDATA wrapped version
    xml_str = re.sub(pattern, wrap_in_cdata, xml_str, flags=re.DOTALL)
    
    return xml_str


def clean_xml_content(content):
    """Clean content for XML - removes invalid characters and fixes empty hrefs"""
    if not content:
        return ""
    
    # First, fix empty href attributes
    content = fix_empty_hrefs(content)
    
    # Remove duplicate sections if present
    content = remove_duplicate_sections(content)
    
    # Remove invalid XML characters (especially char 20 which is a control character)
    # Keep only valid XML 1.0 characters
    valid_chars = []
    for char in content:
        code = ord(char)
        # Valid XML 1.0 characters: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
        if (code == 0x09 or code == 0x0A or code == 0x0D or 
            (0x20 <= code <= 0xD7FF) or (0xE000 <= code <= 0xFFFD) or 
            (0x10000 <= code <= 0x10FFFF)):
            valid_chars.append(char)
    
    return ''.join(valid_chars)

def fix_empty_hrefs(content):
    """Fix empty href attributes by setting them to /"""
    if not content:
        return content
    
    # Fix empty hrefs - replace href="" with href="/"
    content = re.sub(r'href=""', 'href="/"', content)
    
    # Also fix hrefs that might have just whitespace
    content = re.sub(r'href="\s+"', 'href="/"', content)
    
    return content

def remove_duplicate_sections(content):
    """Remove duplicate content sections"""
    if not content:
        return content
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Track seen content to detect duplicates
    seen_content = set()
    elements_to_remove = []
    
    # Check for duplicate lists
    for list_elem in soup.find_all(['ul', 'ol']):
        list_html = str(list_elem)
        if list_html in seen_content:
            elements_to_remove.append(list_elem)
        else:
            seen_content.add(list_html)
    
    # Check for duplicate paragraphs in sequence
    for p in soup.find_all('p'):
        p_text = p.get_text(strip=True)
        if len(p_text) > 50:  # Only check substantial paragraphs
            if p_text in seen_content:
                # Check if this is truly a duplicate (not just similar text)
                for seen in seen_content:
                    if p_text == seen:
                        elements_to_remove.append(p)
                        break
            else:
                seen_content.add(p_text)
    
    # Remove duplicates
    for elem in elements_to_remove:
        elem.decompose()
    
    return str(soup)

def extract_tags_and_categories(soup, url):
    """Extract tags and categories from blog content"""
    tags = []
    categories = []
    
    # Look for common tag/category patterns
    # Check for tag sections
    for selector in ['.tags', '.tag-list', '.post-tags', '[class*="tag"]', '.entry-tags']:
        try:
            tag_section = soup.select_one(selector)
            if tag_section:
                tag_links = tag_section.find_all('a', href=True)
                for link in tag_links:
                    tag_text = link.get_text(strip=True)
                    if tag_text and len(tag_text) < 50:  # Reasonable tag length
                        tags.append(tag_text)
                if tags:
                    break
        except Exception:
            continue
    
    # Check for category sections - expanded selectors including Divi meta container
    for selector in ['.et_pb_title_meta_container a', '.categories', '.category-list', '.post-categories', '[class*="categor"]', 
                     '.entry-categories', '.post-meta a[rel="category"]', 'a[rel="category tag"]',
                     '.entry-meta a[href*="/category/"]', 'span.cat-links a']:
        try:
            if 'a[' in selector:  # Direct link selector
                cat_links = soup.select(selector)
            else:
                cat_section = soup.select_one(selector)
                if cat_section:
                    cat_links = cat_section.find_all('a', href=True)
                else:
                    cat_links = []
                    
            for link in cat_links:
                cat_text = link.get_text(strip=True)
                if cat_text and len(cat_text) < 50:  # Reasonable category length
                    categories.append(cat_text)
            if categories:
                break
        except Exception:
            continue
    
    # Additional check: Look for links with /category/ in the URL
    if not categories:
        category_links = soup.find_all('a', href=lambda x: x and '/category/' in x.lower())
        for link in category_links[:3]:  # Limit to first 3 to avoid navigation links
            cat_text = link.get_text(strip=True)
            if cat_text and len(cat_text) < 50 and cat_text not in categories:
                categories.append(cat_text)
    
    # Fallback: extract from URL structure or meta tags
    if not categories:
        # Try to extract from URL path
        path_parts = url.split('/')
        for part in path_parts:
            if part in ['news', 'blog', 'articles', 'posts', 'automotive', 'luxury', 'vehicles', 'personal-injury']:
                categories.append(part.replace('-', ' ').title())
                break
    
    return tags, categories


def extract_hyperlinks_from_content(content: str, source_url: str) -> Dict:
    """Extract and categorize all hyperlinks from post content"""
    if not content:
        return {'internal_links': [], 'external_links': [], 'relative_links': []}
    
    soup = BeautifulSoup(content, 'html.parser')
    source_domain = urlparse(source_url).netloc.lower()
    
    internal_links = []
    external_links = []
    relative_links = []
    
    # Find all anchor tags with href attributes
    for link in soup.find_all('a', href=True):
        if not isinstance(link, Tag):
            continue
        href_raw = link.get('href', '')
        # Handle AttributeValueList case
        if isinstance(href_raw, list):
            href = href_raw[0] if href_raw else ''
        else:
            href = str(href_raw) if href_raw else ''
        href = href.strip()
        link_text = link.get_text(strip=True)
        
        # Skip empty or fragment-only links
        if not href or href.startswith('#'):
            continue
            
        try:
            parsed = urlparse(href)
            
            if not parsed.netloc:  # Relative URL
                relative_links.append({
                    'url': href,
                    'text': link_text,
                    'full_tag': str(link)
                })
            elif parsed.netloc.lower() == source_domain:  # Internal link
                relative_url = parsed.path + (f'?{parsed.query}' if parsed.query else '') + (f'#{parsed.fragment}' if parsed.fragment else '')
                internal_links.append({
                    'url': href,  # Keep original full URL
                    'text': link_text,
                    'full_tag': str(link),
                    'relative_url': relative_url,
                    'original_full_url': href  # Store original for preview
                })
            else:  # External link
                external_links.append({
                    'url': href,
                    'text': link_text,
                    'full_tag': str(link),
                    'domain': parsed.netloc.lower()
                })
                
        except Exception:
            # If URL parsing fails, treat as relative
            relative_links.append({
                'url': href,
                'text': link_text,
                'full_tag': str(link)
            })
    
    return {
        'internal_links': internal_links,
        'external_links': external_links, 
        'relative_links': relative_links
    }


def convert_internal_links_to_relative(content: str, source_url: str) -> str:
    """Convert internal links in content to relative URLs"""
    if not content:
        return content
        
    soup = BeautifulSoup(content, 'html.parser')
    source_domain = urlparse(source_url).netloc.lower()
    
    # Find and update internal links
    for link in soup.find_all('a', href=True):
        if not isinstance(link, Tag):
            continue
        href_raw = link.get('href', '')
        # Handle AttributeValueList case
        if isinstance(href_raw, list):
            href = href_raw[0] if href_raw else ''
        else:
            href = str(href_raw) if href_raw else ''
        try:
            parsed = urlparse(href)
            if parsed.netloc.lower() == source_domain:
                # Convert to relative URL
                relative_url = parsed.path
                if parsed.query:
                    relative_url += f'?{parsed.query}'
                if parsed.fragment:
                    relative_url += f'#{parsed.fragment}'
                link['href'] = relative_url
        except Exception:
            continue  # Skip malformed URLs
    
    return str(soup)


def main():
    """Extract URLs from config/urls.txt using modern extractor"""
    import os
    
    print("MODERN EXTRACTOR")
    print("=" * 50)
    
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
        return False
    
    print(f"Found {len(urls)} URLs to process\n")
    
    posts = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Extracting: {url}")
        post = extract_blog_post(url)
        if post:
            posts.append(post)
            print(f"  SUCCESS: {post['title'][:60]}...")
        else:
            print("  FAILED: Could not extract content")
    
    print(f"\nExtracted {len(posts)}/{len(urls)} posts successfully!")
    
    if posts:
        xml_content = generate_wordpress_xml(posts)
        output_file = os.path.join(os.path.dirname(__file__), "..", "output", "modern_export.xml")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"Generated {output_file}")
    
    return len(posts) > 0


if __name__ == "__main__":
    main()