// Main application orchestrator - loads and coordinates all JavaScript modules
// Entry point for WordPress Migration Tool

console.log('WordPress Migration Tool - Loading JavaScript modules...');

// Application configuration
window.WordPressApp = {
    version: '2.0',
    modules: ['app-init', 'clipboard', 'url-management', 'find-replace', 'global-find-replace'],
    initialized: false
};

// Initialize application when all scripts are loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('WordPress Migration Tool - All modules loaded successfully');
    console.log('Available modules:', window.WordPressApp.modules);
    window.WordPressApp.initialized = true;
});