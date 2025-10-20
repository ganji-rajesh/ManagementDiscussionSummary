# Annual Report Summarizer - Documentation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [Deployment](#deployment)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

***

## Overview

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

## Architecture

### System Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit App  │
│   (Frontend)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ PyMuPDF │ │ Gemini API   │
│  (PDF)  │ │ (Summary)    │
└─────────┘ └──────────────┘
```

### Component Diagram

```python
app.py
├── main()                      # Application entry point
├── extract_text_from_pdf()     # PDF processing module
├── summarize_with_gemini()     # AI summarization module
└── Streamlit UI Components     # Interface elements
```

### Data Flow

1. **Input Phase**
   - User uploads PDF file
   - User specifies page range (start/end)
   - User provides Gemini API key
   - User selects AI model

2. **Processing Phase**
   - PDF saved to temporary file
   - Text extracted page-by-page with progress tracking
   - Extracted text validated

3. **Summarization Phase**
   - Gemini API configured with user key
   - Prompt generated with context
   - AI model processes text
   - Summary returned

4. **Output Phase**
   - Summary displayed in markdown
   - Download option provided
   - Cleanup of temporary files

***

## Installation

### Prerequisites

```bash
# System Requirements
- Python 3.8 or higher
- pip package manager
- Internet connection (for Gemini API)
- 2GB RAM minimum
- Web browser (Chrome, Firefox, Safari, Edge)
```

### Local Installation

#### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/annual-report-summarizer.git
cd annual-report-summarizer
```

#### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Run Application
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

***

## Configuration

### Environment Variables (Optional)

For development/testing, you can pre-configure the API key:

```bash
# .env file (DO NOT commit to Git)
GEMINI_API_KEY=your_api_key_here
```

### Streamlit Configuration

Create `.streamlit/config.toml` for custom settings:

```toml
[server]
maxUploadSize = 200
enableXsrfProtection = true

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### Model Configuration

Available Gemini models (configurable in app):
- `gemini-2.5-flash` - Fast, cost-effective (recommended)
- `gemini-2.5-pro` - Best quality, slower
- `gemini-2.0-flash` - Balanced performance
- `gemini-pro-latest` - Latest stable version

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

## API Reference

### Core Functions

#### `extract_text_from_pdf(pdf_file, start_page, end_page)`

Extracts text from specified page range in uploaded PDF.

**Parameters**:
- `pdf_file` (UploadedFile): Streamlit file upload object
- `start_page` (int): Starting page number (1-based, inclusive)
- `end_page` (int): Ending page number (1-based, inclusive)

**Returns**:
- `tuple[str, str]`: (extracted_text, error_message)
  - `extracted_text`: Full text content or empty string
  - `error_message`: Error description or empty string

**Behavior**:
1. Saves uploaded file to temporary location
2. Opens PDF using PyMuPDF
3. Validates page range against document
4. Extracts text page-by-page with progress tracking
5. Cleans up temporary file
6. Returns concatenated text with newlines

**Error Handling**:
- Invalid page range: Returns error message
- Page exceeds document: Auto-adjusts with warning
- File access error: Returns exception message

**Example**:
```python
text, error = extract_text_from_pdf(uploaded_file, 131, 180)
if error:
    st.error(f"Extraction failed: {error}")
else:
    st.success(f"Extracted {len(text)} characters")
```

***

#### `summarize_with_gemini(text, api_key, model_name)`

Generates comprehensive summary using Google Gemini API.

**Parameters**:
- `text` (str): Text content to summarize
- `api_key` (str): Google Gemini API authentication key
- `model_name` (str): Gemini model identifier (default: "gemini-2.5-flash")

**Returns**:
- `tuple[str, str]`: (summary, error_message)
  - `summary`: Generated summary text or empty string
  - `error_message`: Error description or empty string

**Prompt Structure**:
```
Focus on:
- Key business insights and industry trends
- Financial performance highlights
- Major risks and concerns
- Strategic opportunities
- Future outlook and projections
```

**API Configuration**:
```python
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name)
response = model.generate_content(prompt)
```

**Error Handling**:
- Empty text: Validation error
- Invalid API key: Authentication error
- Rate limiting: API error with retry suggestion
- Network issues: Connection error

**Example**:
```python
summary, error = summarize_with_gemini(
    text="Long document text...",
    api_key="your_api_key",
    model_name="gemini-2.5-flash"
)
```

***

#### `main()`

Main application entry point and UI orchestration.

**Responsibilities**:
1. Page configuration
2. Sidebar input collection
3. File upload handling
4. Validation logic
5. Extraction orchestration
6. Summarization orchestration
7. Result display
8. Error presentation

**UI Components**:
- Header and description
- Sidebar configuration panel
- File uploader
- Number inputs (page range)
- Model selector
- Action button
- Status messages
- Result display
- Download button

**Execution Flow**:
```python
if __name__ == "__main__":
    main()
```

***

## Deployment

### Streamlit Community Cloud (Recommended)

#### Prerequisites
- GitHub account
- Streamlit Community Cloud account (free)
- Repository with code pushed

#### Step-by-Step Deployment

**1. Prepare Repository**

Ensure your repository contains:
```
your-repo/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

**2. Push to GitHub**
```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

**3. Deploy on Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click "New app"
3. Select your repository
4. Choose branch: `main`
5. Main file path: `app.py`
6. Click "Deploy"

**4. Application URL**

Your app will be available at:
```
https://your-username-annual-report-summarizer.streamlit.app
```

#### Deployment Configuration

**requirements.txt**:
```txt
streamlit==1.39.0
google-generativeai==0.8.3
pymupdf==1.24.13
```

**.gitignore**:
```
__pycache__/
*.py[cod]
.env
.streamlit/secrets.toml
*.pdf
.vscode/
```

***

### Alternative Deployment Options

#### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and Run**:
```bash
docker build -t annual-report-summarizer .
docker run -p 8501:8501 annual-report-summarizer
```

#### Heroku Deployment

**Procfile**:
```
web: sh setup.sh && streamlit run app.py
```

**setup.sh**:
```bash
mkdir -p ~/.streamlit/
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml
```

***

## Security

### Best Practices

#### 1. API Key Management

**Never commit API keys to Git**:
```bash
# Add to .gitignore
.env
.streamlit/secrets.toml
config.py
```

**Use Streamlit Secrets** (for deployment):
```toml
# .streamlit/secrets.toml (local only)
GEMINI_API_KEY = "your_key_here"
```

Access in code:
```python
api_key = st.secrets["GEMINI_API_KEY"]
```

#### 2. Input Validation

The application validates:
- Page range logic (start ≤ end)
- Page numbers against document length
- API key presence
- Text content non-empty

#### 3. File Handling

- Temporary files created with `tempfile.NamedTemporaryFile`
- Files deleted after processing with `os.unlink()`
- No persistent storage of uploaded PDFs

#### 4. Data Privacy

**User Data**:
- API keys entered per session (not stored)
- Uploaded PDFs processed in memory
- No data logged or persisted

**Third-Party Data Sharing**:
- Text sent to Google Gemini API for summarization
- Subject to [Google's Privacy Policy](https://policies.google.com/privacy)

#### 5. Rate Limiting

**Gemini API Limits** (Free Tier):
- 60 requests per minute
- 1500 requests per day

**Recommendation**: Implement caching for repeated summaries

***

## Troubleshooting

### Common Issues

#### 1. Model Not Found (404 Error)

**Error Message**:
```
404 models/gemini-1.5-pro is not found for API version v1beta
```

**Solution**:
Use updated model names:
- ✅ `gemini-2.5-flash`
- ✅ `gemini-2.5-pro`
- ❌ `gemini-1.5-pro` (deprecated)

#### 2. API Key Invalid

**Error Message**:
```
Error generating summary: Invalid API key
```

**Solution**:
1. Verify API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Check for extra spaces when copying
3. Ensure API key has Gemini API access enabled

#### 3. PDF Text Extraction Failed

**Error Message**:
```
Error extracting text: [Errno 2] No such file or directory
```

**Solution**:
- Ensure PDF is properly uploaded
- Check file isn't corrupted
- Verify file size < 200MB
- Try re-uploading

#### 4. Empty Summary

**Cause**: Text might be from scanned images (not selectable text)

**Solution**:
1. Check "View Extracted Text" - if empty, PDF needs OCR
2. Use PDF with selectable text
3. Or preprocess with OCR tool (Tesseract)

#### 5. Slow Performance

**Symptoms**: Processing takes > 2 minutes

**Solutions**:
- Use `gemini-2.5-flash` instead of `gemini-2.5-pro`
- Reduce page range if possible
- Check internet connection speed
- Verify API quota not exceeded



## Performance Optimization

### Best Practices

#### 1. Caching (Future Enhancement)

```python
@st.cache_data(ttl=3600)
def extract_text_from_pdf_cached(pdf_hash, start_page, end_page):
    # Cache extracted text for 1 hour
    pass
```

#### 2. Chunking Large Documents

For documents > 50 pages:
```python
def chunk_text(text, max_chars=30000):
    chunks = []
    while len(text) > max_chars:
        chunks.append(text[:max_chars])
        text = text[max_chars:]
    chunks.append(text)
    return chunks
```

#### 3. Async Processing (Future)

Process extraction and summarization in parallel using `asyncio`.

***

## Contributing

### Development Workflow

1. **Fork Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow PEP 8 style guide
   - Add docstrings to functions
   - Include type hints

4. **Test Changes**
   ```bash
   # Run locally
   streamlit run app.py
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Standards

**Python Style**: PEP 8
**Docstring Format**: Google style
**Type Hints**: Required for all functions
**Line Length**: 79 characters max

### Testing Checklist

- [ ] PDF upload works
- [ ] Page range validation correct
- [ ] Text extraction successful
- [ ] Gemini API integration functional
- [ ] Error messages clear
- [ ] Download works
- [ ] Mobile responsive (basic)

***

## FAQ

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

***

## Changelog

### v1.0.0 (October 2025)
- Initial release
- PDF text extraction with PyMuPDF
- Gemini AI summarization
- Streamlit web interface
- Multi-model support
- Download functionality
- Progress tracking
- Error handling

***

## License

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

***

## Support & Contact


**Author**: [Ganji Rajesh]

**Version**: 1.0.0

**Last Updated**: October 20, 2025

***

## Acknowledgments

- **Streamlit** - Web framework
- **Google Gemini** - AI summarization
- **PyMuPDF** - PDF processing
***
