"""
Utility functions for the Job Crawler application.
"""

import logging
import re
import os
from datetime import datetime
from typing import Optional, Dict, Any

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and level.
    
    Args:
        name (str): Logger name
        level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler and set level
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add formatter to handler
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Replace newlines and tabs with spaces
    text = re.sub(r'[\n\t\r]+', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    return text

def extract_salary(text: str) -> str:
    """
    Extract salary information from text.
    
    Args:
        text (str): Text to extract salary from
        
    Returns:
        str: Extracted salary or empty string if not found
    """
    if not text:
        return ""
    
    # Common salary patterns
    patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*-\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # $50,000 - $70,000
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:to|–|-)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # $50,000 to 70,000
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*-\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:USD|EUR|GBP)',  # 50,000 - 70,000 USD
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k\s*-\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k',  # 50k - 70k
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # $50,000
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:USD|EUR|GBP)',  # 50,000 USD
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*k',  # 50k
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return ""

def extract_date(text: str) -> Optional[str]:
    """
    Extract date from text and convert to ISO format.
    
    Args:
        text (str): Text to extract date from
        
    Returns:
        str: Date in ISO format or None if not found
    """
    if not text:
        return None
    
    # Common date patterns
    patterns = [
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),  # 2023-01-15
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),  # 01/15/2023
        (r'(\d{1,2})/(\d{1,2})/(\d{2})', '%m/%d/%y'),  # 01/15/23
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),  # 15-01-2023
        (r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', '%d %B %Y'),  # 15 January 2023
        (r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', '%B %d, %Y'),  # January 15, 2023
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if fmt == '%d %B %Y' or fmt == '%B %d, %Y':
                    # Handle month names
                    date_str = match.group(0)
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                else:
                    # Handle numeric dates
                    if fmt == '%m/%d/%Y' or fmt == '%m/%d/%y':
                        month, day, year = match.groups()
                    elif fmt == '%d-%m-%Y':
                        day, month, year = match.groups()
                    else:  # '%Y-%m-%d'
                        year, month, day = match.groups()
                    
                    # Convert 2-digit year to 4-digit
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    
                    # Create date object
                    dt = datetime(int(year), int(month), int(day))
                    return dt.date().isoformat()
            except ValueError:
                continue
    
    # Handle relative dates
    relative_patterns = [
        (r'today', 0),
        (r'yesterday', 1),
        (r'(\d+)\s+days?\s+ago', lambda m: int(m.group(1))),
        (r'(\d+)\s+weeks?\s+ago', lambda m: int(m.group(1)) * 7),
        (r'(\d+)\s+months?\s+ago', lambda m: int(m.group(1)) * 30),
    ]
    
    for pattern, days_ago in relative_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            days = days_ago(match) if callable(days_ago) else days_ago
            dt = datetime.now() - datetime.timedelta(days=days)
            return dt.date().isoformat()
    
    return None

def normalize_url(base_url: str, url: str) -> str:
    """
    Normalize URL by ensuring it has a proper scheme and domain.
    
    Args:
        base_url (str): Base URL to use for relative URLs
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL
    """
    if not url:
        return ""
    
    # Check if URL is already absolute
    if url.startswith(('http://', 'https://')):
        return url
    
    # Handle protocol-relative URLs
    if url.startswith('//'):
        return 'https:' + url
    
    # Handle root-relative URLs
    if url.startswith('/'):
        # Extract domain from base_url
        match = re.match(r'(https?://[^/]+)', base_url)
        if match:
            domain = match.group(1)
            return domain + url
        else:
            return base_url.rstrip('/') + url
    
    # Handle relative URLs
    return base_url.rstrip('/') + '/' + url

def extract_job_type(text: str) -> str:
    """
    Extract job type from text.
    
    Args:
        text (str): Text to extract job type from
        
    Returns:
        str: Extracted job type or empty string if not found
    """
    if not text:
        return ""
    
    # Common job type patterns
    job_types = {
        'full-time': ['full time', 'full-time', 'permanent', 'regular'],
        'part-time': ['part time', 'part-time'],
        'contract': ['contract', 'temporary', 'temp'],
        'internship': ['internship', 'intern'],
        'freelance': ['freelance', 'freelancer'],
        'remote': ['remote', 'work from home', 'wfh', 'telecommute']
    }
    
    text_lower = text.lower()
    
    for job_type, keywords in job_types.items():
        for keyword in keywords:
            if keyword in text_lower:
                return job_type.title()
    
    return ""

def extract_experience_level(text: str) -> str:
    """
    Extract experience level from text.
    
    Args:
        text (str): Text to extract experience level from
        
    Returns:
        str: Extracted experience level or empty string if not found
    """
    if not text:
        return ""
    
    # Common experience level patterns
    experience_levels = {
        'entry level': ['entry level', 'junior', 'jr', 'beginner', 'graduate', 'fresh'],
        'mid level': ['mid level', 'intermediate', 'experienced'],
        'senior level': ['senior', 'sr', 'expert', 'lead', 'principal']
    }
    
    text_lower = text.lower()
    
    for level, keywords in experience_levels.items():
        for keyword in keywords:
            if keyword in text_lower:
                return level.title()
    
    return ""

def create_directory_if_not_exists(directory_path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory_path (str): Path to directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
