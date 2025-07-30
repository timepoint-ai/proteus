import os
import logging
import tweepy
import base64
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class XComAPIService:
    """Enhanced X.com API service with both API integration and manual fallback"""
    
    def __init__(self):
        # Initialize X.com API credentials from environment
        self.api_key = os.environ.get('X_API_KEY')
        self.api_secret = os.environ.get('X_API_SECRET')
        self.bearer_token = os.environ.get('X_BEARER_TOKEN')
        self.access_token = os.environ.get('X_ACCESS_TOKEN')
        self.access_token_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        # Initialize API client if credentials are available
        self.client = None
        if self.bearer_token or self.api_key:
            try:
                if self.bearer_token:
                    # Use v2 client with bearer token
                    self.client = tweepy.Client(
                        bearer_token=self.bearer_token,
                        consumer_key=self.api_key,
                        consumer_secret=self.api_secret,
                        access_token=self.access_token,
                        access_token_secret=self.access_token_secret,
                        wait_on_rate_limit=True
                    )
                elif self.api_key and self.api_secret:
                    # Use OAuth1 with just API key/secret
                    auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
                    if self.access_token and self.access_token_secret:
                        auth.set_access_token(self.access_token, self.access_token_secret)
                    self.client = tweepy.Client(auth=auth, wait_on_rate_limit=True)
                logger.info("X.com API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize X.com API client: {e}")
                self.client = None
    
    def extract_tweet_id_from_url(self, url: str) -> Optional[str]:
        """Extract tweet ID from X.com/Twitter URL"""
        patterns = [
            r'(?:x\.com|twitter\.com)/\w+/status/(\d+)',
            r'(?:x\.com|twitter\.com)/i/web/status/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username from X.com/Twitter URL"""
        patterns = [
            r'(?:x\.com|twitter\.com)/(\w+)/status/\d+',
            r'(?:x\.com|twitter\.com)/(\w+)/?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                username = match.group(1)
                # Filter out common non-username paths
                if username not in ['i', 'home', 'explore', 'notifications', 'messages']:
                    return username
        return None
    
    async def fetch_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Fetch tweet data using X.com API"""
        if not self.client:
            logger.warning("X.com API client not initialized, cannot fetch tweet")
            return None
            
        try:
            # Get tweet with expansions for author info
            tweet = self.client.get_tweet(
                tweet_id,
                expansions=['author_id'],
                tweet_fields=['created_at', 'text', 'author_id'],
                user_fields=['username', 'name']
            )
            
            if tweet.data:
                author = tweet.includes['users'][0] if tweet.includes and 'users' in tweet.includes else None
                return {
                    'id': tweet.data.id,
                    'text': tweet.data.text,
                    'author_username': author.username if author else None,
                    'author_name': author.name if author else None,
                    'created_at': tweet.data.created_at
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching tweet {tweet_id}: {e}")
            return None
    
    async def fetch_tweets_by_username(self, username: str, start_time: datetime, 
                                     end_time: datetime, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch tweets from a user within a time window"""
        if not self.client:
            logger.warning("X.com API client not initialized")
            return []
            
        try:
            # Get user ID from username
            user = self.client.get_user(username=username)
            if not user or not user.data:
                logger.error(f"User {username} not found")
                return []
                
            user_id = user.data.id
            
            # Fetch tweets in time window
            tweets = self.client.get_users_tweets(
                user_id,
                start_time=start_time.isoformat() + 'Z',
                end_time=end_time.isoformat() + 'Z',
                max_results=max_results,
                tweet_fields=['created_at', 'text']
            )
            
            if not tweets.data:
                return []
                
            return [
                {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'author_username': username
                }
                for tweet in tweets.data
            ]
            
        except Exception as e:
            logger.error(f"Error fetching tweets for {username}: {e}")
            return []
    
    async def capture_tweet_screenshot(self, tweet_url: str) -> Optional[str]:
        """Capture screenshot of tweet using Playwright"""
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 800, 'height': 1200},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # Navigate to tweet
                await page.goto(tweet_url, wait_until='networkidle')
                
                # Wait for tweet to load
                await page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                
                # Remove cookie banner and other overlays if present
                await page.evaluate('''
                    () => {
                        // Remove cookie banner
                        const cookieBanner = document.querySelector('[data-testid="BottomBar"]');
                        if (cookieBanner) cookieBanner.remove();
                        
                        // Remove login prompt
                        const loginPrompt = document.querySelector('[data-testid="sheetDialog"]');
                        if (loginPrompt) loginPrompt.remove();
                        
                        // Remove sticky header
                        const header = document.querySelector('header');
                        if (header) header.style.display = 'none';
                    }
                ''')
                
                # Find the tweet element
                tweet_element = await page.query_selector('article[data-testid="tweet"]')
                
                if tweet_element:
                    # Take screenshot of just the tweet
                    screenshot_bytes = await tweet_element.screenshot()
                    
                    # Convert to base64
                    base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    await browser.close()
                    return f"data:image/png;base64,{base64_screenshot}"
                else:
                    logger.error("Tweet element not found on page")
                    await browser.close()
                    return None
                    
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    async def verify_tweet_authenticity(self, tweet_id: str, expected_username: str,
                                      start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Verify tweet authenticity using API or manual verification"""
        result = {
            'verified': False,
            'tweet_id': tweet_id,
            'username_match': False,
            'time_window_match': False,
            'text': None,
            'created_at': None,
            'method': 'none'
        }
        
        # Try API verification first
        if self.client:
            tweet_data = await self.fetch_tweet_by_id(tweet_id)
            if tweet_data:
                result['method'] = 'api'
                result['text'] = tweet_data['text']
                result['created_at'] = tweet_data['created_at']
                
                # Check username match (case-insensitive)
                if tweet_data['author_username']:
                    result['username_match'] = (
                        tweet_data['author_username'].lower() == expected_username.lower()
                    )
                
                # Check time window
                if tweet_data['created_at']:
                    tweet_time = tweet_data['created_at']
                    if isinstance(tweet_time, str):
                        tweet_time = datetime.fromisoformat(tweet_time.replace('Z', '+00:00'))
                    result['time_window_match'] = start_time <= tweet_time <= end_time
                
                result['verified'] = result['username_match'] and result['time_window_match']
                return result
        
        # If API fails, indicate manual verification needed
        result['method'] = 'manual_required'
        logger.info(f"API verification not available for tweet {tweet_id}, manual verification required")
        return result
    
    def parse_manual_tweet_data(self, tweet_url: str, tweet_text: str, 
                               tweet_timestamp: str) -> Dict[str, Any]:
        """Parse manually submitted tweet data"""
        tweet_id = self.extract_tweet_id_from_url(tweet_url)
        username = self.extract_username_from_url(tweet_url)
        
        # Parse timestamp
        tweet_time = None
        try:
            # Try common timestamp formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M']:
                try:
                    tweet_time = datetime.strptime(tweet_timestamp, fmt)
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.error(f"Error parsing timestamp: {e}")
        
        return {
            'tweet_id': tweet_id,
            'username': username,
            'text': tweet_text,
            'timestamp': tweet_time,
            'url': tweet_url,
            'method': 'manual'
        }
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API status and rate limits"""
        status = {
            'api_configured': bool(self.client),
            'has_bearer_token': bool(self.bearer_token),
            'has_api_key': bool(self.api_key),
            'rate_limits': None
        }
        
        if self.client:
            try:
                # Get rate limit status
                limits = self.client.get_me()
                status['rate_limits'] = 'Available'
            except Exception as e:
                status['rate_limits'] = f'Error: {str(e)}'
        
        return status