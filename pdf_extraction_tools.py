"""
PDF Text Search and Analysis Module

This module provides utilities for searching text in PDF documents and
extracting page numbers from Table of Contents using spatial analysis.

Author: Ganji Rajesh
License: MIT
Version: 1.0.0
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from contextlib import contextmanager

import pymupdf


# Configure module-level logger
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class PDFSearchError(Exception):
    """Raised when a PDF search operation fails."""
    pass


class PDFNotFoundError(PDFSearchError):
    """Raised when the specified PDF file cannot be found."""
    pass


class InvalidPageNumberError(PDFSearchError):
    """Raised when an invalid page number is provided."""
    pass


# ============================================================================
# Context Manager for PDF Document Handling
# ============================================================================

@contextmanager
def open_pdf_document(pdf_path: str):
    """
    Context manager for safely opening and closing PDF documents.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Yields:
        pymupdf.Document: The opened PDF document.
        
    Raises:
        PDFNotFoundError: If the PDF file cannot be opened.
        
    Example:
        >>> with open_pdf_document("file.pdf") as doc:
        ...     for page in doc:
        ...         print(page.number)
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        logger.debug("Opened PDF: %s", pdf_path)
        yield doc
    except FileNotFoundError as e:
        logger.error("PDF file not found: %s", pdf_path)
        raise PDFNotFoundError(f"PDF file not found: {pdf_path}") from e
    except Exception as e:
        logger.error("Failed to open PDF %s: %s", pdf_path, e)
        raise PDFSearchError(f"Failed to open PDF: {e}") from e
    finally:
        if doc is not None:
            doc.close()
            logger.debug("Closed PDF: %s", pdf_path)


# ============================================================================
# Core Search Functions
# ============================================================================

def count_word_occurrences(pdf_path: str, search_word: str) -> int:
    """
    Count the total number of occurrences of a word across all pages in a PDF.
    
    Args:
        pdf_path: The file path to the PDF document.
        search_word: The word to search for (case-sensitive by default).
    
    Returns:
        Total count of occurrences across all pages.
        
    Raises:
        PDFSearchError: If an error occurs during the search.
        ValueError: If search_word is empty.
    
    Example:
        >>> count = count_word_occurrences("document.pdf", "Management")
        >>> print(f"Found {count} occurrences")
        Found 12 occurrences
    """
    if not search_word or not search_word.strip():
        raise ValueError("Search word cannot be empty")
    
    logger.info("Counting occurrences of '%s' in %s", search_word, pdf_path)
    
    try:
        total_count = 0
        
        with open_pdf_document(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                matches = page.search_for(search_word)
                count_on_page = len(matches)
                total_count += count_on_page
                
                if count_on_page > 0:
                    logger.debug(
                        "Found %d occurrence(s) on page %d",
                        count_on_page,
                        page_num
                    )
        
        logger.info("Total occurrences found: %d", total_count)
        return total_count
        
    except PDFSearchError:
        raise
    except Exception as e:
        logger.exception("Unexpected error while counting occurrences")
        raise PDFSearchError(f"Error counting occurrences: {e}") from e


def get_word_occurrence_pages(pdf_path: str, search_word: str) -> List[int]:
    """
    Get a list of page numbers where the word occurs.
    
    Args:
        pdf_path: The file path to the PDF document.
        search_word: The word to search for (case-sensitive by default).
    
    Returns:
        List of 1-based page numbers where the word was found.
        Empty list if word not found.
        
    Raises:
        PDFSearchError: If an error occurs during the search.
        ValueError: If search_word is empty.
    
    Example:
        >>> pages = get_word_occurrence_pages("document.pdf", "Management")
        >>> print(f"Found on pages: {pages}")
        Found on pages: [3, 10, 25, 42]
    """
    if not search_word or not search_word.strip():
        raise ValueError("Search word cannot be empty")
    
    logger.info("Finding pages with '%s' in %s", search_word, pdf_path)
    
    try:
        page_numbers = []
        
        with open_pdf_document(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                if page.search_for(search_word):
                    page_numbers.append(page_num)
                    logger.debug("Found '%s' on page %d", search_word, page_num)
        
        logger.info(
            "Word '%s' found on %d page(s)",
            search_word,
            len(page_numbers)
        )
        return page_numbers
        
    except PDFSearchError:
        raise
    except Exception as e:
        logger.exception("Unexpected error while finding word occurrences")
        raise PDFSearchError(f"Error finding occurrences: {e}") from e


def get_nth_occurrence_page(
    pdf_path: str,
    search_word: str,
    n: int
) -> Optional[int]:
    """
    Return the page number containing the n-th occurrence of a search word.
    
    Occurrences are counted across the entire document in page order.
    
    Args:
        pdf_path: Path to the PDF file.
        search_word: The word to search for (case-sensitive by default).
        n: The 1-based index of the occurrence to locate (must be >= 1).
    
    Returns:
        The 1-based page number containing the n-th occurrence,
        or None if n exceeds the total number of occurrences.
        
    Raises:
        PDFSearchError: If an error occurs during the search.
        ValueError: If n < 1 or search_word is empty.
    
    Example:
        >>> page = get_nth_occurrence_page("document.pdf", "Management", 5)
        >>> print(f"5th occurrence is on page {page}")
        5th occurrence is on page 12
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    
    if not search_word or not search_word.strip():
        raise ValueError("Search word cannot be empty")
    
    logger.info(
        "Finding %d-th occurrence of '%s' in %s",
        n,
        search_word,
        pdf_path
    )
    
    try:
        remaining = n
        
        with open_pdf_document(pdf_path) as doc:
            for page_index, page in enumerate(doc):
                matches = page.search_for(search_word)
                count_here = len(matches)
                
                if remaining <= count_here:
                    page_num = page_index + 1
                    logger.info(
                        "%d-th occurrence found on page %d",
                        n,
                        page_num
                    )
                    return page_num
                
                remaining -= count_here
        
        logger.warning(
            "%d-th occurrence not found (total occurrences < %d)",
            n,
            n
        )
        return None
        
    except PDFSearchError:
        raise
    except Exception as e:
        logger.exception("Unexpected error while locating n-th occurrence")
        raise PDFSearchError(f"Error locating n-th occurrence: {e}") from e


# ============================================================================
# Table of Contents Parsing
# ============================================================================

def get_topic_page_number(
    pdf_path: str,
    content_page_num: int,
    topic_text: str,
    proximity_threshold: int = 50
) -> Optional[Tuple[int, Dict[str, float]]]:
    """
    Extract page number for a topic from a Table of Contents page.
    
    Uses spatial analysis to match topics with their corresponding page numbers
    by analyzing text position coordinates. Handles multi-column layouts where
    topics and page numbers are visually separated.
    
    Args:
        pdf_path: Path to the PDF file.
        content_page_num: The 1-based page number of the Table of Contents.
        topic_text: The topic name to search for (case-insensitive).
        proximity_threshold: Maximum vertical distance in pixels between
            topic and page number. Defaults to 50.
    
    Returns:
        A tuple containing:
            - The page number associated with the topic
            - A dictionary with positioning metadata:
                - 'topic_y': Y-coordinate of the topic
                - 'topic_x': X-coordinate of the topic
                - 'vertical_distance': Vertical distance to matched page number
        Returns None if the topic or page number is not found.
        
    Raises:
        PDFSearchError: If an error occurs during parsing.
        InvalidPageNumberError: If content_page_num is invalid.
        ValueError: If topic_text is empty or proximity_threshold is invalid.
    
    Example:
        >>> result = get_topic_page_number("doc.pdf", 4, "Introduction")
        >>> if result:
        ...     page_num, metadata = result
        ...     print(f"Topic found on page {page_num}")
    """
    # Validate inputs
    if content_page_num < 1:
        raise InvalidPageNumberError("Page number must be >= 1")
    
    if not topic_text or not topic_text.strip():
        raise ValueError("Topic text cannot be empty")
    
    if proximity_threshold < 0:
        raise ValueError("Proximity threshold must be non-negative")
    
    logger.info(
        "Extracting page number for topic '%s' from ToC page %d in %s",
        topic_text,
        content_page_num,
        pdf_path
    )
    
    try:
        with open_pdf_document(pdf_path) as doc:
            # Validate page number
            if content_page_num > len(doc):
                raise InvalidPageNumberError(
                    f"Page {content_page_num} exceeds document length "
                    f"({len(doc)} pages)"
                )
            
            page = doc.load_page(content_page_num - 1)
            page_dict = page.get_text("dict")
            
            # Find topic position
            topic_position = _find_topic_position(page_dict, topic_text)
            
            if topic_position is None:
                logger.warning(
                    "Topic '%s' not found on page %d",
                    topic_text,
                    content_page_num
                )
                return None
            
            topic_x, topic_y = topic_position
            logger.debug(
                "Topic '%s' found at position (x=%.2f, y=%.2f)",
                topic_text,
                topic_x,
                topic_y
            )
            
            # Extract all numbers with positions
            page_numbers = _extract_numbers_with_positions(page_dict)
            logger.debug("Extracted %d numeric values from page", len(page_numbers))
            
            # Find the closest page number to the right
            result = _find_closest_right_number(
                page_numbers,
                topic_x,
                topic_y,
                proximity_threshold
            )
            
            if result:
                page_num, vertical_distance = result
                logger.info(
                    "Topic '%s' maps to page %d (distance: %.2f px)",
                    topic_text,
                    page_num,
                    vertical_distance
                )
                
                metadata = {
                    "topic_y": topic_y,
                    "topic_x": topic_x,
                    "vertical_distance": vertical_distance
                }
                return page_num, metadata
            else:
                logger.warning(
                    "No page number found to the right of topic '%s' "
                    "within %d px threshold",
                    topic_text,
                    proximity_threshold
                )
                return None
            
    except (PDFSearchError, InvalidPageNumberError):
        raise
    except Exception as e:
        logger.exception("Unexpected error while parsing ToC page")
        raise PDFSearchError(f"Error parsing Contents page: {e}") from e


# ============================================================================
# Private Helper Functions
# ============================================================================

def _find_topic_position(
    page_dict: Dict,
    topic_text: str
) -> Optional[Tuple[float, float]]:
    """
    Locate the X and Y coordinates of a topic in the page dictionary.
    
    Args:
        page_dict: Dictionary from page.get_text("dict").
        topic_text: The topic to search for (case-insensitive).
    
    Returns:
        Tuple of (x_coordinate, y_coordinate) or None if not found.
    """
    topic_text_lower = topic_text.lower()
    
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # Skip non-text blocks
            continue
            
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if topic_text_lower in span["text"].lower():
                    bbox = span["bbox"]
                    return bbox[0], bbox[1]  # x, y coordinates
    
    return None


def _extract_numbers_with_positions(
    page_dict: Dict
) -> List[Tuple[int, float, float]]:
    """
    Extract all numeric values from the page with their coordinates.
    
    Args:
        page_dict: Dictionary from page.get_text("dict").
    
    Returns:
        List of tuples (number, x_coordinate, y_coordinate).
    """
    numbers = []
    
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # Skip non-text blocks
            continue
            
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                # Find all numbers in this span's text
                matches = re.findall(r"\d+", span["text"])
                
                for num_str in matches:
                    bbox = span["bbox"]
                    numbers.append((int(num_str), bbox[0], bbox[1]))
    
    return numbers


def _find_closest_right_number(
    page_numbers: List[Tuple[int, float, float]],
    topic_x: float,
    topic_y: float,
    proximity_threshold: int
) -> Optional[Tuple[int, float]]:
    """
    Find the number closest to the topic position on the right side.
    
    Args:
        page_numbers: List of (number, x, y) tuples.
        topic_x: X-coordinate of the topic.
        topic_y: Y-coordinate of the topic.
        proximity_threshold: Maximum vertical distance allowed.
    
    Returns:
        Tuple of (page_number, vertical_distance) or None if no match found.
    """
    closest_num = None
    closest_dist = float("inf")
    
    for num, x, y in page_numbers:
        # Number must be to the right of the topic
        if x > topic_x:
            vertical_distance = abs(y - topic_y)
            
            # Check if within threshold and closer than previous matches
            if vertical_distance <= proximity_threshold and vertical_distance < closest_dist:
                closest_num = num
                closest_dist = vertical_distance
    
    if closest_num is not None:
        return closest_num, closest_dist
    
    return None


