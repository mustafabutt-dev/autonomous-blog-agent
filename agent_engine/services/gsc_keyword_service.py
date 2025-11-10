"""
Google Search Console Keyword Service
Fetches real keyword data from your verified website
"""

from .base_keyword_service import BaseKeywordService
from typing import Dict, List
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class GSCKeywordService(BaseKeywordService):
    """
    Fetch keywords from Google Search Console
    """
    
    def __init__(self):
        self.credentials_path = os.getenv("GSC_CREDENTIALS_PATH")
        self.site_url = os.getenv("GSC_SITE_URL")
        self.service = None
        
        if self.is_available():
            self._initialize_service()
    
    def _initialize_service(self):
        """Initialize GSC API service"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/webmasters.readonly']
            )
            self.service = build('searchconsole', 'v1', credentials=credentials)
            print(" GSC Service initialized")
        except Exception as e:
            print(f" GSC initialization error: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if GSC credentials are configured"""
        available = bool(self.credentials_path and self.site_url)
        if not available:
            print("  GSC not configured - set GSC_CREDENTIALS_PATH and GSC_SITE_URL")
        return available
    
    async def fetch_keywords(self, topic: str, product_name: str = None) -> Dict:
        """
        Fetch keywords from GSC for the given topic
        """
        
        if not self.is_available() or not self.service:
            return self._empty_result()
        
        try:
            # Query last 90 days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            request_body = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query'],
                'rowLimit': 100,  # Get top 100 queries
                'dimensionFilterGroups': []
            }
            
            # Filter by topic if possible
            if topic:
                request_body['dimensionFilterGroups'] = [{
                    'filters': [{
                        'dimension': 'query',
                        'operator': 'contains',
                        'expression': topic.lower()
                    }]
                }]
            
            # Execute query
            response = self.service.searchanalytics().query(
                siteUrl=self.site_url,
                body=request_body
            ).execute()
            
            # Process results
            rows = response.get('rows', [])
            
            if not rows:
                print(f"  No GSC data found for topic: {topic}")
                return self._empty_result()
            
            # Categorize keywords by performance
            keywords_with_metrics = [
                {
                    'keyword': row['keys'][0],
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0),
                    'position': row.get('position', 100)
                }
                for row in rows
            ]
            
            # Sort and categorize
            primary = self._extract_primary_keywords(keywords_with_metrics)
            secondary = self._extract_secondary_keywords(keywords_with_metrics)
            long_tail = self._extract_long_tail_keywords(keywords_with_metrics)
            
            return {
                "source": "Google Search Console",
                "primary": primary,
                "secondary": secondary,
                "long_tail": long_tail,
                "metadata": {
                    "total_keywords": len(rows),
                    "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "site": self.site_url
                }
            }
            
        except Exception as e:
            print(f" GSC API Error: {e}")
            return self._empty_result()
    
    def _extract_primary_keywords(self, keywords: List[dict]) -> List[str]:
        """Extract primary keywords (high clicks, good position)"""
        # Top performers: position < 20 and clicks > 10
        primary = [
            kw['keyword'] for kw in keywords
            if kw['position'] < 20 and kw['clicks'] > 10
        ]
        return primary[:10]  # Top 10
    
    def _extract_secondary_keywords(self, keywords: List[dict]) -> List[str]:
        """Extract secondary keywords (decent performance)"""
        # Medium performers: position < 50, some clicks
        secondary = [
            kw['keyword'] for kw in keywords
            if 20 <= kw['position'] < 50 and kw['clicks'] > 0
        ]
        return secondary[:10]
    
    def _extract_long_tail_keywords(self, keywords: List[dict]) -> List[str]:
        """Extract long-tail keywords (high potential, lower traffic)"""
        # Long tail: good position but low clicks (opportunity!)
        long_tail = [
            kw['keyword'] for kw in keywords
            if kw['position'] < 30 and kw['clicks'] < 10 and len(kw['keyword'].split()) >= 3
        ]
        return long_tail[:10]
    
    def _empty_result(self) -> Dict:
        """Return empty result when service unavailable"""
        return {
            "source": "Google Search Console",
            "primary": [],
            "secondary": [],
            "long_tail": [],
            "metadata": {"available": False}
        }