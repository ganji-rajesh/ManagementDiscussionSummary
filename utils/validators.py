"""
validators.py

Input validation utilities for the Annual Report Workspace.
Ensures data integrity for file uploads, API keys, and page boundaries.
"""

from typing import Tuple

def validate_pdf_format(file_name: str, file_size_bytes: int, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    Validates if the uploaded file is a PDF and within the size limits.
    """
    if not file_name.lower().endswith('.pdf'):
        return False, "Invalid file format. Please upload a PDF file."
    
    max_bytes = max_size_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        return False, f"File size exceeds the {max_size_mb}MB limit."
        
    return True, ""

def validate_api_key(api_key: str, provider: str = "gemini") -> Tuple[bool, str]:
    """
    Validates the format of the provided API key.
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty."
        
    if provider.lower() == "gemini":
        # Basic check for typical Gemini API key format (often starts with AIza)
        if len(api_key) < 30:
            return False, "Invalid Gemini API key format. Key is too short."
        if not api_key.startswith("AIza"):
            return False, "Invalid Gemini API key format. Ensure it is copied correctly."
            
    return True, ""

def validate_page_bounds(start_page: int, end_page: int, total_pages: int) -> Tuple[bool, str]:
    """
    Validates that the selected page bounds are logical and within the document range.
    """
    if start_page < 1:
        return False, "Start page must be at least 1."
        
    if end_page > total_pages:
        return False, f"End page ({end_page}) cannot exceed total pages ({total_pages})."
        
    if start_page > end_page:
        return False, "Start page cannot be greater than end page."
        
    return True, ""

def validate_source_name(name: str, existing_names: list[str]) -> Tuple[bool, str]:
    """
    Validates the custom source name for uniqueness and valid characters.
    """
    if not name or not name.strip():
        return False, "Source name cannot be empty."
        
    clean_name = name.strip()
    if clean_name in existing_names:
        return False, f"Source name '{clean_name}' already exists. Please choose a unique name."
        
    if len(clean_name) > 50:
        return False, "Source name is too long (maximum 50 characters)."
        
    return True, ""
