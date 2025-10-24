"""
Annual Report Text Extraction and Summarization with Gemini AI
Streamlit Application with User-Confirmed Page Detection
"""

import os
import tempfile
from typing import Optional, Tuple, List
import streamlit as st
import google.generativeai as genai
import pymupdf  # PyMuPDF

# Import the new extraction function
from pdf_extraction_tools1 import extract_pdf_content


# Page configuration
st.set_page_config(
    page_title="MDA Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_automatic_page_numbers(pdf_path: str) -> Tuple[bool, dict, str]:
    """
    Extract page numbers from PDF for user confirmation.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Tuple of (success, numbers_dict, message)
    """
    try:
        # Use the new extract_pdf_content function
        result = extract_pdf_content(
            pdf_path,
            target_phrases=["management discussion and analysis", "corporate"]
        )
        
        if not result['success']:
            return False, {}, f"❌ {result.get('message', 'Could not find target phrases in PDF')}"
        
        # Extract all candidate page numbers
        toc_page = result['table_of_content']
        
        # Get all page number numbers from the result
        # mda_starting_page_numbers contains: [(page_num, distance), ...]
        # mda_ending_page_numbers contains: [(page_num, distance), ...]
        
        starting_numbers = result.get('mda_starting_page_numbers', [])
        ending_numbers = result.get('mda_ending_page_numbers', [])
        
        numbers = {
            'table_of_content_page': toc_page,
            'starting_pages': starting_numbers,  # List of (page, distance) tuples
            'ending_pages': ending_numbers,      # List of (page, distance) tuples
            'found_phrases': result.get('found_phrases', [])
        }
        
        return True, numbers, f"✅ Table of contents page {toc_page}"
        
    except Exception as e:
        return False, {}, f"❌ Error during page detection: {str(e)}"


# def extract_text_from_pdf(
#     pdf_file,
#     start_page: int,
#     end_page: int
# ) -> tuple[str, str]:
def extract_text_from_pdf(
    pdf_file,
    start_page: int,
    end_page: int,
    toc_page: int  # NEW PARAMETER
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
        
        # for idx, page_num in enumerate(range(start_page - 1, end_page)):
        # NEW CODE:
        for idx, page_num in enumerate(range(start_page + toc_page - 1, end_page + toc_page)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text.append(page_text)
            
            # Update progress
            progress = (idx + 1) / (end_page - start_page + 1)
            progress_bar.progress(progress)
        
        doc.close()
        os.unlink(tmp_path)
        
        extracted_text = '\\n'.join(all_text)
        return extracted_text, ""
    
    except Exception as e:
        return "", f"Error extracting text: {str(e)}"


def summarize_with_gemini(
    text: str,
    api_key: str,
    model_name: str = "gemini-2.0-flash-exp"
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
        prompt = f"""Please provide a comprehensive summary of the following \\
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
    st.title("📄 MDA Summarizer")
    st.markdown(
        "Extract and summarize Management Discussion & Analysis "
        "sections from annual reports using Google Gemini AI"
    )
    st.divider()
    
    # Initialize session state
    if 'detection_mode' not in st.session_state:
        st.session_state.detection_mode = "Automatic"
    if 'numbers' not in st.session_state:
        st.session_state.numbers = None
    if 'detection_complete' not in st.session_state:
        st.session_state.detection_complete = False
    
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
                "gemini-2.0-flash-exp",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
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
        
        st.divider()
        
        # Page detection mode
        st.header("📖 Page Detection")
        
        # Detection mode selection
        detection_mode = st.radio(
            "Detection Mode",
            options=["Automatic", "Manual"],
            index=0,
            help="Choose automatic detection with confirmation or manually specify page range"
        )
        
        st.session_state.detection_mode = detection_mode
        
        # Manual mode inputs
        if detection_mode == "Manual":
            st.write("")
            col1, col2 = st.columns(2)
            
            with col1:
                manual_start = st.number_input(
                    "Start Page",
                    min_value=1,
                    value=165,
                    step=1,
                    help="First page of MD&A section"
                )
            
            with col2:
                manual_end = st.number_input(
                    "End Page",
                    min_value=1,
                    value=211,
                    step=1,
                    help="Last page of MD&A section"
                )
        
        st.divider()
        
        # Detect pages button (for automatic mode)
        if detection_mode == "Automatic" and uploaded_file:
            detect_button = st.button(
                "🔍 Detect Page Numbers",
                type="secondary",
                use_container_width=True
            )
        else:
            detect_button = False
        
        # Process button
        if detection_mode == "Manual":
            process_enabled = uploaded_file and api_key
        else:
            process_enabled = uploaded_file and api_key and st.session_state.detection_complete
        
        process_button = st.button(
            "🚀 Generate Summary",
            type="primary",
            use_container_width=True,
            disabled=not process_enabled
        )
    
    # Main content area
    if not uploaded_file:
        st.info("👈 Please upload a PDF file from the sidebar to begin")
        
        # Instructions
        with st.expander("📚 How to use this app", expanded=True):
            st.markdown("""
### Getting Started

1. **Get Gemini API Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) 
   to create a free API key
2. **Enter API Key**: Paste your API key in the sidebar
3. **Upload PDF**: Upload your annual report PDF file
4. **Choose Detection Mode**:
   - **Automatic**: AI detects starting and ending pages management discussion section, you confirm them from the selection
   - **Manual**: Specify start and end page numbers directly
5. **Detect Pages** (Automatic mode): Click to find page number numbers
6. **Confirm Pages** (Automatic mode): Review and select the correct page numbers
7. **Generate Summary**: Click to process and summarize

### Automatic Detection with Confirmation

The automatic mode:
- Searches for "Management Discussion and Analysis" in the Table of Contents
- Extracts all nearby page numbers using spatial analysis
- Presents them to you for confirmation
- Uses your confirmed selection for extraction

### Note

Processing may take 30-60 seconds depending on document length.
""")
        return
    
    # Display file info
    st.success(f"✅ File uploaded: **{uploaded_file.name}**")
    
    # Handle page detection button click
    if detect_button:
        # Save file temporarily for page detection
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        with st.spinner("🔍 Detecting page numbers using spatial analysis..."):
            success, numbers, msg = get_automatic_page_numbers(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if success:
            st.session_state.numbers = numbers
            st.session_state.detection_complete = False
            st.success(msg)
        else:
            st.error(msg)
            st.session_state.numbers = None
    
    # Display candidate selection UI if numbers are available
    if st.session_state.numbers and detection_mode == "Automatic":
        st.subheader("📋 Detected Page Number numbers")
        
        numbers = st.session_state.numbers
        
        st.info(f"📍 Found in Table of Contents on page **{numbers['table_of_content_page']}**")
        st.write(f"🔍 Search phrase: **{', '.join(numbers['found_phrases'])}**")
        
        st.divider()
        
        # Create columns for start and end page selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 📖 Starting Page numbers")
            
            starting_pages = numbers['starting_pages']
            if starting_pages:
                # Create options list with page numbers and distances
                start_options = []
                for page_num, distance in starting_pages[:10]:  # Show top 10 numbers
                    start_options.append(f"Page {int(page_num)} (distance: {distance:.1f})")
                
                selected_start_option = st.radio(
                    "Select starting page:",
                    options=start_options,
                    index=0,
                    key="start_page_selection"
                )
                
                # Extract the selected page number
                confirmed_start = int(selected_start_option.split()[1])
            else:
                st.warning("No starting page numbers found")
                confirmed_start = None
        
        with col2:
            st.write("### 📖 Ending Page numbers")
            
            ending_pages = numbers['ending_pages']
            if ending_pages:
                # Create options list
                end_options = []
                for page_num, distance in ending_pages[:5]:  # Show top 5 numbers
                    end_options.append(f"Page {int(page_num)} (distance: {distance:.1f})")
                
                selected_end_option = st.radio(
                    "Select ending page:",
                    options=end_options,
                    index=0,
                    key="end_page_selection"
                )
                
                # Extract the selected page number
                confirmed_end = int(selected_end_option.split()[1])
            else:
                st.warning("No ending page numbers found")
                confirmed_end = None
        
        st.divider()
        
        # Confirm button
        if confirmed_start and confirmed_end:
            if st.button("✅ Confirm Page Selection", type="primary", use_container_width=True):
                st.session_state.confirmed_start_page = confirmed_start
                st.session_state.confirmed_end_page = confirmed_end
                st.session_state.detection_complete = True
                st.success(f"✅ Confirmed: Pages {confirmed_start} to {confirmed_end}")
                st.rerun()
        
        # Show confirmed pages if available
        if st.session_state.detection_complete:
            st.success(
                f"✅ **Confirmed Page Range:** {st.session_state.confirmed_start_page} "
                f"to {st.session_state.confirmed_end_page}"
            )
    
    # Process when Generate Summary button clicked
    if process_button:
        # Validation
        if not api_key:
            st.error("❌ Please enter your Gemini API key in the sidebar")
            return
        
        # Determine page range based on mode
        if detection_mode == "Manual":
            start_page = manual_start
            end_page = manual_end
            
            if start_page > end_page:
                st.error("❌ Start page must be less than or equal to end page")
                return
        else:
            # Automatic mode - use confirmed pages
            start_page = st.session_state.confirmed_start_page
            end_page = st.session_state.confirmed_end_page
            toc_page = st.session_state.numbers['table_of_content_page']
        
        st.info(f"📄 Extracting pages: **{start_page} to {end_page}**")
        
        # Step 1: Extract text
        with st.spinner("📖 Extracting text from PDF..."):
            extracted_text, error = extract_text_from_pdf(
                uploaded_file,
                start_page,
                end_page,
                toc_page
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
                disabled=False
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



