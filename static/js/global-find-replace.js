// Global Find & Replace functionality

// Open find/replace modal with specific URL pre-filled (GLOBAL mode)
function openFindReplaceForUrl(url, urlId) {
    // Pre-fill the modal with the specific URL
    document.getElementById('globalSearchPattern').value = url;
    document.getElementById('globalReplaceWith').value = '';
    document.getElementById('globalUseRegex').checked = false;
    document.getElementById('globalPreviewSection').style.display = 'none';
    document.getElementById('globalApplyBtn').disabled = true;
    
    // Store URL ID for showing edit status
    window.currentUrlId = urlId;
    
    // Reset to global mode
    window.targetPostIndex = undefined;
    document.getElementById('globalFindReplaceModalLabel').textContent = '🌐 Global Find & Replace';
    
    const modal = new bootstrap.Modal(document.getElementById('globalFindReplaceModal'));
    modal.show();
}

// Open find/replace for URL in specific post only (POST mode)
function openFindReplaceForUrlInPost(url) {
    // Show post selector first
    fetch('/api/get-posts-with-url', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: url})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.posts.length > 0) {
            if (data.posts.length === 1) {
                // Only one post, go directly to find/replace
                openFindReplaceForUrlInSpecificPost(url, data.posts[0].index);
            } else {
                // Multiple posts, show selector
                showPostSelector(url, data.posts);
            }
        } else {
            alert('No posts found containing this URL');
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function openFindReplaceForUrlInSpecificPost(url, postIndex) {
    // Pre-fill and set post-specific mode
    document.getElementById('globalSearchPattern').value = url;
    document.getElementById('globalReplaceWith').value = '';
    document.getElementById('globalUseRegex').checked = false;
    document.getElementById('globalPreviewSection').style.display = 'none';
    document.getElementById('globalApplyBtn').disabled = true;
    
    // Store post index for targeted replacement
    window.targetPostIndex = postIndex;
    
    // Update modal title to indicate post-specific mode
    document.getElementById('globalFindReplaceModalLabel').textContent = '📍 Find & Replace (This Post Only)';
    
    const modal = new bootstrap.Modal(document.getElementById('globalFindReplaceModal'));
    modal.show();
}

function showPostSelector(url, posts) {
    const modalContent = `
        <div class="modal fade" id="postSelectorModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Select Post</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>This URL appears in ${posts.length} posts. Select which post to modify:</p>
                        <div class="list-group">
                            ${posts.map(post => `
                                <button class="list-group-item list-group-item-action" 
                                        onclick="selectPostForReplace('${url}', ${post.index})">
                                    <strong>${post.title}</strong>
                                    <br><small class="text-muted">${post.url}</small>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existing = document.getElementById('postSelectorModal');
    if (existing) existing.remove();
    
    // Add and show modal
    document.body.insertAdjacentHTML('beforeend', modalContent);
    const modal = new bootstrap.Modal(document.getElementById('postSelectorModal'));
    modal.show();
}

function selectPostForReplace(url, postIndex) {
    // Close post selector and open find/replace for specific post
    bootstrap.Modal.getInstance(document.getElementById('postSelectorModal')).hide();
    openFindReplaceForUrlInSpecificPost(url, postIndex);
}

// Open find/replace for URL in specific post only
function openFindReplaceForUrlInPost(url, postIndex) {
    // Pre-fill and set post-specific mode
    document.getElementById('globalSearchPattern').value = url;
    document.getElementById('globalReplaceWith').value = '';
    document.getElementById('globalUseRegex').checked = false;
    document.getElementById('globalPreviewSection').style.display = 'none';
    document.getElementById('globalApplyBtn').disabled = true;
    
    // Store post index for targeted replacement
    window.targetPostIndex = postIndex;
    
    // Update modal title to indicate post-specific mode
    document.getElementById('globalFindReplaceModalLabel').textContent = '🔧 Find & Replace URLs (This Post Only)';
    
    const modal = new bootstrap.Modal(document.getElementById('globalFindReplaceModal'));
    modal.show();
}

// General find/replace (no pre-filled URL)
function openGlobalFindReplace() {
    // Clear modal and reset to global mode
    document.getElementById('globalSearchPattern').value = '';
    document.getElementById('globalReplaceWith').value = '';
    document.getElementById('globalUseRegex').checked = false;
    document.getElementById('globalPreviewSection').style.display = 'none';
    document.getElementById('globalApplyBtn').disabled = true;
    
    // Reset to global mode
    window.targetPostIndex = undefined;
    document.getElementById('globalFindReplaceModalLabel').textContent = '🔧 Find & Replace URLs';
    
    const modal = new bootstrap.Modal(document.getElementById('globalFindReplaceModal'));
    modal.show();
}

// Preview global replace changes
function previewGlobalReplace() {
    const searchPattern = document.getElementById('globalSearchPattern').value;
    const replaceWith = document.getElementById('globalReplaceWith').value;
    const useRegex = document.getElementById('globalUseRegex').checked;
    
    if (!searchPattern || !replaceWith) {
        alert('Please fill in both search and replace fields');
        return;
    }
    
    fetch('/api/find-replace/global-preview', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            searchPattern: searchPattern,
            replaceWith: replaceWith,
            useRegex: useRegex,
            targetPostIndex: window.targetPostIndex
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.matches) {
            displayGlobalMatches(data);
            document.getElementById('globalPreviewSection').style.display = 'block';
            document.getElementById('globalApplyBtn').disabled = false;
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function displayGlobalMatches(data) {
    const content = document.getElementById('globalPreviewContent');
    
    if (data.total_matches === 0) {
        content.innerHTML = '<div class="alert alert-info">No matches found in your content.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-success">
            Found ${data.total_matches} matches in your content
        </div>
        <div class="mb-3 d-flex gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="selectAllGlobalMatches()">
                ✓ Select All (${data.total_matches})
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="selectNoneGlobalMatches()">
                ✗ Select None
            </button>
            <div class="ms-auto">
                <span class="badge bg-info" id="selectedCount">0 selected</span>
            </div>
        </div>
        <div class="list-group">
    `;
    
    let globalIndex = 0;
    data.matches.forEach(postData => {
        postData.matches.forEach((match, matchIndex) => {
            const matchId = `${postData.post_index}:${matchIndex}`;
            globalIndex++;
            
            html += `
                <div class="list-group-item">
                    <div class="form-check">
                        <input class="form-check-input global-match-checkbox" type="checkbox" 
                               value="${matchId}" id="global-match-${matchId}" 
                               onchange="updateSelectedCount()">
                        <label class="form-check-label" for="global-match-${matchId}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <div class="mb-2">
                                        <small class="text-muted">
                                            <strong>#${globalIndex}</strong> in: 
                                            <a href="${postData.post_url}" target="_blank" class="text-decoration-none">
                                                <strong>${postData.post_title}</strong> 🔗
                                            </a>
                                        </small>
                                    </div>
                                    <div class="mb-2">
                                        <small class="text-info">Link text: "<em>${match.link_text}</em>"</small>
                                    </div>
                                    <div class="font-monospace small bg-light p-2 rounded">
                                        <div class="text-danger">- ${match.text}</div>
                                        <div class="text-success">+ ${match.replacement}</div>
                                    </div>
                                </div>
                            </div>
                        </label>
                    </div>
                </div>
            `;
        });
    });
    
    html += '</div>';
    content.innerHTML = html;
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.global-match-checkbox');
    const selectedCount = document.querySelectorAll('.global-match-checkbox:checked').length;
    const totalCount = checkboxes.length;
    
    const badge = document.getElementById('selectedCount');
    if (badge) {
        badge.textContent = `${selectedCount} of ${totalCount} selected`;
        badge.className = selectedCount > 0 ? 'badge bg-success' : 'badge bg-secondary';
    }
    
    // Enable/disable apply button based on selection
    const applyBtn = document.getElementById('globalApplyBtn');
    if (applyBtn) {
        applyBtn.disabled = selectedCount === 0;
    }
}

function selectAllGlobalMatches() {
    document.querySelectorAll('.global-match-checkbox').forEach(cb => cb.checked = true);
    updateSelectedCount();
}

function selectNoneGlobalMatches() {
    document.querySelectorAll('.global-match-checkbox').forEach(cb => cb.checked = false);
    updateSelectedCount();
}

// Apply global replace changes
function applyGlobalReplace() {
    // Get selected replacements
    const selectedMatches = [];
    document.querySelectorAll('.global-match-checkbox:checked').forEach(cb => {
        selectedMatches.push(cb.value);
    });
    
    if (selectedMatches.length === 0) {
        alert('Please select at least one match to replace');
        return;
    }
    
    fetch('/api/find-replace/global-apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            selectedMatches: selectedMatches
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            
            // Show edited indicator if we have a specific URL ID
            if (window.currentUrlId) {
                const editedBadge = document.getElementById(window.currentUrlId + '_edited');
                if (editedBadge) {
                    editedBadge.style.display = 'inline';
                }
                window.currentUrlId = null;
            }
            
            // Close modal and show download section
            bootstrap.Modal.getInstance(document.getElementById('globalFindReplaceModal')).hide();
            document.getElementById('download-card').style.display = 'block';
            
            // Update download section to show both original and modified XML options
            document.getElementById('download-section').innerHTML = `
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
                <small class="text-muted">
                    Ready to import into WordPress: Tools → Import → WordPress
                </small>
            `;
            
            document.getElementById('download-card').scrollIntoView({behavior: 'smooth'});
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}