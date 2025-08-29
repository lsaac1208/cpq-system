# Chinese Font Setup for PDF Generation

## Overview
This directory contains Chinese fonts for proper PDF rendering. The PDF generator supports multiple Chinese font sources with automatic fallback.

## Font Sources (in priority order)

### 1. Local Font Files (Recommended)
Place Chinese font files in this directory:
- `NotoSansSC-Regular.ttf` - Primary choice
- `SourceHanSansSC-Regular.ttf` - Alternative
- `simhei.ttf` - Windows system font alternative

### 2. CDN Fallback (Automatic)
The system automatically falls back to:
- Google Fonts CDN: Noto Sans SC
- jsDelivr CDN: Source Han Sans

### 3. Manual Font Installation

#### Download Noto Sans SC (Recommended)
1. **Manual Download**:
   - Visit: https://fonts.google.com/noto/specimen/Noto+Sans+SC
   - Click "Download family"
   - Extract zip file
   - Copy `NotoSansSC-Regular.ttf` to this directory
   - Verify file size is > 1MB (actual font file)

2. **Command Line** (macOS/Linux):
   ```bash
   # Download from fontsource (reliable)
   curl -L "https://fonts.bunny.net/noto-sans-sc/files/noto-sans-sc-latin-400-normal.ttf" \
        -o "NotoSansSC-Regular.ttf"
   
   # Verify download (should be > 100KB)
   ls -lh NotoSansSC-Regular.ttf
   ```

#### Alternative: Source Han Sans
1. **Manual Download**:
   - Visit: https://github.com/adobe-fonts/source-han-sans/releases
   - Download "SourceHanSansSC.zip"
   - Extract and find "SourceHanSansSC-Regular.otf"
   - Rename to `SourceHanSansSC-Regular.ttf`
   - Place in this directory

2. **Quick Download**:
   ```bash
   # Download a subset font (smaller, faster)
   curl -L "https://cdn.jsdelivr.net/npm/source-han-sans-sc@1.0.0/SourceHanSansSC-Regular.otf" \
        -o "SourceHanSansSC-Regular.ttf"
   ```

#### Verification Steps
After downloading any font:
```bash
# Check file size (should be > 100KB for basic support, > 1MB for full support)
ls -lh *.ttf

# Test in browser console
# Open your app and run: testFontSupport()
```

## Font File Requirements
- Format: TTF (TrueType Font)
- Size: Recommended < 10MB for better performance
- Encoding: Unicode with Chinese character support (U+4E00-U+9FFF range)

## Testing Your Font
After adding a font file, test PDF generation with Chinese text to ensure proper rendering.

## Troubleshooting
- If Chinese characters appear as boxes or garbled text, ensure the font file supports Chinese characters
- Large font files (>10MB) may cause performance issues
- For production use, consider font subsetting to reduce file size

## Performance Optimization
- Font files are cached after first load
- CDN fallback provides automatic caching
- Consider using web font optimization tools for large deployments