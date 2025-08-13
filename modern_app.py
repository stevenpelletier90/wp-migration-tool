#!/usr/bin/env python3
"""Modern WordPress Migration Tool - Clean Flask Backend"""

import re
import uuid
from datetime import datetime
from typing import Dict

from flask import Flask, jsonify, render_template, request, session

from modern_extractor import extract_blog_post, generate_wordpress_xml

app = Flask(__name__)
app.secret_key = 'modern-migration-tool-2025'

# In-memory storage for the session (simple and clean)
app_data: Dict[str, Dict] = {}

def get_session_data() -> Dict:
    """Get or create session data"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    if session_id not in app_data:
        app_data[session_id] = {
            'urls': [],
            'posts': [],
            'status': 'ready',
            'last_updated': datetime.now(),
            'has_modifications': False  # Track if find/replace was used
        }
    
    return app_data[session_id]

@app.route('/')
def home():
    """Main interface - clean and simple"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok'}

@app.route('/api/urls', methods=['POST'])
def add_urls():
    """Add URLs to session - simple and clean"""
    data = get_session_data()
    
    # Get URLs from textarea
    url_text = request.form.get('url-input', '').strip()
    if not url_text:
        return '<div class="alert alert-warning">Please enter some URLs</div>', 400
    
    # Parse URLs
    urls = [url.strip() for url in url_text.split('\n') if url.strip()]
    if not urls:
        return '<div class="alert alert-warning">No valid URLs found</div>', 400
    
    # Store URLs
    data['urls'] = urls
    data['status'] = 'urls_added'
    
    # Return success message and show the URL management interface
    url_list_html = ''.join([
        f'''
        <div class="d-flex align-items-center border-bottom py-2">
            <div class="me-2">
                <input type="checkbox" class="form-check-input url-checkbox" id="select-{i}" value="{i}" onchange="updateBulkDeleteButton()">
            </div>
            <div class="flex-grow-1 me-3">
                <input type="text" class="form-control font-monospace" value="{url}" 
                       id="url-{i}" onchange="updateUrl({i}, this.value)"
                       style="font-size: 0.85rem;">
            </div>
            <button class="btn btn-outline-danger btn-sm" 
                    hx-post="/api/urls/delete" 
                    hx-vals='{{"index": {i}}}'
                    hx-target="#url-manager"
                    hx-swap="innerHTML">
                Delete
            </button>
        </div>
        '''
        for i, url in enumerate(urls)
    ])
    
    return f'''
    <div id="url-manager">
        <div class="alert alert-success">
            <strong>Success!</strong> Added {len(urls)} URLs
        </div>
        
        <div class="card mt-3">
            <div class="card-header d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <input type="checkbox" class="form-check-input me-2" id="select-all" onchange="toggleAllUrls()">
                    <h6 class="mb-0">Your URLs ({len(urls)})</h6>
                </div>
                <div>
                    <button class="btn btn-outline-warning btn-sm me-2" 
                            id="bulk-delete-btn" 
                            onclick="bulkDeleteUrls()" 
                            style="display: none;">
                        Delete Selected
                    </button>
                    <button class="btn btn-outline-primary btn-sm me-2" 
                            onclick="addNewUrl()">
                        Add Another
                    </button>
                    <button class="btn btn-outline-danger btn-sm" 
                            hx-post="/api/urls/clear"
                            hx-target="#url-manager"
                            hx-swap="innerHTML"
                            hx-confirm="Clear all URLs?">
                        Clear All
                    </button>
                </div>
            </div>
            <div class="card-body">
                {url_list_html}
            </div>
        </div>
    </div>
    
    <script>
        function updateUrl(index, newUrl) {{
            // Update URL via AJAX
            fetch('/api/urls/update', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{index: index, url: newUrl}})
            }});
        }}
        
        function addNewUrl() {{
            const newUrl = prompt('Enter new URL:');
            if (newUrl) {{
                fetch('/api/urls/add', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{url: newUrl}})
                }}).then(() => {{
                    // Refresh the URL list
                    htmx.ajax('GET', '/api/urls/list', '#url-manager');
                }});
            }}
        }}
        
        function toggleAllUrls() {{
            const selectAll = document.getElementById('select-all');
            const checkboxes = document.querySelectorAll('.url-checkbox');
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
            updateBulkDeleteButton();
        }}
        
        function updateBulkDeleteButton() {{
            const checkboxes = document.querySelectorAll('.url-checkbox:checked');
            const bulkBtn = document.getElementById('bulk-delete-btn');
            if (checkboxes.length > 0) {{
                bulkBtn.style.display = 'inline-block';
                bulkBtn.textContent = `Delete Selected (${{checkboxes.length}})`;
            }} else {{
                bulkBtn.style.display = 'none';
            }}
        }}
        
        function bulkDeleteUrls() {{
            const checkboxes = document.querySelectorAll('.url-checkbox:checked');
            const indices = Array.from(checkboxes).map(cb => parseInt(cb.value));
            
            if (indices.length === 0) return;
            
            if (confirm(`Delete ${{indices.length}} selected URLs?`)) {{
                fetch('/api/urls/bulk-delete', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{indices: indices}})
                }}).then(() => {{
                    htmx.ajax('GET', '/api/urls/list', '#url-manager');
                }});
            }}
        }}
    </script>
    '''

@app.route('/api/urls/delete', methods=['POST'])
def delete_url():
    """Delete a specific URL by index"""
    data = get_session_data()
    index = int(request.form.get('index', 0))
    
    if 0 <= index < len(data['urls']):
        data['urls'].pop(index)
        return render_url_list(data['urls'])
    
    return '<div class="alert alert-danger">Invalid URL index</div>', 400

@app.route('/api/urls/clear', methods=['POST'])
def clear_urls():
    """Clear all URLs"""
    data = get_session_data()
    data['urls'] = []
    return '<div class="alert alert-info">All URLs cleared</div>'

@app.route('/api/urls/update', methods=['POST'])
def update_url():
    """Update a specific URL"""
    data = get_session_data()
    req_data = request.get_json()
    index = req_data.get('index', 0)
    new_url = req_data.get('url', '').strip()
    
    if 0 <= index < len(data['urls']) and new_url:
        data['urls'][index] = new_url
        return {'success': True}
    
    return {'success': False}, 400

@app.route('/api/urls/add', methods=['POST'])
def add_single_url():
    """Add a single new URL"""
    data = get_session_data()
    req_data = request.get_json()
    new_url = req_data.get('url', '').strip()
    
    if new_url:
        data['urls'].append(new_url)
        return {'success': True}
    
    return {'success': False}, 400

@app.route('/api/urls/bulk-delete', methods=['POST'])
def bulk_delete_urls():
    """Delete multiple URLs by indices"""
    data = get_session_data()
    req_data = request.get_json()
    indices = req_data.get('indices', [])
    
    if not indices:
        return {'success': False, 'error': 'No indices provided'}, 400
    
    # Sort indices in reverse order to avoid index shifting issues
    indices = sorted(set(indices), reverse=True)
    
    # Remove URLs by index
    for index in indices:
        if 0 <= index < len(data['urls']):
            data['urls'].pop(index)
    
    return {'success': True, 'deleted_count': len(indices)}

@app.route('/api/urls/list', methods=['GET'])
def list_urls():
    """Get current URL list"""
    data = get_session_data()
    return render_url_list(data['urls'])

def render_posts_with_details(results, posts):
    """Helper function to render posts with expandable details"""
    if not results:
        return '<div class="alert alert-info">No posts extracted</div>'
    
    html_parts = []
    
    for i, r in enumerate(results):
        # Calculate link counts
        hyperlinks = r.get("hyperlinks", {})
        internal_count = len(hyperlinks.get("internal_links", []))
        external_count = len(hyperlinks.get("external_links", []))
        relative_count = len(hyperlinks.get("relative_links", []))
        total_links = internal_count + external_count + relative_count
        
        # Build accordion item
        html_parts.append(f'''
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" 
                        data-bs-toggle="collapse" data-bs-target="#post-{i}" 
                        aria-expanded="false">
                    <div class="d-flex justify-content-between align-items-center w-100 me-3">
                        <strong>{r["title"][:80]}{"..." if len(r["title"]) > 80 else ""}</strong>
                        <small class="text-muted ms-2">
                            📁 {len(r.get("categories", []))} categories | 
                            🔗 {total_links} links
                        </small>
                    </div>
                </button>
            </h2>
            <div id="post-{i}" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <h6 class="text-muted">📁 Categories ({len(r.get("categories", []))})</h6>
                            <div class="mb-3">
                                {", ".join(r.get("categories", [])) if r.get("categories") else "<em>No categories found</em>"}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-muted">🏷️ Tags ({len(r.get("tags", []))})</h6>
                            <div class="mb-3">
                                {", ".join(r.get("tags", [])) if r.get("tags") else "<em>No tags found</em>"}
                            </div>
                        </div>
                    </div>
                    
                    <div class="d-flex gap-2 mb-3">
                        <a href="{r["url"]}" target="_blank" class="btn btn-outline-info btn-sm">
                            🔗 View Source Post
                        </a>
                    </div>
                    
                    {render_link_section("Internal Links → Relative", "🏠", hyperlinks.get("internal_links", []), "internal", i)}
                    {render_link_section("External Links", "🌐", hyperlinks.get("external_links", []), "external", i)}
                    {render_link_section("Relative Links", "📂", hyperlinks.get("relative_links", []), "relative", i)}
                </div>
            </div>
        </div>
        ''')
    
    return ''.join(html_parts)

def render_link_section(title, icon, links, link_type, post_index):
    """Helper function to render a section of links"""
    if not links:
        return ""
    
    html_parts = [f'''
    <div class="mb-3">
        <h6 class="text-muted">{icon} {title} ({len(links)})</h6>
    ''']
    
    if link_type == "internal":
        html_parts.append('<small class="text-muted mb-2 d-block">These have been auto-converted to relative URLs for WordPress</small>')
    
    html_parts.append('<div class="list-group list-group-flush">')
    
    for link in links:
        url = link["url"]
        
        html_parts.append('''
        <div class="list-group-item d-flex justify-content-between align-items-center py-2">
            <div class="flex-grow-1">
        ''')
        
        if link_type == "internal":
            html_parts.append(f'''
                <code class="text-success">{link.get("relative_url", "")}</code>
                <br><small class="text-muted">was: {url}</small>
            ''')
        elif link_type == "external":
            html_parts.append(f'''
                <code>{url}</code>
                <br><small class="text-muted">to: {link.get("domain", "")}</small>
            ''')
        else:  # relative
            html_parts.append(f'<code>{url}</code>')
        
        html_parts.append('''
            </div>
        </div>
        ''')
    
    html_parts.append('</div></div>')
    return ''.join(html_parts)

def render_url_list(urls):
    """Helper function to render URL list"""
    if not urls:
        return '<div class="alert alert-info">No URLs added yet</div>'
    
    url_list_html = ''.join([
        f'''
        <div class="d-flex align-items-center border-bottom py-2">
            <div class="me-2">
                <input type="checkbox" class="form-check-input url-checkbox" id="select-{i}" value="{i}" onchange="updateBulkDeleteButton()">
            </div>
            <div class="flex-grow-1 me-3">
                <input type="text" class="form-control font-monospace" value="{url}" 
                       id="url-{i}" onchange="updateUrl({i}, this.value)"
                       style="font-size: 0.85rem;">
            </div>
            <button class="btn btn-outline-danger btn-sm" 
                    hx-post="/api/urls/delete" 
                    hx-vals='{{"index": {i}}}'
                    hx-target="#url-manager"
                    hx-swap="innerHTML">
                Delete
            </button>
        </div>
        '''
        for i, url in enumerate(urls)
    ])
    
    return f'''
    <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Your URLs ({len(urls)})</h6>
            <div>
                <button class="btn btn-outline-primary btn-sm me-2" 
                        onclick="addNewUrl()">
                    Add Another
                </button>
                <button class="btn btn-outline-danger btn-sm" 
                        hx-post="/api/urls/clear"
                        hx-target="#url-manager"
                        hx-swap="innerHTML"
                        hx-confirm="Clear all URLs?">
                    Clear All
                </button>
            </div>
        </div>
        <div class="card-body">
            {url_list_html}
        </div>
    </div>
    '''

@app.route('/api/migrate', methods=['POST'])
def migrate():
    """Extract content using modern libraries - simple and powerful"""
    data = get_session_data()
    
    if not data.get('urls'):
        return '<div class="alert alert-danger">No URLs to process</div>', 400
    
    data['status'] = 'processing'
    posts = []
    results = []
    
    # Use modern extractor
    for url in data['urls']:
        try:
            post = extract_blog_post(url)
            if post:
                posts.append(post)
                results.append({
                    'url': url,
                    'status': 'success', 
                    'title': post['title'],
                    'method': post['method'],
                    'categories': post.get('categories', []),
                    'tags': post.get('tags', []),
                    'hyperlinks': post.get('hyperlinks', {'internal_links': [], 'external_links': [], 'relative_links': []})
                })
            else:
                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': 'Could not extract content'
                })
        except Exception as e:
            results.append({
                'url': url,
                'status': 'failed',
                'error': str(e)
            })
    
    # Store results
    data['posts'] = posts
    data['original_posts'] = [post.copy() for post in posts]  # Store original copies
    data['results'] = results
    data['status'] = 'completed' if posts else 'failed'
    data['has_modifications'] = False  # Track if any modifications were made
    
    # Generate response
    successful = len(posts)
    failed = len(data['urls']) - successful
    
    if successful > 0:
        return f'''
        <div class="alert alert-success">
            <strong>Migration Complete!</strong><br>
            Successfully extracted: {successful} posts<br>
            {'Failed: ' + str(failed) + ' posts<br>' if failed > 0 else ''}
        </div>
        <div class="mt-3">
            <h6>Extracted Posts:</h6>
            <div class="accordion" id="posts-accordion">
                {render_posts_with_details([r for r in results if r["status"] == "success"], data["posts"])}
            </div>
        </div>
        <script>
            // Update download section to show original vs modified status
            fetch('/api/status')
                .then(response => response.json())
                .then(status => {{
                    const isModified = {str(data.get('has_modifications', False)).lower()};
                    
                    let downloadHTML = '';
                    
                    if (isModified) {{
                        // Show both options when modifications exist
                        downloadHTML = `
                            <div class="row g-2 mb-3">
                                <div class="col-md-6">
                                    <a href="/api/download" class="btn btn-success btn-lg w-100" download="wordpress_import.xml">
                                        <i class="bi bi-arrow-repeat"></i> Download Modified XML
                                    </a>
                                </div>
                                <div class="col-md-6">
                                    <a href="/api/download-original" class="btn btn-outline-secondary btn-lg w-100" download="wordpress_import_original.xml">
                                        <i class="bi bi-download"></i> Download Original XML
                                    </a>
                                </div>
                            </div>
                            <div class="alert alert-success py-2">
                                <small><strong>Modified version includes your find/replace changes</strong></small>
                            </div>
                        `;
                    }} else {{
                        // Show single option when no modifications
                        downloadHTML = `
                            <div class="d-grid">
                                <a href="/api/download" class="btn btn-success btn-lg" download="wordpress_import.xml">
                                    <i class="bi bi-download"></i> Download WordPress XML
                                </a>
                            </div>
                            <div class="mt-3">
                                <div class="alert alert-info py-2">
                                    <small><strong>Original extracted content</strong></small>
                                </div>
                            </div>
                        `;
                    }}
                    
                    downloadHTML += `
                        <small class="text-muted">
                            Ready to import into WordPress: Tools → Import → WordPress
                        </small>
                    `;
                    
                    document.getElementById('download-section').innerHTML = downloadHTML;
                }});
        </script>
        '''
    else:
        return '''
        <div class="alert alert-danger">
            <strong>Migration Failed!</strong><br>
            No posts could be extracted. Check your URLs and try again.
        </div>
        '''

@app.route('/api/download')
def download():
    """Generate and serve WordPress XML (current version)"""
    data = get_session_data()
    
    if not data.get('posts'):
        return jsonify({'error': 'No posts to export'}), 400
    
    # Generate XML using modern extractor
    xml_content = generate_wordpress_xml(data['posts'])
    
    # Return as downloadable file
    from flask import Response
    return Response(
        xml_content,
        mimetype='application/xml',
        headers={
            'Content-Disposition': 'attachment; filename=wordpress_import.xml',
            'Content-Type': 'application/xml; charset=utf-8'
        }
    )

@app.route('/api/download-original')
def download_original():
    """Generate and serve original WordPress XML (before modifications)"""
    data = get_session_data()
    
    if not data.get('posts'):
        return jsonify({'error': 'No posts to export'}), 400
    
    # Get original posts (before any modifications)
    original_posts = data.get('original_posts', data['posts'])
    
    # Generate XML using modern extractor
    xml_content = generate_wordpress_xml(original_posts)
    
    # Return as downloadable file
    from flask import Response
    return Response(
        xml_content,
        mimetype='application/xml',
        headers={
            'Content-Disposition': 'attachment; filename=wordpress_import_original.xml',
            'Content-Type': 'application/xml; charset=utf-8'
        }
    )

@app.route('/api/status')
def status():
    """Get current session status"""
    data = get_session_data()
    return jsonify({
        'status': data.get('status', 'ready'),
        'url_count': len(data.get('urls', [])),
        'post_count': len(data.get('posts', [])),
        'last_updated': data['last_updated'].isoformat() if data.get('last_updated') else None
    })

@app.route('/api/find-replace/preview', methods=['POST'])
def preview_replace():
    """Preview find/replace changes using difflib for git-style diffs"""
    data = get_session_data()
    req_data = request.get_json()
    
    search_pattern = req_data.get('search_pattern', '').strip()
    replace_with = req_data.get('replace_with', '').strip()
    use_regex = req_data.get('use_regex', False)
    post_index = req_data.get('post_index')
    
    if not search_pattern or not replace_with:
        return jsonify({'success': False, 'error': 'Both search and replace fields are required'})
    
    if not data.get('posts'):
        return jsonify({'success': False, 'error': 'No posts available for find/replace'})
    
    try:
        changes_preview = []
        total_matches = 0
        
        # If post_index is provided, only process that specific post
        if post_index is not None:
            if post_index >= len(data['posts']):
                return jsonify({'success': False, 'error': 'Invalid post index'})
            posts_to_process = [(post_index, data['posts'][post_index])]
        else:
            # Process all posts (global search)
            posts_to_process = enumerate(data['posts'])
        
        for i, post in posts_to_process:
            original_content = post.get('content', '')
            if not original_content:
                continue
                
            # Find <a> elements that contain the search pattern
            from bs4 import BeautifulSoup, Tag
            soup = BeautifulSoup(original_content, 'html.parser')
            matching_elements = []
            
            for link in soup.find_all('a', href=True):
                if not isinstance(link, Tag):
                    continue
                href = link.get('href', '')
                if isinstance(href, list):
                    href = href[0] if href else ''
                href = str(href) if href else ''
                
                if use_regex:
                    try:
                        if re.search(search_pattern, href):
                            # Show what the href will become
                            new_href = re.sub(search_pattern, replace_with, href)
                            matching_elements.append({
                                'original_tag': str(link),
                                'original_href': href,
                                'new_href': new_href
                            })
                    except re.error as e:
                        return jsonify({'success': False, 'error': f'Invalid regex pattern: {e}'})
                else:
                    if search_pattern in href:
                        new_href = href.replace(search_pattern, replace_with)
                        matching_elements.append({
                            'original_tag': str(link),
                            'original_href': href,
                            'new_href': new_href
                        })
            
            if matching_elements:
                total_matches += len(matching_elements)
                changes_preview.append({
                    'post_title': post['title'],
                    'post_url': post['url'],
                    'matches': len(matching_elements),
                    'elements': matching_elements
                })
        
        if total_matches == 0:
            return jsonify({
                'success': False, 
                'error': f'No matches found for "{search_pattern}"'
            })
        
        # Show actual <a> elements and what they'll become
        diff_html = f'<div class="alert alert-info">Found {total_matches} matching links across {len(changes_preview)} posts</div>'
        
        diff_html += '<div class="mb-3">'
        diff_html += '<h6>Link Changes Preview:</h6>'
        
        for i, change in enumerate(changes_preview):
            diff_html += '<div class="card mb-3">'
            diff_html += '<div class="card-header d-flex justify-content-between">'
            diff_html += f'<span>📄 {change["post_title"]} ({change["matches"]} links)</span>'
            diff_html += f'<a href="{change["post_url"]}" target="_blank" class="btn btn-outline-info btn-sm">🔗 Source</a>'
            diff_html += '</div>'
            diff_html += '<div class="card-body">'
            
            for idx, element in enumerate(change["elements"]):
                element_id = f'element-{i}-{idx}'
                diff_html += '<div class="mb-3 p-3 border rounded">'
                
                # Checkbox for selective replacement
                diff_html += '<div class="form-check mb-2">'
                diff_html += f'<input class="form-check-input replacement-checkbox" type="checkbox" id="{element_id}" value="{element_id}" checked>'
                diff_html += f'<label class="form-check-label fw-bold" for="{element_id}">Replace this link</label>'
                diff_html += '</div>'
                
                # For relative links, show them with full domain for context in preview
                original_tag_display = element["original_tag"]
                if element["original_href"].startswith('/'):
                    # Replace relative href with full URL for better context in preview
                    full_url = f'https://www.fitzgeraldcadillacannapolis.com{element["original_href"]}'
                    original_tag_display = original_tag_display.replace(f'href="{element["original_href"]}"', f'href="{full_url}"')
                
                diff_html += '<div class="mb-2"><strong>Link in content:</strong></div>'
                diff_html += f'<code class="d-block mb-2 p-2 bg-light">{original_tag_display}</code>'
                diff_html += '<div class="row">'
                diff_html += '<div class="col-md-6">'
                diff_html += '<span class="badge bg-danger mb-1">Before</span>'
                diff_html += f'<br><code>{element["original_href"]}</code>'
                diff_html += '</div>'
                diff_html += '<div class="col-md-6">'
                diff_html += '<span class="badge bg-success mb-1">After</span>'
                diff_html += f'<br><code>{element["new_href"]}</code>'
                diff_html += '</div>'
                diff_html += '</div>'
                diff_html += '</div>'
            
            diff_html += '</div></div>'
        
        diff_html += '</div>'
        
        # Add select all/none controls
        diff_html += '''
        <div class="d-flex gap-2 mb-3">
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="selectAllReplacements()">
                Select All
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="selectNoneReplacements()">
                Select None
            </button>
        </div>
        <script>
            function selectAllReplacements() {
                document.querySelectorAll('.replacement-checkbox').forEach(cb => cb.checked = true);
            }
            function selectNoneReplacements() {
                document.querySelectorAll('.replacement-checkbox').forEach(cb => cb.checked = false);
            }
        </script>
        '''
        
        # Store preview data in session for selective application
        data['preview_data'] = changes_preview
        data['preview_search'] = search_pattern
        data['preview_replace'] = replace_with
        data['preview_regex'] = use_regex
        
        return jsonify({
            'success': True,
            'diff_html': diff_html,
            'total_matches': total_matches,
            'affected_posts': len(changes_preview)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing find/replace: {str(e)}'})

@app.route('/api/find-replace/apply', methods=['POST'])
def apply_replace():
    """Apply selective find/replace changes to post data in memory"""
    data = get_session_data()
    req_data = request.get_json()
    
    selected_elements = req_data.get('selected_elements', [])
    
    if not selected_elements:
        return jsonify({'success': False, 'error': 'No elements selected for replacement'})
    
    if not data.get('preview_data'):
        return jsonify({'success': False, 'error': 'No preview data available. Please run preview first.'})
    
    try:
        total_changes = 0
        use_regex = data['preview_regex']
        
        # Build a set of selected element IDs for quick lookup
        selected_set = set(selected_elements)
        
        # Apply changes only to selected elements
        for i, change in enumerate(data['preview_data']):
            post_index = None
            # Find the corresponding post
            for idx, post in enumerate(data['posts']):
                if post['title'] == change['post_title']:
                    post_index = idx
                    break
            
            if post_index is None:
                continue
                
            original_content = data['posts'][post_index].get('content', '')
            if not original_content:
                continue
            
            # Apply replacements only for selected elements
            modified_content = original_content
            changes_made = 0
            
            for idx, element in enumerate(change["elements"]):
                element_id = f'element-{i}-{idx}'
                if element_id in selected_set:
                    # Apply this specific replacement
                    old_href = element["original_href"]
                    new_href = element["new_href"]
                    
                    if use_regex:
                        modified_content = re.sub(re.escape(old_href), new_href, modified_content)
                    else:
                        modified_content = modified_content.replace(old_href, new_href)
                    changes_made += 1
            
            if changes_made > 0:
                data['posts'][post_index]['content'] = modified_content
                total_changes += changes_made
        
        data['last_updated'] = datetime.now()
        data['has_modifications'] = True  # Mark that find/replace was used
        
        # Clear preview data
        data.pop('preview_data', None)
        data.pop('preview_search', None) 
        data.pop('preview_replace', None)
        data.pop('preview_regex', None)
        
        return jsonify({
            'success': True,
            'changes_made': total_changes,
            'message': f'Successfully replaced {total_changes} selected instances'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error applying selective find/replace: {str(e)}'})


@app.route('/api/find-replace/global-preview', methods=['POST'])
def global_preview_replace():
    """Preview find/replace changes across all posts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        search_pattern = data.get('searchPattern', '').strip()
        replace_with = data.get('replaceWith', '').strip()
        use_regex = data.get('useRegex', False)
        target_post_index = data.get('targetPostIndex')
        
        if not search_pattern:
            return jsonify({'error': 'Search pattern is required'}), 400
        
        session_data = get_session_data()
        posts = session_data.get('posts', [])
        
        if not posts:
            return jsonify({'error': 'No posts available'}), 400
        
        # If targeting specific post, only process that post
        if target_post_index is not None:
            if target_post_index >= len(posts):
                return jsonify({'error': 'Invalid post index'}), 400
            posts_to_process = [(target_post_index, posts[target_post_index])]
        else:
            posts_to_process = enumerate(posts)
        
        all_matches = []
        
        for post_index, post in posts_to_process:
            content = post['content']
            post_matches = []
            
            try:
                # Parse HTML to find only hyperlinks, not images
                from bs4 import BeautifulSoup, Tag
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all <a> tags with href attributes that match our search pattern
                for link in soup.find_all('a', href=True):
                    if isinstance(link, Tag):
                        href = link.get('href', '')
                        if isinstance(href, list):
                            href = href[0] if href else ''
                        if not href:
                            continue
                        
                        # Check if this href matches our search pattern
                        match_found = False
                        replacement = href  # Default to original href
                        if use_regex:
                            import re
                            pattern = re.compile(search_pattern)
                            if pattern.search(href):
                                match_found = True
                                replacement = pattern.sub(replace_with, href)
                        else:
                            if search_pattern in href:
                                match_found = True
                                replacement = href.replace(search_pattern, replace_with)
                        
                        if match_found:
                            # Get context around this link
                            link_text = link.get_text(strip=True) or '[No text]'
                            
                            # Find position of this href in the original content
                            href_start = content.find(f'href="{href}"')
                            if href_start == -1:
                                href_start = content.find(f"href='{href}'")
                            if href_start == -1:
                                # Try without quotes
                                href_start = content.find(f'href={href}')
                            
                            if href_start != -1:
                                # Find the start and end of the href value
                                href_value_start = content.find(href, href_start)
                                href_value_end = href_value_start + len(href)
                                position = (href_value_start, href_value_end)
                            else:
                                # Fallback: use simple string search
                                href_start = content.find(href)
                                if href_start != -1:
                                    position = (href_start, href_start + len(href))
                                else:
                                    position = (0, 0)  # Fallback position
                            
                            # Get surrounding context
                            parent = link.parent
                            context = ""
                            if parent:
                                parent_text = parent.get_text(strip=True)
                                if len(parent_text) > 150:
                                    # Find the link position and get context around it
                                    link_pos = parent_text.find(link_text)
                                    if link_pos != -1:
                                        start = max(0, link_pos - 50)
                                        end = min(len(parent_text), link_pos + len(link_text) + 50)
                                        context = parent_text[start:end]
                                        if start > 0:
                                            context = "..." + context
                                        if end < len(parent_text):
                                            context = context + "..."
                                    else:
                                        context = parent_text[:150] + "..." if len(parent_text) > 150 else parent_text
                                else:
                                    context = parent_text
                            
                            post_matches.append({
                                'text': href,
                                'replacement': replacement,
                                'link_text': link_text,
                                'context': context,
                                'context_highlight_start': 0,
                                'context_highlight_end': len(context),
                                'position': position
                            })
            
            except Exception as e:
                return jsonify({'error': f'Regex error: {str(e)}'}), 400
            
            if post_matches:
                all_matches.append({
                    'post_index': post_index,
                    'post_title': post.get('title', 'Untitled'),
                    'post_url': post.get('url', ''),
                    'matches': post_matches
                })
        
        # Store matches for apply operation
        session_data['global_matches'] = all_matches
        session_data['global_search_pattern'] = search_pattern
        session_data['global_replace_with'] = replace_with
        session_data['global_use_regex'] = use_regex
        # Session data is automatically saved in app_data
        
        total_matches = sum(len(post_data['matches']) for post_data in all_matches)
        
        return jsonify({
            'matches': all_matches,
            'total_matches': total_matches,
            'total_posts': len(all_matches)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/find-replace/global-apply', methods=['POST'])
def global_apply_replace():
    """Apply selected global find/replace changes across multiple posts."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        selected_matches = data.get('selectedMatches', [])
        
        if not selected_matches:
            return jsonify({'error': 'No matches selected'}), 400
        
        session_data = get_session_data()
        posts = session_data.get('posts', [])
        global_matches = session_data.get('global_matches', [])
        
        if not posts or not global_matches:
            return jsonify({'error': 'No data available for replacement'}), 400
        
        # Group selected matches by post
        matches_by_post = {}
        for match_id in selected_matches:
            # match_id format: "post_index:match_index"
            try:
                post_index, match_index = map(int, match_id.split(':'))
                if post_index not in matches_by_post:
                    matches_by_post[post_index] = []
                matches_by_post[post_index].append(match_index)
            except (ValueError, IndexError):
                continue
        
        total_applied = 0
        
        # Apply replacements to each post
        for post_index, match_indices in matches_by_post.items():
            if post_index >= len(posts):
                continue
            
            # Find the corresponding global match data
            post_match_data = None
            for global_match in global_matches:
                if global_match['post_index'] == post_index:
                    post_match_data = global_match
                    break
            
            if not post_match_data:
                continue
            
            content = posts[post_index]['content']
            
            # Apply replacements in reverse order to maintain indices
            for match_index in sorted(match_indices, reverse=True):
                if 0 <= match_index < len(post_match_data['matches']):
                    match = post_match_data['matches'][match_index]
                    start, end = match['position']
                    content = content[:start] + match['replacement'] + content[end:]
                    total_applied += 1
            
            # Update post content
            posts[post_index]['content'] = content
            posts[post_index]['modified'] = True
        
        session_data['posts'] = posts
        session_data['has_modifications'] = True
        # Session data is automatically saved in app_data
        
        # Clear global match data
        session_data.pop('global_matches', None)
        session_data.pop('global_search_pattern', None)
        session_data.pop('global_replace_with', None)
        session_data.pop('global_use_regex', None)
        # Session data is automatically saved in app_data
        
        return jsonify({
            'success': True,
            'message': f'Applied {total_applied} replacements across {len(matches_by_post)} posts'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-url-list', methods=['GET'])
def get_url_list():
    """Get a clean list of hyperlinks only (no images)"""
    try:
        data = get_session_data()
        posts = data.get('posts', [])
        
        if not posts:
            return jsonify({'success': False, 'error': 'No posts available'})
        
        # Extract hyperlinks from already-parsed content (avoids navigation/sidebar links)
        url_details = []
        
        for post_index, post in enumerate(posts):
            post_title = post.get('title', 'Untitled')
            post_source_url = post.get('url', '')  # Get the source URL
            hyperlinks = post.get('hyperlinks', {})
            
            # Get all link types from the cleaned extraction
            all_links = []
            all_links.extend(hyperlinks.get('internal_links', []))
            all_links.extend(hyperlinks.get('external_links', []))
            all_links.extend(hyperlinks.get('relative_links', []))
            
            for link_data in all_links:
                if isinstance(link_data, dict):
                    url = link_data.get('url', '')
                    link_text = link_data.get('text', '[No text]')
                elif isinstance(link_data, str):
                    url = link_data
                    link_text = '[No text]'
                else:
                    continue
                
                if url and not url.startswith('#'):  # Skip anchor links
                    url_details.append({
                        'url': url,
                        'link_text': link_text,
                        'post_title': post_title,
                        'post_index': post_index,
                        'source_url': post_source_url  # Add source URL
                    })
        
        # Create simple hyperlinks list
        if not url_details:
            html = '<div class="alert alert-info">No hyperlinks found in your content.</div>'
        else:
            # Group by URL for deduplication
            link_groups = {}
            for detail in url_details:
                url = detail['url']
                if url not in link_groups:
                    link_groups[url] = {
                        'count': 0,
                        'contexts': [],
                        'url': url
                    }
                link_groups[url]['count'] += 1
                link_groups[url]['contexts'].append(detail)
            
            # Relative links are identified inline when needed
            
            html = f'''
                <div class="alert alert-success">
                    📊 Found {len(link_groups)} unique hyperlinks across {len(posts)} posts
                </div>
                <div class="mb-3">
                    <small class="text-muted">Use Global Find & Replace above to modify these URLs across all posts.</small>
                </div>
                <div class="list-group">
            '''
            
            # Show each unique URL with copy and replace options
            for url, group_data in sorted(link_groups.items(), key=lambda x: x[1]['count'], reverse=True):
                count = group_data['count']
                contexts = group_data['contexts']
                first_context = contexts[0]
                
                # Determine URL type for styling
                if url.startswith('http'):
                    badge_class = "bg-primary"
                    url_type = "External"
                elif url.startswith('/'):
                    badge_class = "bg-warning"
                    url_type = "Relative"
                else:
                    badge_class = "bg-secondary"
                    url_type = "Other"
                
                escaped_url = url.replace("'", "\\'")
                
                # Check if this URL has been modified
                url_id = f"url_{hash(url) % 100000}"  # Create unique ID for URL
                
                # Get the source URL from the first context
                source_url = first_context.get('source_url', '')
                
                html += f'''
                    <div class="list-group-item" id="{url_id}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="flex-grow-1 me-3">
                                <div class="mb-1">
                                    <span class="badge {badge_class} me-2">{count}x</span>
                                    <small class="text-muted">{url_type}</small>
                                    <span class="badge bg-success ms-2" id="{url_id}_edited" style="display: none;">✓ Edited</span>
                                </div>
                                <code class="d-block text-break small">{url}</code>
                                <small class="text-muted">"{first_context['link_text']}" in {first_context['post_title']}</small>
                            </div>
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('{escaped_url}')" title="Copy URL">
                                    📋 Copy
                                </button>
                                <button class="btn btn-sm btn-outline-primary" onclick="openFindReplaceForUrl('{escaped_url}', '{url_id}')" title="Find & Replace this URL">
                                    🔧 Replace
                                </button>
                                {f'<a href="{source_url}" target="_blank" class="btn btn-sm btn-outline-info" title="View source post">🔗 Source</a>' if source_url else ''}
                            </div>
                        </div>
                    </div>
                '''
            
            html += '</div>'
        
        return jsonify({'success': True, 'html': html})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})




@app.route('/api/get-posts-with-url', methods=['POST'])
def get_posts_with_url():
    """Get list of posts that contain a specific URL"""
    try:
        data = get_session_data()
        posts = data.get('posts', [])
        req_data = request.get_json()
        search_url = req_data.get('url', '')
        
        if not search_url:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        matching_posts = []
        
        for post_index, post in enumerate(posts):
            content = post.get('content', '')
            if search_url in content:
                matching_posts.append({
                    'index': post_index,
                    'title': post.get('title', 'Untitled'),
                    'url': post.get('url', '')
                })
        
        return jsonify({'success': True, 'posts': matching_posts})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print('Starting Modern WordPress Migration Tool')
    print('Available at: http://localhost:5000')
    app.run(debug=True, host='127.0.0.1', port=5000)
