// Find & Replace functionality
function findReplace(url, postIndex) {
    // Pre-populate the modal and show it
    document.getElementById('searchPattern').value = url;
    document.getElementById('replaceWith').value = '';
    document.getElementById('useRegex').checked = false;
    document.getElementById('previewSection').style.display = 'none';
    document.getElementById('applyBtn').disabled = true;
    
    // Store the original URL and post index for context
    window.currentReplaceUrl = url;
    window.currentPostIndex = postIndex;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('findReplaceModal'));
    modal.show();
}

// Preview replace changes
function previewReplace() {
    const searchPattern = document.getElementById('searchPattern').value;
    const replaceWith = document.getElementById('replaceWith').value;
    const useRegex = document.getElementById('useRegex').checked;
    
    if (!searchPattern || !replaceWith) {
        alert('Please fill in both search and replace fields');
        return;
    }
    
    // Call API to preview changes
    fetch('/api/find-replace/preview', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            search_pattern: searchPattern,
            replace_with: replaceWith,
            use_regex: useRegex,
            post_index: window.currentPostIndex
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('previewContent').innerHTML = data.diff_html;
            document.getElementById('previewSection').style.display = 'block';
            document.getElementById('applyBtn').disabled = false;
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

// Apply replace changes
function applyReplace() {
    const searchPattern = document.getElementById('searchPattern').value;
    const replaceWith = document.getElementById('replaceWith').value;
    const useRegex = document.getElementById('useRegex').checked;
    
    // Get selected replacements
    const selectedElements = [];
    document.querySelectorAll('.replacement-checkbox:checked').forEach(cb => {
        selectedElements.push(cb.value);
    });
    
    if (selectedElements.length === 0) {
        alert('Please select at least one link to replace');
        return;
    }
    
    fetch('/api/find-replace/apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            search_pattern: searchPattern,
            replace_with: replaceWith,
            use_regex: useRegex,
            selected_elements: selectedElements,
            post_index: window.currentPostIndex
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Successfully replaced ${data.changes_made} instances`);
            // Close modal and show download section with updated status
            bootstrap.Modal.getInstance(document.getElementById('findReplaceModal')).hide();
            document.getElementById('download-card').style.display = 'block';
            
            // Update download section for modified XML
            document.getElementById('download-section').innerHTML = `
                <div class="d-grid">
                    <a href="/api/download" class="btn btn-success btn-lg" download="wordpress_import.xml">
                        <i class="bi bi-arrow-repeat"></i> Download Updated XML
                    </a>
                </div>
                <div class="mt-3">
                    <div class="alert alert-success py-2">
                        <small><strong>Updated with your find/replace changes (${data.changes_made} changes)</strong></small>
                    </div>
                    <small class="text-muted">
                        Ready to import into WordPress: Tools → Import → WordPress
                    </small>
                </div>
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