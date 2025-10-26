"""
PDF Content Extractor Module

Custom extractor to:
- Identify Table of Contents page with robust phrase options:
    [All common versions of 'Management Discussion and Analysis'] AND [Corporate Governance variants]
- Find bbox for 'management discussion and analysis' variants
- Extract all contents from same line and below line (separately)
- Find numbers from each group, calculate distance to phrase, sort ascending
- Output: numbers from same line (starting pages), from below lines (ending pages)

Author: Ganji Rajesh
Version: 1.0.3
"""

from typing import Dict, List, Tuple, Optional, Any
import math
import re

import pymupdf  # PyMuPDF

DEFAULT_MDA_TERMS = [
    "Management Discussion and Analysis",
    "Management Discussion & Analysis",
    "Management Discussion",
    "Management’s Discussion and Analysis",
    "Managements Discussion and Analysis",
    "MANAGEMENT DISCUSSION AND ANALYSIS",
    "MANAGEMENT DISCUSSION",
    "MANAGEMENT'S DISCUSSION AND ANALYSIS",
    "MANAGEMENT’S DISCUSSION & ANALYSIS",
    "MANAGEMENT DISCUSSION AND ANALYSIS",
    "Mgmt Discussion and Analysis",
    "MDA",
]
DEFAULT_Other_TERMS = [
    "Corporate Governance",
    "Report on Corporate Governance",
    "Corporate Governance Report",
    "CORPORATE GOVERNANCE",
    "CORPORATE GOVERNANCE REPORT",
    "Corporate Governance & Reports"
]
DEFAULT_SEARCH_PHRASES = DEFAULT_MDA_TERMS + DEFAULT_Other_TERMS

BELOW_LINE_RANGE = 72  # Points (1 inch)
NUMBER_PATTERN = r'\d+\.?\d*'

def calculate_bbox_center(bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    return (center_x, center_y)

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def extract_numbers_from_text(text: str) -> List[str]:
    numbers = re.findall(NUMBER_PATTERN, text)
    return [num for num in numbers if num]

def _extract_contents_from_page(
    page: pymupdf.Page,
    phrase_bbox: Tuple[float, float, float, float]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    x0, y0, x1, y1 = phrase_bbox
    text_dict = page.get_text("dict")
    same_line_contents = []
    below_line_contents = []
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_bbox = line["bbox"]
            line_y0, line_y1 = line_bbox[1], line_bbox[3]
            # Same line as phrase
            if line_y0 <= y1 and line_y1 >= y0:
                for span in line["spans"]:
                    same_line_contents.append({
                        'text': span['text'],
                        'bbox': span['bbox'],
                        'font': span.get('font', ''),
                        'size': span.get('size', 0)
                    })
            # Below the phrase line (within range)
            elif line_y0 >= y1 and line_y0 <= (y1 + BELOW_LINE_RANGE):
                for span in line["spans"]:
                    below_line_contents.append({
                        'text': span['text'],
                        'bbox': span['bbox'],
                        'font': span.get('font', ''),
                        'size': span.get('size', 0),
                        'y_position': line_y0
                    })
    return same_line_contents, below_line_contents

def _extract_numbers_with_distance(
    contents: List[Dict[str, Any]],
    phrase_bbox: Tuple[float, float, float, float]
) -> List[Dict[str, Any]]:
    phrase_center = calculate_bbox_center(phrase_bbox)
    number_infos = []
    for item in contents:
        numbers = extract_numbers_from_text(item['text'])
        item_center = calculate_bbox_center(item['bbox'])
        distance = calculate_distance(phrase_center, item_center)
        for number in numbers:
            number_infos.append({
                'number': number,
                'text': item['text'],
                'bbox': item['bbox'],
                'center': item_center,
                'distance': distance
            })
    # Sort by distance ascending
    number_infos.sort(key=lambda x: x['distance'])
    return number_infos

def extract_pdf_content(
    pdf_path: str,
    mda_terms: Optional[List[str]] = None,
    other_terms: Optional[List[str]] = None
) -> Dict[str, Any]:
    if mda_terms is None:
        mda_terms = DEFAULT_MDA_TERMS.copy()
    if other_terms is None:
        other_terms = DEFAULT_Other_TERMS.copy()
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return {
            'success': False,
            'message': f'Error opening PDF: {str(e)}'
        }
    try:
        toc_page_num = None
        mda_bbox = None
        found_phrases = []

        # Step 1: Find TOC Page - Must contain a phrase from both lists
        for page_num, page in enumerate(doc):
            has_mda = False
            has_other = False
            mda_bbox_local = None

            for phrase in mda_terms:
                instances = page.search_for(phrase)
                if instances and not has_mda:
                    has_mda = True
                    mda_bbox_local = instances[0]
            for phrase in other_terms:
                instances = page.search_for(phrase)
                if instances:
                    has_other = True
            if has_mda and has_other:
                toc_page_num = page_num
                mda_bbox = mda_bbox_local
                break

        if toc_page_num is None or mda_bbox is None:
            return {
                'success': False,
                'message': 'Table of Contents page not found with required phrases'
            }

        page = doc[toc_page_num]
        phrase_center = calculate_bbox_center(mda_bbox)

        # Get which phrase matched for MDA, for output reference; get all matches on page
        found_phrases = []
        for phrase in mda_terms + other_terms:
            if page.search_for(phrase):
                found_phrases.append(phrase)

        # Extract contents
        same_line_contents, below_line_contents = _extract_contents_from_page(page, mda_bbox)
        # Extract numbers, calculate distance, sort
        same_line_numbers = _extract_numbers_with_distance(same_line_contents, mda_bbox)
        below_line_numbers = _extract_numbers_with_distance(below_line_contents, mda_bbox)
        # Output numbers from same line as starting page, below line as ending page
        starting_page_numbers = [(num['number'], num['distance']) for num in same_line_numbers]
        ending_page_numbers = [(num['number'], num['distance']) for num in below_line_numbers]
        return {
            'success': True,
            'table_of_content': toc_page_num + 1,
            'found_phrases': found_phrases,
            'phrase_bbox': mda_bbox,
            'phrase_center': phrase_center,
            'same_line_numbers_sorted': same_line_numbers,
            'below_line_numbers_sorted': below_line_numbers,
            'starting_page_numbers': starting_page_numbers,
            'ending_page_numbers': ending_page_numbers
        }

        return {
            'success': False,
            'message': 'No valid Table of Contents page found'
        }
    finally:
        doc.close()

__version__ = '1.0.2'
__author__ = 'Ganji Rajesh'
__all__ = [
    'extract_pdf_content',
    'calculate_bbox_center',
    'calculate_distance',
    'extract_numbers_from_text'
]
