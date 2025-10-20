"""
Annual Report Text Extraction and Summarization with Gemini AI
Streamlit Application with Automatic Page Detection
"""

import os
import tempfile
from typing import Optional, Tuple

import streamlit as st
import google.generativeai as genai
import pymupdf

# Import functions from pdf_extraction_tools
from pdf_extraction_tools import (
    get_nth_occurrence_page,
    get_topic_page_number,
    get_word_occurrence_pages
)


# Page configuration
st.set_page_config(
    page_title="Annual Report Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_automatic_page_range(pdf_path: str) -> Tuple[Optional[int], Optional[int], str]:
    """
    Automatically detect the Management Discussion section page range.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Tuple of (start_page, end_page, status_message)
    """
    try:
        # Step 1: Find the contents page (first occurrence of 'content')
        contents_page_no = get_nth_occurrence_page(pdf_path, 'content', 1)
        
        if contents_page_no is None:
            return None, None, "❌ Could not find 'content' page in the PDF"
        
        # Step 2: Find the starting page of "management discussion"
        result = get_topic_page_number(pdf_path, contents_page_no, "management discussion")
        
        if result is None:
            return None, None, f"❌ Could not find 'management discussion' topic on contents page {contents_page_no}"
        
        starting_page = result[0]
        
        # Step 3: Find the ending page (page with "cautionary statement")
        cautionary_pages = get_word_occurrence_pages(pdf_path, "cautionary statement")
        
        if not cautionary_pages:
            return None, None, "❌ Could not find 'cautionary statement' in the PDF"
        
        # Get the second occurrence (index 1) if available, otherwise use the first
        ending_page = cautionary_pages[1] if len(cautionary_pages) > 1 else cautionary_pages[0]
        
        status_msg = f"✅ Auto-detected pages: {starting_page} to {ending_page}"
        return starting_page, ending_page, status_msg
        
    except Exception as e:
        return None, None, f"❌ Error during automatic detection: {str(e)}"


def extract_text_from_pdf(
    pdf_file,
    start_page: int,
    end_page: int
) -> tuple[str, str]:
    """
    Extract text from specific page range in PDF.
    
    Args:
        pdf_file: Uploaded PDF file object
        start_page: Starting page number (1-based indexing)
        end_page: Ending page number (1-based indexing, inclusive)
    
    Returns:
        Tuple of (extracted_text, error_message)
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        # Open PDF
        doc = pymupdf.open(tmp_path)
        
        # Validate page range
        total_pages = len(doc)
        
        if start_page < 1 or end_page < start_page:
            doc.close()
            os.unlink(tmp_path)
            return "", f"Invalid page range: {start_page}-{end_page}"
        
        if end_page > total_pages:
            end_page = total_pages
            st.warning(
                f"End page adjusted to {total_pages} "
                f"(document has {total_pages} pages)"
            )
        
        # Extract text from each page
        all_text = []
        progress_bar = st.progress(0)
        
        for idx, page_num in enumerate(range(start_page - 1, end_page)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text.append(page_text)
            
            # Update progress
            progress = (idx + 1) / (end_page - start_page + 1)
            progress_bar.progress(progress)
        
        doc.close()
        os.unlink(tmp_path)
        
        extracted_text = '\n'.join(all_text)
        return extracted_text, ""
        
    except Exception as e:
        return "", f"Error extracting text: {str(e)}"


def summarize_with_gemini(
    text: str,
    api_key: str,
    model_name: str = "gemini-2.5-flash"
) -> tuple[str, str]:
    """
    Summarize text using Google Gemini API.
    
    Args:
        text: Text to summarize
        api_key: Gemini API key
        model_name: Gemini model name
    
    Returns:
        Tuple of (summary, error_message)
    """
    try:
        if not text or not text.strip():
            return "", "Text to summarize cannot be empty"
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel(model_name)
        
        # Create the prompt
        prompt = f"""Please provide a comprehensive summary of the following \
Management Discussion and Analysis section from an annual report.

Focus on:
- Key business insights and industry trends
- Financial performance highlights
- Major risks and concerns
- Strategic opportunities
- Future outlook and projections

Text to summarize:
{text}
"""
        
        # Generate summary
        response = model.generate_content(prompt)
        
        return response.text, ""
        
    except Exception as e:
        return "", f"Error generating summary: {str(e)}"


def main():
    """Main Streamlit application."""
    
    # Header
    st.title("📄 Annual Report Summarizer")
    st.markdown(
        "Extract and summarize Management Discussion & Analysis "
        "sections from annual reports using Google Gemini AI"
    )
    st.divider()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key. "
                 "Get it from https://aistudio.google.com/app/apikey"
        )
        
        # Model selection
        model_choice = st.selectbox(
            "Select Model",
            options=[
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-pro-latest"
            ],
            help="Choose the Gemini model for summarization"
        )
        
        st.divider()
        
        # File upload
        st.header("📤 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose Annual Report PDF",
            type=['pdf'],
            help="Upload the annual report PDF file"
        )
        
        # Page detection mode
        st.header("📖 Page Detection")
        detection_mode = st.radio(
            "Detection Mode",
            options=["Automatic", "Manual"],
            help="Choose automatic detection or manually specify page range"
        )
        
        # Manual page range inputs (only shown in Manual mode)
        if detection_mode == "Manual":
            col1, col2 = st.columns(2)
            
            with col1:
                start_page = st.number_input(
                    "Start Page",
                    min_value=1,
                    value=165,
                    step=1,
                    help="First page of MD&A section"
                )
            
            with col2:
                end_page = st.number_input(
                    "End Page",
                    min_value=1,
                    value=211,
                    step=1,
                    help="Last page of MD&A section"
                )
        else:
            st.info("📍 Pages will be detected automatically")
            start_page = None
            end_page = None
        
        st.divider()
        
        # Process button
        process_button = st.button(
            "🚀 Generate Summary",
            type="primary",
            use_container_width=True
        )
    
    # Main content area
    if not uploaded_file:
        st.info("👈 Please upload a PDF file from the sidebar to begin")
        
        # Instructions
        with st.expander("📚 How to use this app"):
            st.markdown("""
            1. **Get Gemini API Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) 
               to create a free API key
            2. **Enter API Key**: Paste your API key in the sidebar
            3. **Upload PDF**: Upload your annual report PDF file
            4. **Choose Detection Mode**:
               - **Automatic**: Automatically finds Management Discussion section
               - **Manual**: Specify start and end page numbers
            5. **Select Model**: Choose the appropriate Gemini model
            6. **Generate**: Click "Generate Summary" to process
            
            **Automatic Detection Logic**:
            - Finds the "content" page in the PDF
            - Locates "management discussion" in the table of contents
            - Identifies ending at "cautionary statement"
            
            **Note**: Processing may take 30-60 seconds depending on document length.
            """)
        
        return
    
    # Display file info
    st.success(f"✅ File uploaded: **{uploaded_file.name}**")
    
    # Process when button clicked
    if process_button:
        
        # Validation
        if not api_key:
            st.error("❌ Please enter your Gemini API key in the sidebar")
            return
        
        # Handle automatic or manual page detection
        if detection_mode == "Automatic":
            # Save file temporarily for page detection
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            with st.spinner("🔍 Auto-detecting page range..."):
                start_page, end_page, status_msg = get_automatic_page_range(tmp_path)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Display detection result
            if start_page is None or end_page is None:
                st.error(status_msg)
                st.info("💡 Try using **Manual** mode to specify pages directly")
                return
            else:
                st.success(status_msg)
        else:
            # Manual mode validation
            if start_page > end_page:
                st.error("❌ Start page must be less than or equal to end page")
                return
        
        st.info(f"📄 Extracting pages: **{start_page} to {end_page}**")
        
        # Step 1: Extract text
        with st.spinner("📖 Extracting text from PDF..."):
            extracted_text, error = extract_text_from_pdf(
                uploaded_file,
                start_page,
                end_page
            )
        
        if error:
            st.error(f"❌ {error}")
            return
        
        st.success(
            f"✅ Extracted {len(extracted_text):,} characters "
            f"from {end_page - start_page + 1} pages"
        )
        
        # Display extracted text in expander
        with st.expander("📝 View Extracted Text"):
            st.text_area(
                "Extracted Content",
                extracted_text[:5000] + "..." if len(extracted_text) > 5000 
                else extracted_text,
                height=300,
                disabled=True
            )
        
        # Step 2: Summarize
        with st.spinner(f"🤖 Generating summary with {model_choice}..."):
            summary, error = summarize_with_gemini(
                extracted_text,
                api_key,
                model_choice
            )
        
        if error:
            st.error(f"❌ {error}")
            return
        
        # Display summary
        st.success("✅ Summary generated successfully!")
        st.divider()
        
        st.subheader("📊 Summary")
        st.markdown(summary)
        
        # Download button
        st.download_button(
            label="💾 Download Summary",
            data=summary,
            file_name="annual_report_summary.txt",
            mime="text/plain",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
