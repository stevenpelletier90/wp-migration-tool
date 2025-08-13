# WordPress Blog Migration Tool

A streamlined Python tool for extracting blog metadata and content from websites and generating WordPress WXR import files with an advanced web interface.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Current Project Status

**✅ Fully Functional** - Modern web interface with advanced content extraction
**✅ Smart URL Management** - Separate hyperlinks from images with context
**✅ Selective Find & Replace** - Choose exactly which URLs to modify
**✅ Modern Content Extraction** - Using newspaper3k and trafilatura libraries
**✅ Clean UI/UX** - Professional interface with copy functionality

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Install dependencies
venv\Scripts\pip.exe install -r requirements.txt
```

### 2. Run the Modern Web Interface
```bash
venv\Scripts\python.exe modern_app.py
```
**Access:** `http://localhost:5000/`

### 3. Basic Workflow
1. **Add URLs** - Paste your blog post URLs (one per line)
2. **Start Migration** - Extract content with modern libraries
3. **Show URLs** - Review hyperlinks vs images with full context
4. **Find & Replace** - Selectively modify URLs with preview
5. **Download XML** - Get your WordPress import file

## 📁 Current Project Structure

```
C:\Users\steve\Downloads\test\
├── modern_app.py                 # Main Flask application (⚠️ NEEDS REFACTORING)
├── modern_extractor.py          # Modern content extraction (newspaper3k/trafilatura)
├── CLAUDE.md                    # This documentation
├── requirements.txt             # Dependencies
├── urls.txt                     # URL source file
└── venv/                        # Virtual environment
```

**⚠️ URGENT: Code needs refactoring - modern_app.py is 2000+ lines with mixed HTML/CSS/JS**

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

### **Standard Workflow**
```
1. Add URLs (paste blog post URLs)
   ↓
2. Start Migration (extract with modern libraries)  
   ↓
3. Show All URLs (review hyperlinks vs images)
   ↓
4. Find & Replace URLs (optional - global or per-post)
   ↓
5. Download WordPress XML
```

### **URL Management Options**
- **📋 Copy URLs** - One-click copying with toast feedback
- **🔧 Global Replace** - Modify URL across all posts  
- **📝 Per-Post Replace** - Modify URL in specific post only
- **🖼️ Image Reference** - Images shown separately (copy-only)

## 🛠️ Current Technical Architecture

### **Frontend (⚠️ NEEDS SEPARATION)**
- **Inline HTML** - All HTML embedded in Python strings
- **Inline CSS** - Styling mixed with HTML
- **Inline JavaScript** - Functions embedded in HTML
- **Bootstrap 5.3.7** - Professional UI components
- **HTMX 2.0.6** - Dynamic interactions
- **Alpine.js 3.14.9** - Reactive components

### **Backend** 
- **Flask application** - `modern_app.py` (2000+ lines, needs refactoring)
- **Modern extraction** - `modern_extractor.py` with newspaper3k/trafilatura  
- **Session-based storage** - In-memory data handling
- **BeautifulSoup parsing** - HTML/XML processing

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

### **URL Source** (`urls.txt`)
```
# WordPress Migration URLs - Add your blog post URLs below
https://example.com/blog/2023/january/01/post-title.htm
https://example.com/blog/2023/january/02/another-post.htm
```

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
1. **Single URL test** - Always test with one URL first
2. **Check URL separation** - Verify hyperlinks vs images display correctly
3. **Test find/replace** - Ensure only hyperlinks are processed
4. **WordPress import** - Test the generated XML in WordPress

---

# Important Instructions for Claude Code

## 🚨 CRITICAL: Refactoring Priority

**BEFORE making any feature changes, the codebase MUST be refactored:**

### **Current State**
- `modern_app.py` is 2000+ lines with mixed HTML/CSS/JavaScript
- All frontend code is embedded in Python strings
- Single file contains routes, business logic, templates, and assets
- Unmaintainable and error-prone

### **Required Refactoring Steps**

#### **Step 1: Extract Static Assets** 
```bash
mkdir -p static/css static/js templates
# Move CSS to static/css/main.css
# Move JavaScript to static/js/main.js  
# Create HTML templates in templates/
```

#### **Step 2: Separate Routes and Logic**
- Extract route handlers to separate modules
- Create service layer for business logic
- Use Flask templates instead of string concatenation
- Proper Flask project structure

#### **Step 3: Template System**
- Convert inline HTML to Jinja2 templates
- Use template inheritance for consistency  
- Separate partials for reusable components

## Current Development Guidelines

### **Project Status**
- **Functional but unmaintainable** - All features work but code structure is poor
- **Modern extraction** - Uses newspaper3k/trafilatura libraries  
- **Professional UI** - Good user experience but poor code organization
- **Needs immediate refactoring** - Cannot add features until structure is fixed

### **Development Approach**
- **REFACTOR FIRST** - Do not add features until code is properly structured
- **Maintain functionality** - All current features must continue working
- **Test thoroughly** - Verify nothing breaks during refactoring
- **Use proper Flask patterns** - Templates, static files, blueprints

### **Code Standards**
- **Linting required** - Always run `ruff check` before changes
- **Separation of concerns** - HTML, CSS, JS, and Python in separate files
- **Flask best practices** - Use templates, static files, and proper structure
- **No inline code** - No HTML/CSS/JS embedded in Python strings