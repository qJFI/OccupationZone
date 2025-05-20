#!/usr/bin/env python3
"""
Utility functions for enhancing crawler capabilities and avoiding detection
"""

import random
import time
import logging
import requests
import re
import urllib.parse
from typing import Dict, List, Optional, Union, Any, Tuple
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# Import configuration
from core.config import (
    HEADERS, USER_AGENTS, REQUEST_TIMEOUT, REQUEST_DELAY,
    MAX_RETRIES, ADD_RANDOM_DELAY, MIN_RANDOM_DELAY, MAX_RANDOM_DELAY,
    ROTATE_USER_AGENT, USE_ROTATING_PROXIES, PROXY_LIST, MOCK_BROWSER
)

# Set up logging
logger = logging.getLogger(__name__)

def get_random_user_agent() -> str:
    """Get a random user agent from the list of user agents"""
    return random.choice(USER_AGENTS)

def get_random_proxy() -> Optional[Dict[str, str]]:
    """Get a random proxy from the proxy list"""
    if not USE_ROTATING_PROXIES or not PROXY_LIST:
        return None
    
    proxy = random.choice(PROXY_LIST)
    return {"http": proxy, "https": proxy}

def get_headers(custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Get headers with optional custom headers and user agent rotation"""
    headers = HEADERS.copy()
    
    # Rotate user agent if enabled
    if ROTATE_USER_AGENT:
        headers['User-Agent'] = get_random_user_agent()
    
    # Add custom headers if provided
    if custom_headers:
        headers.update(custom_headers)
    
    return headers

def create_session(max_retries: int = MAX_RETRIES) -> requests.Session:
    """Create a session with retry capabilities"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid"""
    try:
        result = urllib.parse.urlparse(url)
        # Check for scheme and netloc
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """Normalize URL by ensuring it has scheme and fixing common issues"""
    if not url:
        return ""
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove trailing slash for consistency
    if url.endswith('/'):
        url = url[:-1]
    
    return url

def generate_alternative_urls(url: str) -> List[str]:
    """Generate alternative URLs to try when a 404 is encountered"""
    alternatives = []
    
    try:
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Add base URL
        alternatives.append(base_url)
        
        # Try parent paths
        path_parts = parsed.path.strip('/').split('/')
        for i in range(len(path_parts)):
            parent_path = '/'.join(path_parts[:-(i+1)])
            if parent_path:
                alternatives.append(f"{base_url}/{parent_path}")
        
        # Try adding common job URL patterns
        for pattern in ['jobs', 'careers', 'job-search', 'positions', 'work-with-us']:
            alternatives.append(f"{base_url}/{pattern}")
        
    except Exception as e:
        logger.error(f"Error generating alternative URLs: {e}")
    
    # Remove duplicates
    return list(dict.fromkeys(alternatives))

def make_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    timeout: int = REQUEST_TIMEOUT,
    verify: bool = True,
    allow_redirects: bool = True,
    session: Optional[requests.Session] = None,
    try_alternatives: bool = True,
) -> Tuple[Optional[requests.Response], Optional[str]]:
    """Make a request with enhanced anti-bot detection measures and 404 handling"""
    # Validate and normalize URL
    url = normalize_url(url)
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        return None, None
    
    # Apply random delay if enabled
    if ADD_RANDOM_DELAY:
        delay = REQUEST_DELAY + random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
        time.sleep(delay)
    else:
        time.sleep(REQUEST_DELAY)
    
    # Get headers with user agent rotation if enabled
    request_headers = get_headers(headers)
    
    # Get proxy if enabled
    proxies = get_random_proxy()
    
    # Use provided session or create a new one
    if session is None:
        session = create_session()
    
    # Track the actual URL used (in case we try alternatives)
    final_url = url
    
    try:
        if method.upper() == "GET":
            response = session.get(
                url,
                params=params,
                headers=request_headers,
                cookies=cookies,
                timeout=timeout,
                proxies=proxies,
                verify=verify,
                allow_redirects=allow_redirects,
            )
        elif method.upper() == "POST":
            response = session.post(
                url,
                params=params,
                data=data,
                headers=request_headers,
                cookies=cookies,
                timeout=timeout,
                proxies=proxies,
                verify=verify,
                allow_redirects=allow_redirects,
            )
        else:
            logger.error(f"Unsupported method: {method}")
            return None, None
        
        # Log request details for debugging
        logger.debug(f"Request: {method} {url}")
        logger.debug(f"Status code: {response.status_code}")
        
        # Handle specific status codes
        if response.status_code == 404:
            logger.warning(f"URL not found: {url} - 404 Not Found")
            
            # Try alternative URLs if enabled
            if try_alternatives:
                alternatives = generate_alternative_urls(url)
                logger.info(f"Trying {len(alternatives)} alternative URLs")
                
                for alt_url in alternatives:
                    logger.info(f"Trying alternative URL: {alt_url}")
                    
                    # Recursive call with try_alternatives=False to avoid infinite recursion
                    alt_response, used_url = make_request(
                        alt_url, method, params, data, headers, cookies,
                        timeout, verify, allow_redirects, session, 
                        try_alternatives=False
                    )
                    
                    if alt_response and alt_response.status_code == 200:
                        logger.info(f"Successfully found alternative URL: {alt_url}")
                        return alt_response, alt_url
            
            return None, None
        elif response.status_code == 403:
            logger.warning(f"Blocked by {url} - 403 Forbidden")
        elif response.status_code == 429:
            logger.warning(f"Rate limited by {url} - 429 Too Many Requests")
        elif "captcha" in response.text.lower() or "robot" in response.text.lower():
            logger.warning(f"Possible CAPTCHA/anti-bot measure detected at {url}")
        
        response.raise_for_status()
        return response, final_url
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Exception: {e}")
    except Exception as e:
        logger.error(f"Unexpected error making request to {url}: {e}")
    
    return None, None

def parse_html(html_content: str) -> Optional[BeautifulSoup]:
    """Parse HTML content with BeautifulSoup"""
    if not html_content:
        logger.warning("Empty HTML content provided to parse_html")
        return None
        
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Check if page likely contains a 404 indicator
        title = soup.find('title')
        if title and title.get_text(strip=True).lower() in ['404', 'not found', 'page not found', 'error 404']:
            logger.warning("Page appears to be a 404 page based on title")
            return None
            
        # Check for common 404 text patterns
        body_text = soup.get_text().lower()
        if any(phrase in body_text for phrase in ['page not found', 'does not exist', 'no longer available']):
            logger.warning("Page appears to be a 404 page based on content")
            return None
            
        return soup
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return None

def extract_text(element) -> str:
    """Safely extract text from a BeautifulSoup element"""
    if element is None:
        return ""
    return element.get_text(strip=True)

def extract_attribute(element, attribute: str) -> Optional[str]:
    """Safely extract an attribute from a BeautifulSoup element"""
    if element is None:
        return None
    return element.get(attribute)

def is_valid_job(job_data: Dict[str, Any]) -> bool:
    """Check if job data is valid and has required fields"""
    required_fields = ['title', 'company', 'description']
    return all(field in job_data and job_data[field] for field in required_fields)

def standardize_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize job data fields for consistent storage"""
    # Ensure all required fields exist
    standard_fields = [
        'id', 'title', 'company', 'location', 'description',
        'salary', 'job_type', 'experience_level', 'application_link',
        'posting_date', 'source_website', 'platform', 'additional_data'
    ]
    
    standardized_data = {}
    
    # Copy existing fields
    for field in standard_fields:
        if field in job_data:
            standardized_data[field] = job_data[field]
        else:
            standardized_data[field] = None
    
    # Handle special case for platform/source_website compatibility
    if 'platform' in job_data and 'source_website' not in job_data:
        standardized_data['source_website'] = job_data['platform']
    elif 'source_website' in job_data and 'platform' not in job_data:
        standardized_data['platform'] = job_data['source_website']
    
    # Add any additional fields from the original data
    for key, value in job_data.items():
        if key not in standardized_data:
            if 'additional_data' not in standardized_data:
                standardized_data['additional_data'] = {}
            if isinstance(standardized_data['additional_data'], dict):
                standardized_data['additional_data'][key] = value
    
    return standardized_data
