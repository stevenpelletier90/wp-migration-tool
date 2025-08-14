# WordPress Migration Tool - Project Structure

## 📁 Directory Organization

### **Root Directory**
- `modern_app.py` - **Main Flask Web Application** (2000+ lines, needs refactoring)
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `CLAUDE.md` - Project documentation and Claude Code instructions

### **📂 /extractors** - Content Extraction Methods
- `modern_extractor.py` - **Fast extractor** using newspaper3k/trafilatura libraries
- `browser_scraper.py` - **Browser automation** for JavaScript-heavy sites
- `fixed_extractor.py` - XML generation utilities (used by browser_scraper)

### **📂 /config** - Configuration Files
- `urls.txt` - **URL source file** (edit this to add your blog URLs)
- `chromedriver.exe` - ChromeDriver for browser automation

### **📂 /static** - Web Interface Assets
- `/css/main.css` - Extracted CSS styles
- `/js/` - JavaScript modules:
  - `app-init.js` - Application initialization
  - `clipboard.js` - Copy functionality
  - `find-replace.js` - Find/replace modal
  - `global-find-replace.js` - Global find/replace
  - `main.js` - Main application logic
  - `url-management.js` - URL list management

### **📂 /templates** - HTML Templates
- `index.html` - Main web interface template

### **📂 /output** - Generated Files (Auto-created)
- `modern_export.xml` - Output from modern_extractor.py
- `test_output.xml` - Output from test.py
- `wordpress_import.xml` - Final WordPress import file
- `test_output.json` - Debug JSON from test script
- `wordpress_import.json` - Debug JSON output

### **📂 /venv** - Python Virtual Environment
- Contains all installed Python dependencies

---

## 🚀 Usage Methods

### **Method 1: Modern Web Interface (Recommended)**
```bash
# Start web interface
venv\Scripts\python.exe modern_app.py

# Access: http://localhost:5000/
# Features: Modern UI, URL management, find/replace, download XML
```

### **Method 2: Fast Extraction**
```bash
# Quick extraction using newspaper3k/trafilatura
venv\Scripts\python.exe extractors\modern_extractor.py

# Uses: config/urls.txt
# Output: output/modern_export.xml
```

### **Method 3: Browser Automation**
```bash
# Browser scraping for JavaScript-heavy sites
venv\Scripts\python.exe extractors\browser_scraper.py

# Uses: config/urls.txt, config/chromedriver.exe
# Output: output/wordpress_import.xml
```

### **Testing**
```bash
# To test with fewer URLs:
# 1. Edit config/urls.txt to include only 2-3 URLs
# 2. Run any of the above methods
# 3. Check output/ directory for results
```

---

## 📋 Workflow

### **Step 1: Setup URLs**
1. Edit `config/urls.txt`
2. Add your blog post URLs (one per line)
3. Lines starting with `#` are comments

### **Step 2: Choose Extraction Method**
- **Web Interface**: Best for interactive use, URL management
- **Modern Extractor**: Fast, reliable for most sites
- **Browser Scraper**: For JavaScript-heavy or protected sites
- **Testing**: Just add fewer URLs to config/urls.txt

### **Step 3: Process Results**
- Generated XML files are in `output/` directory
- Import the XML file into WordPress via Tools → Import

---

## 🛠️ File Relationships

### **Dependencies**
- `modern_app.py` → uses `extractors/modern_extractor.py`
- `extractors/browser_scraper.py` → uses `extractors/fixed_extractor.py`

### **Input Files**
- `config/urls.txt` - Used by ALL extraction methods
- `config/chromedriver.exe` - Used by browser-based methods only

### **Output Files**
- All generated files go to `output/` directory
- JSON files are for debugging/inspection
- XML files are for WordPress import

---

## ⚠️ Important Notes

### **Current Issues**
1. **modern_app.py is 2000+ lines** - Needs refactoring into modules
2. **HTML/CSS/JS mixed in Python** - Should be separated into templates/static
3. **Single file architecture** - Should use proper Flask project structure

### **Recommended Usage**
- **For production**: Use Method 1 (Web Interface)
- **For testing**: Use 2-3 URLs in config/urls.txt with any method
- **For problematic sites**: Use Method 3 (Browser Automation)
- **For bulk processing**: Use Method 2 (Fast Extraction)