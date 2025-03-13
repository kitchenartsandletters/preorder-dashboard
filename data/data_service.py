"""
Data Service for the Preorder Admin Dashboard.

This module provides a unified interface for accessing data from various sources:
- Shopify API (product and order data)
- GitHub (approval issues)
- Local files (overrides, tracking data)
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta

# Import data connectors
from data.shopify_api import ShopifyConnector
from data.github_api import GitHubConnector
from data.file_io import FileIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataService:
    """
    Unified data service for the Preorder Admin Dashboard.
    """
    
    def __init__(self, base_dir=None, test_mode=False):
        """
        Initialize the data service.
        
        Args:
            base_dir (str): Base directory for file operations
            test_mode (bool): If True, use test data instead of API calls
        """
        self.test_mode = test_mode
        
        # Set base directory - default to project root
        if base_dir:
            self.base_dir = base_dir
        else:
            # Get project root (parent of current directory)
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        logger.info(f"Initializing DataService with base_dir: {self.base_dir}")
        logger.info(f"Test mode: {test_mode}")
        
        # Initialize connectors
        self.file_io = FileIO(self.base_dir)
        
        if not test_mode:
            self.shopify = ShopifyConnector()
            self.github = GitHubConnector()
        else:
            logger.info("Running in test mode - using simulated data")
            
    def get_preorder_products(self, limit=100):
        """
        Get all preorder products from Shopify.
        
        Args:
            limit (int): Maximum number of products to return
            
        Returns:
            list: List of preorder products
        """
        if self.test_mode:
            return self._get_test_preorder_products(limit)
        
        try:
            # Get products from Shopify preorder collection
            products = self.shopify.get_products_from_collection("preorder", limit=limit)
            if products is not None:
                logger.info(f"Retrieved {len(products)} preorder products from Shopify")
                return products
            else:
                logger.warning("No products returned from Shopify API, using test data instead")
                return self._get_test_preorder_products(limit)
        except Exception as e:
            logger.error(f"Error retrieving preorder products: {e}")
            logger.info("Falling back to test data due to API error")
            return self._get_test_preorder_products(limit)
    
    def get_pending_releases(self):
        """
        Get pending releases from the most recent audit file.
        
        Returns:
            dict: Pending releases data
        """
        if self.test_mode:
            return self._get_test_pending_releases()
        
        try:
            # Find the most recent pending releases file
            audit_dir = os.path.join(self.base_dir, 'audit')
            pending_files = [f for f in os.listdir(audit_dir) 
                           if f.startswith('pending_releases_') and f.endswith('.json')]
            
            if not pending_files:
                logger.warning("No pending releases files found")
                return {"pending_releases": [], "error_cases": [], "total_quantity": 0}
            
            # Get the most recent file
            pending_files.sort(reverse=True)
            latest_file = os.path.join(audit_dir, pending_files[0])
            
            # Read the file
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Retrieved {len(data.get('pending_releases', []))} pending releases from {latest_file}")
            return data
        except Exception as e:
            logger.error(f"Error retrieving pending releases: {e}")
            return {"pending_releases": [], "error_cases": [], "total_quantity": 0}
    
    def get_preorder_tracking_data(self):
        """
        Get preorder tracking data from the tracking CSV.
        
        Returns:
            pandas.DataFrame: Preorder tracking data
        """
        if self.test_mode:
            return self._get_test_preorder_tracking_data()
        
        try:
            # Get preorder tracking data from CSV
            tracking_file = os.path.join(self.base_dir, 'preorders', 'NYT_preorder_tracking.csv')
            if not os.path.exists(tracking_file):
                logger.warning(f"Preorder tracking file not found: {tracking_file}")
                return pd.DataFrame(columns=['ISBN', 'Title', 'Pub Date', 'Quantity', 'Status'])
            
            tracking_data = pd.read_csv(tracking_file)
            logger.info(f"Retrieved {len(tracking_data)} preorder tracking records")
            return tracking_data
        except Exception as e:
            logger.error(f"Error retrieving preorder tracking data: {e}")
            return pd.DataFrame(columns=['ISBN', 'Title', 'Pub Date', 'Quantity', 'Status'])
    
    def get_pub_date_overrides(self):
        """
        Get publication date overrides from the overrides CSV.
        
        Returns:
            dict: Publication date overrides mapping ISBN to corrected date
        """
        if self.test_mode:
            return self._get_test_pub_date_overrides()
        
        try:
            override_file = os.path.join(self.base_dir, 'overrides', 'pub_date_overrides.csv')
            if not os.path.exists(override_file):
                logger.warning(f"Pub date overrides file not found: {override_file}")
                return {}
            
            # Read the overrides file
            overrides_df = pd.read_csv(override_file)
            
            # Convert to dictionary
            overrides = {}
            for _, row in overrides_df.iterrows():
                if 'ISBN' in row and 'Corrected_Pub_Date' in row:
                    overrides[row['ISBN']] = row['Corrected_Pub_Date']
            
            logger.info(f"Retrieved {len(overrides)} publication date overrides")
            return overrides
        except Exception as e:
            logger.error(f"Error retrieving publication date overrides: {e}")
            return {}
    
    def update_pub_date_override(self, isbn, corrected_date):
        """
        Update or add a publication date override.
        
        Args:
            isbn (str): ISBN of the book
            corrected_date (str): Corrected publication date in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.test_mode:
            logger.info(f"Test mode: Would update override for ISBN {isbn} to {corrected_date}")
            return True
        
        try:
            override_file = os.path.join(self.base_dir, 'overrides', 'pub_date_overrides.csv')
            override_dir = os.path.dirname(override_file)
            
            # Create directory if it doesn't exist
            os.makedirs(override_dir, exist_ok=True)
            
            # Load existing overrides
            if os.path.exists(override_file):
                overrides_df = pd.read_csv(override_file)
            else:
                # Create new DataFrame with required columns
                overrides_df = pd.DataFrame(columns=['ISBN', 'Corrected_Pub_Date', 'Notes', 'Updated_At'])
            
            # Check if ISBN already exists
            if 'ISBN' in overrides_df.columns and isbn in overrides_df['ISBN'].values:
                # Update existing override
                idx = overrides_df[overrides_df['ISBN'] == isbn].index[0]
                overrides_df.at[idx, 'Corrected_Pub_Date'] = corrected_date
                overrides_df.at[idx, 'Updated_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Add new override
                new_row = {
                    'ISBN': isbn,
                    'Corrected_Pub_Date': corrected_date,
                    'Notes': 'Added via dashboard',
                    'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                overrides_df = pd.concat([overrides_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save the updated overrides
            overrides_df.to_csv(override_file, index=False)
            logger.info(f"Updated publication date override for ISBN {isbn} to {corrected_date}")
            return True
        except Exception as e:
            logger.error(f"Error updating publication date override: {e}")
            return False
    
    def get_approval_status(self):
        """
        Get approval status from GitHub issues.
        
        Returns:
            list: List of approval issues with status information
        """
        if self.test_mode:
            return self._get_test_approval_status()
        
        try:
            # Get approval issues from GitHub
            issues = self.github.get_issues(label="preorder-approval")
            
            approval_status = []
            for issue in issues:
                # Parse the issue body to extract ISBNs and approval status
                approved_isbns = self._parse_issue_body(issue['body'])
                
                approval_status.append({
                    'issue_number': issue['number'],
                    'title': issue['title'],
                    'created_at': issue['created_at'],
                    'status': issue['state'],
                    'approved_isbns': approved_isbns,
                    'url': issue['html_url']
                })
            
            logger.info(f"Retrieved {len(approval_status)} approval issues")
            return approval_status
        except Exception as e:
            logger.error(f"Error retrieving approval status: {e}")
            return []
    
    def _parse_issue_body(self, issue_body):
        """
        Parse GitHub issue body to extract approved ISBNs.
        
        Args:
            issue_body (str): GitHub issue body text
            
        Returns:
            list: List of approved ISBN strings
        """
        import re
        approved_isbns = []
        
        # Find checkboxes with [x] in the table
        lines = issue_body.split('\n')
        for line in lines:
            # Match lines that have a checked box
            if re.search(r'\|\s*\[x\]', line, re.IGNORECASE):
                # Extract ISBN from the line (assuming it's the second column)
                match = re.search(r'\|\s*\[x\]\s*\|\s*([0-9]+)', line, re.IGNORECASE)
                if match:
                    isbn = match.group(1)
                    approved_isbns.append(isbn)
        
        return approved_isbns
    
    # Test data methods
    def _get_test_preorder_products(self, limit=100):
        """Generate test preorder product data."""
        today = datetime.now().date()
        future_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        recent_date = (today - timedelta(days=3)).strftime('%Y-%m-%d')
        past_date = (today - timedelta(days=60)).strftime('%Y-%m-%d')
        
        test_products = [
            {
                "id": "gid://shopify/Product/1111111111",
                "title": "Future Release Book",
                "barcode": "9781234567890",
                "pub_date": future_date,
                "collections": ["Preorder", "Fiction"]
            },
            {
                "id": "gid://shopify/Product/2222222222",
                "title": "Recent Release Book",
                "barcode": "9781234567891",
                "pub_date": recent_date,
                "collections": ["Preorder", "Non-fiction"]
            },
            {
                "id": "gid://shopify/Product/3333333333",
                "title": "Past Due Book",
                "barcode": "9781234567892",
                "pub_date": past_date,
                "collections": ["Preorder", "Science Fiction"]
            },
            {
                "id": "gid://shopify/Product/4444444444",
                "title": "Missing Date Book",
                "barcode": "9781234567893",
                "pub_date": None,
                "collections": ["Preorder", "Mystery"]
            },
            {
                "id": "gid://shopify/Product/5555555555",
                "title": "Malformed Date Book",
                "barcode": "9781234567894",
                "pub_date": "Coming Soon",
                "collections": ["Preorder", "Poetry"]
            }
        ]
        
        return test_products[:limit]
    
    def _get_test_pending_releases(self):
        """Generate test pending releases data."""
        return {
            "pending_releases": [
                {
                    "isbn": "9780262551311",
                    "title": "Modern Chinese Foodways",
                    "quantity": 2,
                    "original_pub_date": "2025-03-03",
                    "overridden_pub_date": None,
                    "reason": "No longer in preorder status"
                },
                {
                    "isbn": "9784756256522",
                    "title": "Fishes of Edo: A Guide to Classical Japanese Fishes",
                    "quantity": 10,
                    "original_pub_date": "2025-03-04",
                    "overridden_pub_date": None,
                    "reason": "No longer in preorder status"
                }
            ],
            "error_cases": [],
            "total_quantity": 12,
            "run_date": datetime.now().strftime("%Y-%m-%d"),
            "total_pending_books": 2
        }
    
    def _get_test_preorder_tracking_data(self):
        """Generate test preorder tracking data."""
        data = {
            'ISBN': [
                '9781234567890', '9781234567891', '9781234567892',
                '9781234567893', '9781234567894'
            ],
            'Title': [
                'Future Release Book', 'Recent Release Book', 'Past Due Book',
                'Missing Date Book', 'Malformed Date Book'
            ],
            'Pub Date': [
                (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d'),
                (datetime.now().date() - timedelta(days=3)).strftime('%Y-%m-%d'),
                (datetime.now().date() - timedelta(days=60)).strftime('%Y-%m-%d'),
                None, 'Coming Soon'
            ],
            'Quantity': [5, 3, 8, 2, 4],
            'Status': ['Preorder', 'Preorder', 'Preorder', 'Preorder', 'Preorder']
        }
        return pd.DataFrame(data)
    
    def _get_test_pub_date_overrides(self):
        """Generate test publication date overrides."""
        today = datetime.now().date()
        return {
            '9781234567890': (today + timedelta(days=45)).strftime('%Y-%m-%d'),
            '9781234567892': (today + timedelta(days=15)).strftime('%Y-%m-%d')
        }
    
    def _get_test_approval_status(self):
        """Generate test approval status data."""
        return [
            {
                'issue_number': 123,
                'title': 'Preorder Approvals for Week of March 10, 2025',
                'created_at': '2025-03-10T12:00:00Z',
                'status': 'open',
                'approved_isbns': ['9780262551311', '9784756256522'],
                'url': 'https://github.com/example/repo/issues/123'
            },
            {
                'issue_number': 120,
                'title': 'Preorder Approvals for Week of March 3, 2025',
                'created_at': '2025-03-03T12:00:00Z',
                'status': 'closed',
                'approved_isbns': ['9781234567895', '9781234567896'],
                'url': 'https://github.com/example/repo/issues/120'
            }
        ]