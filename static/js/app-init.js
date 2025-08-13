// App initialization and UI state management
document.addEventListener('alpine:init', () => {
    // Show migration card when URLs are added
    document.body.addEventListener('htmx:afterSwap', (e) => {
        if (e.detail.target.id === 'url-status' && e.detail.xhr.status === 200) {
            document.getElementById('migration-card').style.display = 'block';
        }
        if (e.detail.target.id === 'migration-status' && e.detail.xhr.status === 200) {
            document.getElementById('findreplace-card').style.display = 'block';
        }
    });
});

// Skip to download functionality
function skipToDownload() {
    document.getElementById('download-card').style.display = 'block';
    document.getElementById('download-card').scrollIntoView({behavior: 'smooth'});
    
    // Update download section for original XML
    document.getElementById('download-section').innerHTML = `
        <div class="d-grid">
            <a href="/api/download" class="btn btn-success btn-lg" download="wordpress_import.xml">
                <i class="bi bi-download"></i> Download Original XML
            </a>
        </div>
        <div class="mt-3">
            <div class="alert alert-info py-2">
                <small><strong>Original extracted content (no URL changes)</strong></small>
            </div>
            <small class="text-muted">
                Ready to import into WordPress: Tools → Import → WordPress
            </small>
        </div>
    `;
}