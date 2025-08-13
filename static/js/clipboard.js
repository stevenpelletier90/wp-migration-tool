// Clipboard functionality with fallbacks
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // Modern clipboard API
        navigator.clipboard.writeText(text).then(() => {
            showCopyFeedback('URL copied to clipboard!');
        }).catch(err => {
            // Fallback for clipboard API failures
            fallbackCopy(text);
        });
    } else {
        // Fallback for older browsers or non-HTTPS
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    // Create temporary textarea
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopyFeedback('URL copied to clipboard!');
    } catch (err) {
        showCopyFeedback('Copy failed - please copy manually');
    }
    
    document.body.removeChild(textArea);
}

function showCopyFeedback(message) {
    // Create temporary toast notification
    const toast = document.createElement('div');
    toast.className = 'alert alert-success position-fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '250px';
    toast.innerHTML = `<i class="bi bi-check-circle me-2"></i>${message}`;
    
    document.body.appendChild(toast);
    
    // Remove after 2 seconds
    setTimeout(() => {
        if (document.body.contains(toast)) {
            document.body.removeChild(toast);
        }
    }, 2000);
}