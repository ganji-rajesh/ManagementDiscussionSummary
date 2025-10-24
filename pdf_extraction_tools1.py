"""PDF Content Extractor Module.

This module provides functionality to extract and analyze content from PDF files
using PyMuPDF (fitz) library. It focuses on finding specific phrases and analyzing
content around them.

Usage:
    from pdf_extractor import extract_pdf_content
    
    result = extract_pdf_content('path/to/your/file.pdf')
    if result['success']:
        print(result['table_of_content'])
        print(result['mda_starting_page_numbers'])

Author: Ganji Rajesh    
Version: 1.0.0
"""

from typing import Dict, List, Tuple, Optional, Any
import math
import re

import pymupdf  # PyMuPDF


# Constants
DEFAULT_SEARCH_PHRASES = [
    "management discussion and analysis",
    "corporate governance"
]
BELOW_LINE_RANGE = 72  # Points (1 inch)
NUMBER_PATTERN = r'\d+\.?\d*'


def calculate_bbox_center(bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Calculate the center point of a bounding box.
    
    Args:
        bbox: Bounding box coordinates (x0, y0, x1, y1).
    
    Returns:
        Center coordinates (center_x, center_y).
    """
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    return (center_x, center_y)


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points.
    
    Args:
        point1: First point (x, y).
        point2: Second point (x, y).
    
    Returns:
        Euclidean distance between the points.
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def extract_numbers_from_text(text: str) -> List[str]:
    """Extract all numbers (integers and floats) from text.
    
    Args:
        text: Input text string.
    
    Returns:
        List of extracted numbers as strings.
    """
    numbers = re.findall(NUMBER_PATTERN, text)
    return [num for num in numbers if num]


def is_number(text: str) -> bool:
    """Check if text contains any number.
    
    Args:
        text: Input text string.
    
    Returns:
        True if text contains numbers, False otherwise.
    """
    return bool(extract_numbers_from_text(text))


def _clean_contents_with_distance(
    contents: List[Dict[str, Any]],
    phrase_bbox: Tuple[float, float, float, float]
) -> List[Dict[str, Any]]:
    """Add center and distance information to each content item.
    
    Args:
        contents: List of content items with text and bbox.
        phrase_bbox: Bounding box of the phrase.
    
    Returns:
        Cleaned contents with added center and distance information.
    """
    phrase_center = calculate_bbox_center(phrase_bbox)
    cleaned_contents = []
    
    for item in contents:
        item_center = calculate_bbox_center(item['bbox'])
        distance = calculate_distance(phrase_center, item_center)
        
        cleaned_item = {
            'text': item['text'],
            'bbox': item['bbox'],
            'font': item.get('font', ''),
            'size': item.get('size', 0),
            'center': item_center,
            'distance_from_phrase': distance
        }
        
        if 'y_position' in item:
            cleaned_item['y_position'] = item['y_position']
        
        cleaned_contents.append(cleaned_item)
    
    return cleaned_contents


def _segregate_numbers_by_position(
    contents: List[Dict[str, Any]],
    phrase_bbox: Tuple[float, float, float, float]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Segregate numbers into left and right side based on phrase position.
    
    Numbers are sorted by distance in ascending order (closest to farthest).
    
    Args:
        contents: List of content items with center and distance info.
        phrase_bbox: Bounding box of the phrase.
    
    Returns:
        Tuple of (left_side_numbers, right_side_numbers), both sorted by distance.
    """
    phrase_center = calculate_bbox_center(phrase_bbox)
    phrase_center_x = phrase_center[0]
    
    left_side_numbers = []
    right_side_numbers = []
    
    for item in contents:
        text = item['text']
        numbers = extract_numbers_from_text(text)
        
        if not numbers:
            continue
            
        item_center_x = item['center'][0]
        
        for number in numbers:
            number_info = {
                'number': number,
                'text': text,
                'bbox': item['bbox'],
                'center': item['center'],
                'distance': item['distance_from_phrase']
            }
            
            if item_center_x < phrase_center_x:
                left_side_numbers.append(number_info)
            else:
                right_side_numbers.append(number_info)
    
    # Sort by distance in ascending order
    left_side_numbers.sort(key=lambda x: x['distance'])
    right_side_numbers.sort(key=lambda x: x['distance'])
    
    return left_side_numbers, right_side_numbers


def _extract_contents_from_page(
    page: pymupdf.Page,
    phrase_bbox: Tuple[float, float, float, float]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract same line and below line contents from a page.
    
    Args:
        page: PyMuPDF page object.
        phrase_bbox: Bounding box of the target phrase.
    
    Returns:
        Tuple of (same_line_contents, below_line_contents).
    """
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
            
            # Check if line overlaps with phrase line
            if line_y0 <= y1 and line_y1 >= y0:
                for span in line["spans"]:
                    same_line_contents.append({
                        'text': span['text'],
                        'bbox': span['bbox'],
                        'font': span.get('font', ''),
                        'size': span.get('size', 0)
                    })
            
            # Check if line is below within range
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


def extract_pdf_content(
    pdf_path: str,
    target_phrases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Extract and analyze PDF content based on specific phrases.
    
    Args:
        pdf_path: Path to the PDF file.
        target_phrases: List of phrases to search for. Defaults to
            ["management discussion and analysis", "corporate governance"].
    
    Returns:
        Dictionary containing extraction results with the following keys:
            - success (bool): Whether extraction was successful.
            - page_number (int): Page number where phrase was found.
            - found_phrases (List[str]): List of phrases found.
            - phrase_bbox (Tuple): Bounding box of the phrase.
            - phrase_center (Tuple): Center coordinates of the phrase.
            - same_line_contents_cleaned (List): Cleaned same line contents.
            - below_line_contents_cleaned (List): Cleaned below line contents.
            - same_line_left_numbers (List): Left side numbers from same line.
            - same_line_right_numbers (List): Right side numbers from same line.
            - below_line_left_numbers (List): Left side numbers from below line.
            - below_line_right_numbers (List): Right side numbers from below line.
            - table_of_content (int): Page number (ToC page).
            - mda_starting_page_numbers (List[Tuple]): Page numbers and distances.
            - mda_ending_page_numbers (List[Tuple]): Page numbers and distances.
    
    Example:
        >>> result = extract_pdf_content('document.pdf')
        >>> if result['success']:
        ...     print(f"ToC Page: {result['table_of_content']}")
        ...     print(f"MDA Start: {result['mda_starting_page_numbers']}")
    """
    if target_phrases is None:
        target_phrases = DEFAULT_SEARCH_PHRASES.copy()
    
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return {
            'success': False,
            'message': f'Error opening PDF: {str(e)}'
        }
    
    try:
        for page_num, page in enumerate(doc):
            text_instances = []
            found_phrases = []
            
            for phrase in target_phrases:
                instances = page.search_for(phrase)
                if instances:
                    text_instances.extend(instances)
                    found_phrases.append(phrase)
            
            if not text_instances:
                continue
            
            # Process first found phrase
            first_bbox = text_instances[0]
            phrase_center = calculate_bbox_center(first_bbox)
            
            # Extract contents
            same_line_contents, below_line_contents = _extract_contents_from_page(
                page, first_bbox
            )
            
            # Clean contents with distance calculation
            same_line_cleaned = _clean_contents_with_distance(
                same_line_contents, first_bbox
            )
            below_line_cleaned = _clean_contents_with_distance(
                below_line_contents, first_bbox
            )
            
            # Segregate numbers by position
            same_left_nums, same_right_nums = _segregate_numbers_by_position(
                same_line_cleaned, first_bbox
            )
            below_left_nums, below_right_nums = _segregate_numbers_by_position(
                below_line_cleaned, first_bbox
            )
            
            # Create additional fields
            # table_of_content = page_num + 1
            # mda_starting_page_numbers = [
            #     (item['number'], item['distance']) for item in below_left_nums
            # ]
            # mda_ending_page_numbers = [
            #     (item['number'], item['distance']) for item in same_left_nums
            # ]
            # Create additional fields
            table_of_content = page_num + 1
            mda_starting_page_numbers = [
                (item['number'], item['distance']) for item in same_left_nums
            ] + [
                (item['number'], item['distance']) for item in same_right_nums
            ]
            mda_ending_page_numbers = [
                (item['number'], item['distance']) for item in below_left_nums
            ] + [
                (item['number'], item['distance']) for item in below_right_nums
            ]

            
            return {
                'success': True,
                'page_number': page_num + 1,
                'found_phrases': found_phrases,
                'phrase_bbox': first_bbox,
                'phrase_center': phrase_center,
                'same_line_contents_cleaned': same_line_cleaned,
                'below_line_contents_cleaned': below_line_cleaned,
                'same_line_left_numbers': same_left_nums,
                'same_line_right_numbers': same_right_nums,
                'below_line_left_numbers': below_left_nums,
                'below_line_right_numbers': below_right_nums,
                'table_of_content': table_of_content,
                'mda_starting_page_numbers': mda_starting_page_numbers,
                'mda_ending_page_numbers': mda_ending_page_numbers
            }
        
        return {
            'success': False,
            'message': 'Phrases not found in the document'
        }
    
    finally:
        doc.close()


# Module metadata
__version__ = '1.0.0'
__author__ = 'Your Name'
__all__ = [
    'extract_pdf_content',
    'calculate_bbox_center',
    'calculate_distance',
    'extract_numbers_from_text',
    'is_number'
]
