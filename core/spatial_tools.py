"""
spatial_tools.py

Contains heuristics and bounding-box spatial logic for analyzing complex PDF layouts.
Includes experimental Table of Contents parsing and general structure math.
"""

import fitz
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def parse_table_of_contents(pdf_bytes: bytes, scan_pages: int = 15) -> List[Dict[str, int]]:
    """
    Attempts to heuristically locate and parse a Table of Contents (TOC)
    by looking for common TOC patterns (e.g., "Management Discussion .... 24")
    within the first few pages of an annual report.
    
    Args:
        pdf_bytes (bytes): Raw PDF document bytes.
        scan_pages (int): Number of pages from the beginning to scan for a TOC.
        
    Returns:
        List[Dict]: Discovered sections, e.g., [{"title": "MD&A", "page": 24}]
    """
    discovered_sections = []
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_to_scan = min(scan_pages, len(doc))
        
        # Heuristic regex looking for words followed by dots and a number
        # e.g., "Risk Factors ............. 12"
        toc_pattern = re.compile(r"([A-Za-z\s&,-]+?)[\.\s_]*?(\d+)$")
        
        for i in range(pages_to_scan):
            page = doc.load_page(i)
            blocks = page.get_text("blocks")
            
            for block in blocks:
                # Block text is in the 5th tuple item in PyMuPDF (index 4)
                text = block[4].strip()
                for line in text.split('\n'):
                    match = toc_pattern.search(line)
                    if match:
                        title = match.group(1).strip()
                        page_num = int(match.group(2))
                        
                        # Filter out noise
                        if 3 < len(title) < 60 and page_num < len(doc):
                            discovered_sections.append({
                                "title": title,
                                "page": page_num
                            })
                            
        doc.close()
        return discovered_sections
    except Exception as e:
        logger.warning(f"Could not heuristically parse TOC: {e}")
        return []
