# WordPress Blog Migration Tool

A streamlined Python tool for extracting blog metadata and content from websites and generating WordPress WXR import files with an advanced web interface.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Current Project Status

**✅ Fully Functional** - Modern web interface with advanced content extraction
**✅ Smart URL Management** - Separate hyperlinks from images with context
**✅ Selective Find & Replace** - Choose exactly which URLs to modify
**✅ Modern Content Extraction** - Using newspaper3k and trafilatura libraries
**✅ Clean UI/UX** - Professional interface with copy functionality
**✅ Organized Structure** - Files properly organized by purpose
**✅ Type Safety** - Proper type stubs installed for BeautifulSoup
**✅ Code Quality** - All linting issues resolved with Ruff

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Install dependencies
venv\Scripts\pip.exe install -r requirements.txt

# Install type stubs for better IDE support
venv\Scripts\pip.exe install types-beautifulsoup4 types-requests types-lxml
```

### 2. Run the Application

#### **Web Interface (Recommended)**
```bash
venv\Scripts\python.exe modern_app.py
```
**Access:** `http://localhost:5000/`

#### **Command Line Extraction**
```bash
# Fast extraction (newspaper3k/trafilatura)
venv\Scripts\python.exe extractors/modern_extractor.py

# Browser automation (for difficult sites)
venv\Scripts\python.exe extractors/browser_scraper.py
```

### 3. Basic Workflow
1. **Edit URLs** - Add your blog post URLs to `config/urls.txt` (one per line)
2. **Choose Method** - Web interface, command line, or browser automation
3. **Process URLs** - Extract content with modern libraries
4. **Review Results** - Check `output/` directory for generated XML
5. **Import to WordPress** - Use the XML file in WordPress Tools → Import

## 📁 Current Project Structure

```
C:\Users\steve\Downloads\wp-migration-tool\
├── modern_app.py                 # Main Flask application (1247 lines)
├── CLAUDE.md                    # This documentation
├── PROJECT_STRUCTURE.md         # Detailed project organization
├── QUICK_START.md               # Simple getting started guide
├── requirements.txt             # Dependencies
├── config/                      # Configuration files
│   ├── urls.txt                 # URL source file
│   └── chromedriver.exe         # For browser automation
├── extractors/                  # Content extraction methods
│   ├── modern_extractor.py      # newspaper3k/trafilatura extraction
│   ├── browser_scraper.py       # Selenium browser automation
│   └── fixed_extractor.py       # XML generation utilities
├── output/                      # Generated WordPress XML files
├── static/                      # Web interface assets
│   ├── css/main.css            # Custom styles
│   └── js/                     # JavaScript modules
├── templates/                   # HTML templates
│   └── index.html              # Main web interface
└── venv/                       # Virtual environment
```

**✅ WELL-ORGANIZED: Clean directory structure with separated concerns**

## ✨ Current Key Features

### 🎯 **Modern Content Extraction**
- **newspaper3k library** - Primary extraction with fallback to trafilatura
- **Smart content detection** - Finds main content areas, excludes navigation
- **Full metadata extraction** - Titles, dates, categories, tags, complete HTML
- **Clean XML output** - Removes invalid characters, proper CDATA handling
- **WordPress WXR format** - Ready for direct WordPress import

### 🔗 **Smart URL Management**
- **Hyperlinks vs Images** - Clearly separated with different handling
- **Content-only extraction** - Only URLs from actual post content
- **Tracking image filtering** - Excludes analytics/tracking pixels
- **Rich context display** - Link text, surrounding content, post location
- **One-click copying** - Copy any URL with toast feedback

### 🔧 **Advanced Find & Replace**
- **Hyperlink-only processing** - Images excluded from find/replace operations
- **Global vs per-post targeting** - Replace across all posts or specific posts
- **Selective replacement** - Choose exactly which matches to replace
- **Pre-filled from URL list** - Quick access to replace specific URLs
- **Live preview** - See exactly what will change before applying
- **Professional UI** - Accordion layout with context and controls

### 🎨 **Professional Interface**
- **Bootstrap 5.3.7** - Modern, responsive design
- **HTMX 2.0.6** - Dynamic interactions without page reloads
- **Alpine.js 3.14.9** - Lightweight reactive components
- **Toast notifications** - User feedback for copy operations
- **Progressive disclosure** - Tools appear after migration completion

## 🔄 Current User Workflow

### **Method 1: Web Interface (Recommended)**
```
1. Start web app: venv\Scripts\python.exe modern_app.py
2. Open browser: http://localhost:5000
3. Add URLs (paste blog post URLs)
4. Start Migration (extract with modern libraries)  
5. Show All URLs (review hyperlinks vs images)
6. Find & Replace URLs (optional - global or per-post)
7. Download WordPress XML
```

### **Method 2: Command Line**
```
1. Edit config/urls.txt (add your URLs)
2. Run extractor: venv\Scripts\python.exe extractors/modern_extractor.py
3. Check output/modern_export.xml
4. Import to WordPress
```

### **Method 3: Browser Automation**
```
1. Edit config/urls.txt (add your URLs)
2. Run browser scraper: venv\Scripts\python.exe extractors/browser_scraper.py
3. Check output/wordpress_import.xml
4. Import to WordPress
```

### **URL Management Options (Web Interface)**
- **📋 Copy URLs** - One-click copying with toast feedback
- **🔧 Global Replace** - Modify URL across all posts  
- **📝 Per-Post Replace** - Modify URL in specific post only
- **🖼️ Image Reference** - Images shown separately (copy-only)

## 🛠️ Current Technical Architecture

### **Frontend (✅ WELL SEPARATED)**
- **HTML Templates** - Clean Jinja2 templates in templates/
- **Static Assets** - Organized CSS and JS modules in static/
- **Bootstrap 5.3.7** - Professional UI components via CDN
- **HTMX 2.0.6** - Dynamic interactions via CDN
- **Alpine.js 3.14.9** - Reactive components via CDN
- **Modular JS** - Multiple focused JavaScript modules

### **Backend** 
- **Flask application** - `modern_app.py` (1247 lines, well-structured)
- **Modern extraction** - `extractors/modern_extractor.py` with newspaper3k/trafilatura  
- **Browser automation** - `extractors/browser_scraper.py` with Selenium
- **Organized structure** - Proper separation of extractors, config, and output
- **Session-based storage** - In-memory data handling
- **BeautifulSoup parsing** - HTML/XML processing with proper type stubs

### **Current API Endpoints**
- `POST /api/urls` - Add URLs to session
- `POST /api/migrate` - Execute modern content extraction
- `GET /api/get-url-list` - Get hyperlinks vs images with context
- `POST /api/find-replace/global-preview` - Preview global find/replace
- `POST /api/find-replace/global-apply` - Apply selected global changes
- `GET /api/download` - Download WordPress XML
- `GET /health` - Health check

## 🚨 URGENT: Refactoring Required

### **Current Problems**
- **2000+ line single file** - `modern_app.py` is unmaintainable  
- **Inline HTML/CSS/JS** - All frontend code mixed with Python
- **No asset separation** - CSS and JavaScript embedded in strings
- **Hard to maintain** - Simple changes require editing large Python file

### **Proposed Refactoring Plan**

#### **Step 1: Separate Frontend Assets**
```
templates/
├── index.html              # Main template
├── static/
│   ├── css/
│   │   └── main.css        # Extracted CSS
│   └── js/
│       └── main.js         # Extracted JavaScript
└── partials/
    ├── url-list.html       # URL list template  
    └── find-replace.html   # Find/replace modal
```

#### **Step 2: Modularize Backend**  
```
modern_app.py               # Main Flask app (routes only)
├── routes/
│   ├── __init__.py
│   ├── urls.py            # URL management routes
│   ├── migration.py       # Migration routes  
│   └── find_replace.py    # Find/replace routes
├── services/
│   ├── __init__.py
│   ├── url_service.py     # URL processing logic
│   └── migration_service.py # Migration logic
└── templates/             # HTML templates
```

#### **Step 3: Clean Architecture**
- **Templates** - Separate HTML files with Jinja2
- **Static assets** - CSS/JS in proper directories
- **Service layer** - Business logic separated from routes
- **Proper imports** - Modular, testable code

### **Benefits After Refactoring**
- **Maintainable** - Each file has single responsibility
- **Testable** - Services can be unit tested
- **Scalable** - Easy to add new features
- **Professional** - Industry-standard Flask structure

## 📋 Configuration

### **URL Source** (`config/urls.txt`)
```
# WordPress Migration URLs - Add your blog post URLs below
https://www.parkfordofmahopac.com/blog/2025/july/26/discover-the-benefits-of-shopping-at-park-ford-of-mahopac-the-go-to-ford-dealer-for-cortlandt-manor-drivers.htm
https://www.parkfordofmahopac.com/blog/2025/june/26/come-shop-for-new-ford-vehicles-near-scarsdale-ny.htm
# Comments start with #
```

### **Browser Automation** (`config/chromedriver.exe`)
- Required for browser_scraper.py
- Download from https://chromedriver.chromium.org/
- Must match your Chrome browser version

## 🎯 Current Find & Replace Features

### **Smart URL Detection**
- **Hyperlinks only** - Find/replace only processes `<a href="">` tags
- **Images excluded** - `<img src="">` shown separately for reference
- **Content areas only** - Excludes navigation, headers, footers
- **Tracking filtered** - Removes analytics/tracking pixels automatically

### **Flexible Targeting**
- **Global replacement** - Replace URL across all posts
- **Per-post replacement** - Replace URL in specific post only  
- **Selective application** - Choose exactly which matches to replace
- **Pre-filled searches** - Click any URL to auto-fill find/replace

### **Rich Context Display**
- **Link text** - Shows clickable text for each URL
- **Surrounding context** - Text around the link for understanding
- **Post identification** - Shows which post each URL appears in
- **One-click copying** - Copy any URL to clipboard instantly

## 📊 WordPress Import

### **Generated Output**
- **Valid WXR format** - WordPress eXtended RSS 1.2
- **Published posts** - All content imported as published
- **CDATA sections** - Proper HTML content encoding
- **Full metadata** - Categories, tags, dates, slugs preserved

### **Import Process**
1. WordPress Admin → Tools → Import → WordPress
2. Choose your `wordpress_import.xml` file
3. Assign author and import attachments as desired
4. Run the import

## 🧪 Testing & Quality

### **Code Quality**
```bash
# Run linter  
venv\Scripts\ruff.exe check . --exclude=venv

# Auto-fix issues
venv\Scripts\ruff.exe check --fix . --exclude=venv
```

### **Testing Approach**
1. **Edit config/urls.txt** - Add 2-3 URLs for testing
2. **Test extraction** - Run any of the 3 extraction methods
3. **Check output/** - Verify generated XML files
4. **WordPress import** - Test the generated XML in WordPress

### **Latest Test Results** 
- ✅ **11/11 URLs extracted** - 100% success rate with Park Ford dealership URLs
- ✅ **Type checking** - All BeautifulSoup issues resolved with proper type stubs
- ✅ **Code quality** - All Ruff linting issues fixed
- ✅ **All methods working** - Web interface, command line, and browser automation

---

# Important Instructions for Claude Code

## ✅ WELL-ORGANIZED: Current Architecture

The codebase is now well-structured and ready for feature development:

### **Current State**
- `modern_app.py` is 1247 lines with clean Flask structure
- Frontend assets properly separated into templates/ and static/
- Organized directory structure with clear separation of concerns
- Professional Flask project layout

### **Completed Organization**

#### **✅ Static Assets Separated** 
- CSS properly organized in `static/css/main.css`
- JavaScript modules in `static/js/` directory
- HTML templates in `templates/` using Jinja2

#### **✅ Proper Directory Structure**
- `extractors/` - Content extraction methods
- `config/` - Configuration files and settings
- `output/` - Generated WordPress XML files
- `static/` and `templates/` - Frontend assets

#### **✅ Clean Architecture**
- Proper Flask project structure
- Separated concerns between extraction, web interface, and configuration
- Type-safe code with proper stubs

## Current Development Guidelines

### **Project Status**
- **Fully functional and maintainable** - All features work with clean code structure
- **Modern extraction** - Uses newspaper3k/trafilatura libraries  
- **Professional UI** - Excellent user experience with well-organized code
- **Ready for development** - Clean structure ready for new features

### **Development Approach**
- **Add features confidently** - Well-structured codebase supports new development
- **Maintain functionality** - All current features continue working perfectly
- **Test thoroughly** - 11/11 URL extraction success rate verified
- **Follow established patterns** - Use the clean Flask structure already in place

### **Code Standards**
- **Linting required** - Always run `ruff check` before changes
- **Separation of concerns** - HTML, CSS, JS, and Python in separate files
- **Flask best practices** - Use templates, static files, and proper structure
- **No inline code** - No HTML/CSS/JS embedded in Python strings