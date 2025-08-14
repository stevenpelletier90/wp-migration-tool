# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. **Edit Your URLs**
```bash
# Open and edit this file:
config/urls.txt

# Add your blog post URLs (one per line):
https://example.com/blog/post1.html
https://example.com/blog/post2.html
# Comments start with #
```

### 2. **Choose Your Method**

#### **🌐 Web Interface (Recommended)**
```bash
venv\Scripts\python.exe modern_app.py
# Open: http://localhost:5000
```

#### **⚡ Fast Extraction (newspaper3k/trafilatura)**
```bash
venv\Scripts\python.exe extractors\modern_extractor.py
```

#### **🤖 Browser Automation (For JavaScript-heavy sites)**
```bash
venv\Scripts\python.exe extractors\browser_scraper.py
```

### 3. **Get Your WordPress File**
- Check the `output/` folder
- Import the `.xml` file into WordPress
- Go to WordPress Admin → Tools → Import → WordPress

---

## 📁 What's What

| Directory | Purpose |
|-----------|---------|
| `config/` | Your URLs and settings |
| `extractors/` | Two extraction methods (modern & browser) |
| `output/` | Generated WordPress XML files |
| `static/` & `templates/` | Web interface files |

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "No URLs found" | Edit `config/urls.txt` |
| Browser automation fails | Make sure Chrome is installed |
| Web interface won't start | Run `venv\Scripts\pip.exe install -r requirements.txt` |
| Import fails in WordPress | Check `output/` for the XML file |

---

## 💡 Pro Tips

- **Start with 2-3 URLs** in config/urls.txt to test first
- **Use web interface** for bulk processing with URL management  
- **Use browser automation** for JavaScript-heavy sites
- **Check output folder** for all generated files