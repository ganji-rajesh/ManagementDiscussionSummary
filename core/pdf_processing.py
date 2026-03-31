"""
pdf_processing.py

Handles physical manipulation of PDF documents using PyMuPDF.
Includes text extraction with caching for performance and byte-splitting
so users can download specific sub-sections of the annual report.
"""

import fitz  # PyMuPDF
import streamlit as st
import io
import logging

logger = logging.getLogger(__name__)

def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """
    Returns the total number of pages in a PDF document.
    
    Args:
        pdf_bytes (bytes): The raw bytes of the PDF document.
        
    Returns:
        int: Total page count.
        
    Raises:
        RuntimeError: If the PDF cannot be opened.
    """
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return len(doc)
    except Exception as e:
        logger.error(f"Error reading PDF page count: {e}")
        raise RuntimeError(f"Failed to read PDF: {e}")
    finally:
        if doc is not None:
            doc.close()

@st.cache_data(show_spinner="Extracting text from PDF...")
def extract_text_from_pdf(pdf_bytes: bytes, start_page: int, end_page: int) -> str:
    """
    Extracts text from a specified page range within a PDF.
    Wrapped in Streamlit's cache_data to avoid re-extraction on page refreshes.
    
    Args:
        pdf_bytes (bytes): The raw bytes of the uploaded PDF document.
        start_page (int): 1-indexed start page.
        end_page (int): 1-indexed end page.
        
    Returns:
        str: Cleaned extracted text.
    """
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # PyMuPDF is 0-indexed, UI is 1-indexed
        start_idx = max(0, start_page - 1)
        end_idx = min(len(doc) - 1, end_page - 1)
        
        text_content = []
        for i in range(start_idx, end_idx + 1):
            page = doc.load_page(i)
            
            # Extract text using blocks for better structure
            blocks = page.get_text("blocks", sort=True)
            
            # Sort blocks to handle multi-column layouts properly:
            # Group by approximate Y-axis (round to nearest 10), then sort by X-axis
            blocks = sorted(blocks, key=lambda b: (round(b[1] / 10) * 10, b[0]))
            
            # Extract only text blocks (type 0) and ignore empty strings
            page_text = [block[4].strip() for block in blocks if block[6] == 0 and block[4].strip()]
            
            if page_text:
                text_content.append("\n\n".join(page_text))
            
        return "\n\n".join(text_content).strip()
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        raise RuntimeError(f"Failed to process PDF text: {e}")
    finally:
        if doc is not None:
            doc.close()

@st.cache_data(show_spinner="Splitting PDF...")
def split_pdf_to_bytes(pdf_bytes: bytes, start_page: int, end_page: int) -> bytes:
    """
    Extracts a sub-document from the original PDF and returns it as a byte stream.
    Used for creating downloadable 'Active Source' PDFs.
    
    Args:
        pdf_bytes (bytes): The raw bytes of the uploaded PDF document.
        start_page (int): 1-indexed start page.
        end_page (int): 1-indexed end page.
        
    Returns:
        bytes: The byte representation of the sliced PDF.
    """
    source_doc = None
    target_doc = None
    try:
        source_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        target_doc = fitz.open()  # New empty PDF
        
        start_idx = max(0, start_page - 1)
        end_idx = min(len(source_doc) - 1, end_page - 1)
        
        # Insert the range of pages into the new document
        target_doc.insert_pdf(source_doc, from_page=start_idx, to_page=end_idx)
        
        # Save to a byte stream
        pdf_stream = io.BytesIO()
        target_doc.save(pdf_stream)
        
        return pdf_stream.getvalue()
    except Exception as e:
        logger.error(f"Error splitting PDF: {e}")
        raise RuntimeError(f"Failed to slice PDF file: {e}")
    finally:
        if target_doc is not None:
            target_doc.close()
        if source_doc is not None:
            source_doc.close()
