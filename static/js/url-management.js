// URL management functionality
function updateUrl(index, newUrl) {
    // Update URL via AJAX
    fetch('/api/urls/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({index: index, url: newUrl})
    });
}

function addNewUrl() {
    const newUrl = prompt('Enter new URL:');
    if (newUrl) {
        fetch('/api/urls/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: newUrl})
        }).then(() => {
            // Refresh the URL list
            htmx.ajax('GET', '/api/urls/list', '#url-manager');
        });
    }
}

function toggleAllUrls() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.url-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
    updateBulkDeleteButton();
}

function updateBulkDeleteButton() {
    const selectedCheckboxes = document.querySelectorAll('.url-checkbox:checked');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    
    if (bulkDeleteBtn) {
        bulkDeleteBtn.style.display = selectedCheckboxes.length > 0 ? 'inline-block' : 'none';
    }
}

function bulkDeleteUrls() {
    const selectedIndexes = [];
    document.querySelectorAll('.url-checkbox:checked').forEach(cb => {
        selectedIndexes.push(parseInt(cb.value));
    });
    
    if (selectedIndexes.length === 0) {
        alert('Please select URLs to delete');
        return;
    }
    
    if (confirm(`Delete ${selectedIndexes.length} selected URLs?`)) {
        fetch('/api/urls/bulk-delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({indexes: selectedIndexes})
        }).then(() => {
            // Refresh the URL list
            htmx.ajax('GET', '/api/urls/list', '#url-manager');
        });
    }
}

// Show URL list functionality
function showUrlList() {
    fetch('/api/get-url-list', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('url-list-content').innerHTML = data.html;
            document.getElementById('url-list-section').style.display = 'block';
        } else {
            alert('Error: ' + (data.error || 'Unable to load URL list'));
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

// Replace mode management
let currentReplaceMode = null;

function selectIndividualMode(scope) {
    currentReplaceMode = `individual-${scope}`;
    updateModeIndicator();
}

function openBulkByPostReplace() {
    currentReplaceMode = 'bulk-post';
    updateModeIndicator();
    // TODO: Show post selector modal
    alert('Bulk by Post: Select a post, then select multiple URLs from that post');
}

function updateModeIndicator() {
    const indicator = document.getElementById('mode-indicator');
    const modeSpan = document.getElementById('current-mode');
    
    if (currentReplaceMode) {
        indicator.style.display = 'block';
        switch(currentReplaceMode) {
            case 'individual-global':
                modeSpan.textContent = '🎯 Individual Global - Click any URL to replace across ALL posts';
                break;
            case 'individual-post':
                modeSpan.textContent = '📍 Individual by Post - Click any URL to replace in ONE post only';
                break;
            case 'bulk-post':
                modeSpan.textContent = '📝 Bulk by Post - Select multiple URLs from one post';
                break;
            default:
                modeSpan.textContent = 'Unknown mode';
        }
    } else {
        indicator.style.display = 'none';
    }
}

function handleUrlAction(url) {
    if (!currentReplaceMode) {
        alert('Please select a replace mode first (Bulk Global, Bulk by Post, Individual Global, or Individual by Post)');
        return;
    }
    
    switch(currentReplaceMode) {
        case 'individual-global':
            openFindReplaceForUrl(url);
            break;
        case 'individual-post':
            openFindReplaceForUrlInPost(url);
            break;
        case 'bulk-post':
            // TODO: Add to bulk selection for specific post
            alert('Bulk by Post mode: This will be implemented next');
            break;
        default:
            alert('Unknown replace mode');
    }
}