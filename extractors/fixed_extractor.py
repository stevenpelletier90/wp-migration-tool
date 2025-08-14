#!/usr/bin/env python3
"""Fixed XML generation for WordPress - no double encoding"""

import re
from datetime import datetime


def generate_wordpress_xml_fixed(posts):
    """Generate WordPress XML without double-encoding HTML"""
    if not posts:
        return ""
    
    # Create the XML structure manually to avoid auto-escaping
    xml_parts = []
    xml_parts.append('<?xml version="1.0" encoding="UTF-8" ?>')
    xml_parts.append('<rss version="2.0"')
    xml_parts.append(' xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"')
    xml_parts.append(' xmlns:content="http://purl.org/rss/1.0/modules/content/"')
    xml_parts.append(' xmlns:wfw="http://wellformedweb.org/CommentAPI/"')
    xml_parts.append(' xmlns:dc="http://purl.org/dc/elements/1.1/"')
    xml_parts.append(' xmlns:wp="http://wordpress.org/export/1.2/">')
    xml_parts.append('<channel>')
    
    # Channel info
    xml_parts.append('<title>Migrated Blog</title>')
    xml_parts.append('<link>https://newsite.com</link>')
    xml_parts.append('<description>Migrated content</description>')
    xml_parts.append(f'<pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>')
    xml_parts.append('<language>en-US</language>')
    xml_parts.append('<wp:wxr_version>1.2</wp:wxr_version>')
    xml_parts.append('<wp:base_site_url>https://newsite.com</wp:base_site_url>')
    xml_parts.append('<wp:base_blog_url>https://newsite.com</wp:base_blog_url>')
    
    # Add posts
    for post in posts:
        xml_parts.append('<item>')
        
        # Escape title and other text elements
        title = escape_xml_text(post['title'])
        url = escape_xml_text(post['url'])
        author = escape_xml_text(post['author'])
        slug = escape_xml_text(post['slug'])
        
        xml_parts.append(f'<title>{title}</title>')
        xml_parts.append(f'<link>{url}</link>')
        
        if post['date']:
            pub_date = post['date'].strftime("%a, %d %b %Y %H:%M:%S +0000")
            xml_parts.append(f'<pubDate>{pub_date}</pubDate>')
        
        xml_parts.append(f'<dc:creator>{author}</dc:creator>')
        xml_parts.append(f'<guid isPermaLink="false">{url}</guid>')
        xml_parts.append('<description />')
        
        # WordPress specific
        post_id = str(hash(post['url']) % 1000000)
        xml_parts.append(f'<wp:post_id>{post_id}</wp:post_id>')
        
        if post['date']:
            wp_date = post['date'].strftime("%Y-%m-%d %H:%M:%S")
            xml_parts.append(f'<wp:post_date>{wp_date}</wp:post_date>')
            xml_parts.append(f'<wp:post_date_gmt>{wp_date}</wp:post_date_gmt>')
        
        xml_parts.append(f'<wp:post_name>{slug}</wp:post_name>')
        xml_parts.append('<wp:status>publish</wp:status>')
        xml_parts.append('<wp:post_type>post</wp:post_type>')
        xml_parts.append('<wp:post_password />')
        
        # Content - wrap in CDATA without escaping
        clean_content = clean_content_for_cdata(post['content'])
        xml_parts.append(f'<content:encoded><![CDATA[{clean_content}]]></content:encoded>')
        
        # Categories
        for category in post.get('categories', []):
            cat_name = escape_xml_text(category)
            cat_slug = category.lower().replace(' ', '-').replace('&', 'and')
            cat_slug = re.sub(r'[^a-z0-9-]', '', cat_slug)
            xml_parts.append(f'<category domain="category" nicename="{cat_slug}">{cat_name}</category>')
        
        # Tags
        for tag in post.get('tags', []):
            tag_name = escape_xml_text(tag)
            tag_slug = tag.lower().replace(' ', '-').replace('&', 'and')
            tag_slug = re.sub(r'[^a-z0-9-]', '', tag_slug)
            xml_parts.append(f'<category domain="post_tag" nicename="{tag_slug}">{tag_name}</category>')
        
        xml_parts.append('<excerpt:encoded />')
        xml_parts.append('</item>')
    
    xml_parts.append('</channel>')
    xml_parts.append('</rss>')
    
    return '\n'.join(xml_parts)

def escape_xml_text(text):
    """Escape text for XML (not HTML)"""
    if not text:
        return ""
    
    # Only escape XML special characters
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    
    return text

def clean_content_for_cdata(content):
    """Clean content for CDATA section - minimal processing"""
    if not content:
        return ""
    
    # Only remove invalid XML characters that would break parsing
    valid_chars = []
    for char in content:
        code = ord(char)
        # Valid XML 1.0 characters
        if (code == 0x09 or code == 0x0A or code == 0x0D or 
            (0x20 <= code <= 0xD7FF) or (0xE000 <= code <= 0xFFFD) or 
            (0x10000 <= code <= 0x10FFFF)):
            valid_chars.append(char)
    
    content = ''.join(valid_chars)
    
    # Make sure CDATA section doesn't contain ]]>
    content = content.replace(']]>', ']] >')
    
    return content

# Test the fixed version
if __name__ == "__main__":
    # Test with sample data
    sample_post = {
        'title': 'Test Post with HTML',
        'content': '<p>This is a <strong>test</strong> with <a href="http://example.com">links</a>.</p>',
        'url': 'http://test.com/post',
        'date': datetime.now(),
        'author': 'Test Author',
        'slug': 'test-post',
        'categories': ['Test Category'],
        'tags': ['test', 'html']
    }
    
    xml = generate_wordpress_xml_fixed([sample_post])
    print(xml[:500] + "...")