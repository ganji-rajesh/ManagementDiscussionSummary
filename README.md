### Description
Annual Report Summarizer is a web-based application built with Streamlit that automates the extraction and summarization of Management Discussion & Analysis (MD&A) sections from corporate annual reports. The application leverages Google's Gemini AI to generate comprehensive, contextual summaries of financial documents.

### Purpose
- Reduce time spent manually reading lengthy annual reports
- Extract key insights from MD&A sections efficiently
- Provide structured, AI-generated summaries focusing on business insights, financial performance, risks, and strategic outlook

### Technology Stack
- **Frontend/UI**: Streamlit 1.39.0
- **PDF Processing**: PyMuPDF 1.24.13
- **AI/ML**: Google Generative AI (Gemini) 0.8.3
- **Language**: Python 3.8+

### Version
**v1.0.0** (October 2025)

***

## Features

### Core Functionality
- **PDF Text Extraction**: Extract text from specified page ranges using PyMuPDF
- **AI Summarization**: Generate comprehensive summaries using Google Gemini models
- **Progress Tracking**: Real-time progress indicators during extraction
- **Multi-Model Support**: Choose from multiple Gemini model variants
- **Preview Capability**: View extracted text before summarization
- **Export Functionality**: Download summaries as text files

### User Interface
- **Responsive Design**: Wide layout optimized for desktop and tablet
- **Sidebar Configuration**: All input controls organized in collapsible sidebar
- **Error Handling**: User-friendly error messages with actionable guidance
- **Help Documentation**: Built-in usage instructions

***


## Usage Guide

### Quick Start

1. **Obtain Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Sign in with Google account
   - Click "Get API key" → "Create API key"
   - Copy the generated key

2. **Launch Application**
   ```bash
   streamlit run app.py
   ```

3. **Configure Application**
   - Enter API key in sidebar (password-protected field)
   - Select desired Gemini model
   - Upload PDF file
   - Specify page range

4. **Generate Summary**
   - Click "Generate Summary" button
   - Wait for processing (30-90 seconds)
   - Review summary
   - Download if needed

### Detailed Workflow

#### 1. Upload PDF Document

**Supported Formats**: PDF only
**Maximum Size**: 200MB
**Recommendation**: Ensure PDF has selectable text (not scanned images)

```python
# File uploaded via Streamlit widget
uploaded_file = st.file_uploader("Choose Annual Report PDF", type=['pdf'])
```

#### 2. Specify Page Range

**Start Page**: First page of MD&A section (1-based indexing)
**End Page**: Last page of MD&A section (inclusive)

**Tips**:
- Most annual reports list page numbers in Table of Contents
- MD&A typically appears after financial highlights
- Common range: 20-80 pages

#### 3. Text Extraction

Progress indicators show:
- Current extraction progress (%)
- Total characters extracted
- Pages processed

**Example Output**:
```
✅ Extracted 45,231 characters from 47 pages
```

#### 4. View Extracted Text (Optional)

Expand "View Extracted Text" section to review:
- First 5,000 characters shown
- Verify text quality before summarization
- Check for OCR errors if applicable

#### 5. Generate Summary

Click "Generate Summary" button to:
- Send text to Gemini API
- Receive structured summary
- Display in formatted markdown

**Processing Time**: 30-90 seconds (varies by document length)

#### 6. Download Summary

Click "Download Summary" button to:
- Save as `.txt` file
- Filename: `annual_report_summary.txt`
- UTF-8 encoding

***


### FAQ

**Q: What file formats are supported?**
A: Currently only PDF files with selectable text. Scanned PDFs require OCR preprocessing.

**Q: Is my data stored anywhere?**
A: No. Files are processed in memory and temporary files are deleted immediately after processing.

**Q: What's the maximum PDF size?**
A: 200MB, but recommended < 50MB for optimal performance.

**Q: Can I summarize multiple PDFs at once?**
A: Not in current version (v1.0). Upload and process one at a time.

**Q: How much does Gemini API cost?**
A: Free tier available with rate limits. See [Google AI Pricing](https://ai.google.dev/pricing) for details.

**Q: Can I use my own AI model?**
A: Code modification required. See `summarize_with_gemini()` function to integrate alternative LLMs.