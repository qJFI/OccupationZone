"""
Base crawler class for the Job Crawler application.
"""

import abc
import logging
import requests
import time
import random
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin

# Import enhanced crawler utilities
from crawler_utils import (
    make_request as utils_make_request,
    create_session, get_headers, get_random_user_agent,
    is_valid_url, normalize_url, parse_html,
    standardize_job_data, is_valid_job
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseCrawler(abc.ABC):
    """
    Abstract base class for all website crawlers.
    """
    
    # List of user agents to rotate through
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 OPR/78.0.4093.147'
    ]
    
    def __init__(self, name: str, base_url: str, headers: Dict[str, str], request_delay: float = 2.0):
        """
        Initialize the base crawler.
        
        Args:
            name (str): Name of the crawler/website
            base_url (str): Base URL of the website
            headers (dict): HTTP headers to use for requests
            request_delay (float): Delay between requests in seconds
        """
        self.name = name
        self.base_url = base_url
        self.headers = headers
        self.request_delay = request_delay
        self.logger = logging.getLogger(f'crawler.{name.lower()}')
        self.logger.info(f"Initialized {name} crawler")
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    @abc.abstractmethod
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for jobs based on query and filters.
        
        Args:
            query (str): Search query
            filters (dict, optional): Additional filters
            
        Returns:
            list: List of job dictionaries
        """
        pass
    
    @abc.abstractmethod
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job.
        
        Args:
            job_url (str): URL of the job posting
            
        Returns:
            dict: Detailed job information
        """
        pass
    
    def make_request(self, url: str, method: str = 'GET', params: Optional[Dict[str, Any]] = None, 
                    data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None,
                    try_alternatives: bool = True) -> Tuple[Optional[requests.Response], Optional[str]]:
        """
        Make an HTTP request with enhanced error handling, rate limiting, and 404 handling.
        
        Args:
            url (str): URL to request
            method (str): HTTP method (GET, POST, etc.)
            params (dict, optional): Query parameters
            data (dict, optional): Form data
            json_data (dict, optional): JSON data
            try_alternatives (bool, optional): Whether to try alternative URLs on 404 errors
            
        Returns:
            Tuple[Response, str]: HTTP response and the URL that was successfully used, or (None, None) on failure
        """
        # Ensure URL is absolute
        if not url.startswith('http'):
            url = urljoin(self.base_url, url)
            
        # Validate and normalize URL
        url = normalize_url(url)
        if not is_valid_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return None, None
            
        # Use enhanced request making with 404 handling
        response, used_url = utils_make_request(
            url=url,
            method=method,
            params=params,
            data=data,
            headers=self.headers,
            session=self.session,
            try_alternatives=try_alternatives
        )
        
        return response, used_url
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Making {method} request to {url}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=30
                )
                
                # Check if request was successful
                response.raise_for_status()
                
                return response
            
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    # Wait before retrying
                    time.sleep(retry_delay * (attempt + 1))
    
    def make_robust_request(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, 
                   delay_factor: float = 1.5) -> Tuple[Optional[requests.Response], Optional[str]]:
        """
        Make an HTTP request with built-in retries, user agent rotation, and 404 handling.
        
        Args:
            url (str): URL to request
            params (dict, optional): Query parameters for GET request
            max_retries (int): Maximum number of retry attempts
            delay_factor (float): Multiplier for increasing delay between retries
            
        Returns:
            Tuple[Response, str]: HTTP response and the URL that was successfully used, or (None, None) on failure
        """
        # Ensure URL is absolute
        if not url.startswith('http'):
            url = urljoin(self.base_url, url)
            
        # Validate and normalize URL
        url = normalize_url(url)
        if not is_valid_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return None, None
        
        # Set up enhanced headers with anti-bot countermeasures
        custom_headers = {
            'User-Agent': get_random_user_agent(),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',  # Do Not Track
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add random referrers to appear more like a normal browser
        if random.random() > 0.3:  # Increased probability
            referrers = [
                'https://www.google.com/search?q=jobs',
                'https://www.bing.com/search?q=careers',
                'https://www.linkedin.com/jobs/',
                'https://www.indeed.com/jobs',
                'https://duckduckgo.com/?q=job+search',
                'https://www.glassdoor.com/Job/index.htm'
            ]
            custom_headers['Referer'] = random.choice(referrers)
        
        success = False
        final_response = None
        final_url = None
        current_delay = self.request_delay
        
        # Try multiple times with increasing delays
        for attempt in range(1, max_retries + 1):
            try:
                # Add jitter to delay to appear more human-like
                jitter = random.uniform(0.7, 1.3)
                time.sleep(current_delay * jitter)
                
                # Make the request using enhanced utilities
                response, used_url = utils_make_request(
                    url=url,
                    method="GET",
                    params=params,
                    headers=custom_headers,
                    session=self.session,
                    # Only try alternatives on the last attempt
                    try_alternatives=(attempt == max_retries)
                )
                
                # If we got a valid response
                if response and response.status_code == 200:
                    self.logger.info(f"Request successful on attempt {attempt}/{max_retries}")
                    return response, used_url
                elif response:
                    self.logger.warning(f"Request returned status code {response.status_code} on attempt {attempt}/{max_retries}")
                    
                    # Adjust delay based on response
                    if response.status_code == 429:  # Too Many Requests
                        current_delay *= 3
                    elif response.status_code == 403:  # Forbidden
                        current_delay *= 2
                        # Try rotating our custom headers more aggressively
                        custom_headers['User-Agent'] = get_random_user_agent()
                    else:
                        current_delay *= delay_factor
                else:
                    self.logger.warning(f"Request failed on attempt {attempt}/{max_retries}")
                    current_delay *= delay_factor
            except Exception as e:
                self.logger.warning(f"Exception during request (attempt {attempt}/{max_retries}): {str(e)}")
                current_delay *= delay_factor
        
        # If we get here, all attempts failed
        self.logger.error(f"All {max_retries} request attempts failed for URL: {url}")
        return None, None
    
    def normalize_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job data to ensure consistent format.
        
        Args:
            job_data (dict): Raw job data
            
        Returns:
            dict: Normalized job data
        """
        # First apply our basic normalization
        normalized = {
            'title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', ''),
            'description': job_data.get('description', ''),
            'salary': job_data.get('salary', ''),
            'job_type': job_data.get('job_type', ''),
            'experience_level': job_data.get('experience_level', ''),
            'application_link': job_data.get('application_link', ''),
            'posting_date': job_data.get('posting_date', ''),
            'source_website': self.name,
            'platform': self.name,  # Ensure platform is set for backward compatibility
            'additional_data': {}
        }
        
        # Validate and normalize the application link if present
        if normalized['application_link']:
            try:
                normalized['application_link'] = normalize_url(normalized['application_link'])
            except:
                # If URL normalization fails, keep the original
                pass
        
        # Add any additional fields to additional_data
        for key, value in job_data.items():
            if key not in normalized:
                if isinstance(normalized['additional_data'], dict):
                    normalized['additional_data'][key] = value
        
        # Apply the standardize_job_data utility for extra formatting
        return standardize_job_data(normalized)
