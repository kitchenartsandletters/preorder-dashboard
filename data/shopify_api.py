"""
Shopify API Connector for the Preorder Admin Dashboard.

This module provides functionality to interact with the Shopify GraphQL API.
"""
import os
import requests
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShopifyConnector:
    """
    Connector for Shopify GraphQL API.
    """
    
    def __init__(self):
        """
        Initialize the Shopify connector.
        """
        # Load environment variables
        load_dotenv('.env.production')
        
        # Get API credentials
        self.shop_url = os.getenv('SHOP_URL')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        
        if not self.shop_url or not self.access_token:
            logger.error("Missing Shopify API credentials")
            raise ValueError("Missing required environment variables: SHOP_URL, SHOPIFY_ACCESS_TOKEN")
        
        # Ensure shop URL is properly formatted
        if not self.shop_url.startswith(('http://', 'https://')):
            self.shop_url = f"https://{self.shop_url}"
        
        # Remove trailing slash if present
        if self.shop_url.endswith('/'):
            self.shop_url = self.shop_url[:-1]
        
        # Set GraphQL URL
        self.graphql_url = f"{self.shop_url}/admin/api/2025-01/graphql.json"
        
        # Set headers
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token
        }
        
        logger.info(f"Initialized Shopify connector with URL: {self.graphql_url}")
    
    def run_query_with_retries(self, query, variables, max_retries=3, delay=1):
        """
        Run a GraphQL query with retry logic.
        
        Args:
            query (str): GraphQL query
            variables (dict): Query variables
            max_retries (int): Maximum number of retry attempts
            delay (int): Delay between retries in seconds
            
        Returns:
            dict: Query response data
        """
        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.post(
                    self.graphql_url,
                    json={'query': query, 'variables': variables},
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error: Received status code {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    attempt += 1
                    time.sleep(delay)
                    continue
                    
                data = response.json()
                
                if 'errors' in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    attempt += 1
                    time.sleep(delay)
                    continue
                    
                return data['data']
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(delay)
                
        raise Exception(f"Failed to execute query after {max_retries} attempts")
    
    def get_products_from_collection(self, collection_handle, limit=250):
        """
        Get products from a specific collection.
        
        Args:
            collection_handle (str): Collection handle (e.g., "preorder")
            limit (int): Maximum number of products to return
            
        Returns:
            list: List of products in the collection
        """
        query = """
        query($handle: String!, $first: Int!) {
            collectionByHandle(handle: $handle) {
                products(first: $first) {
                    edges {
                        node {
                            id
                            title
                            variants(first: 1) {
                                edges {
                                    node {
                                        barcode
                                    }
                                }
                            }
                            metafields(first: 10, namespace: "custom") {
                                edges {
                                    node {
                                        key
                                        value
                                    }
                                }
                            }
                            collections(first: 5) {
                                edges {
                                    node {
                                        title
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "handle": collection_handle,
            "first": limit
        }
        
        try:
            data = self.run_query_with_retries(query, variables)
            product_edges = data.get('collectionByHandle', {}).get('products', {}).get('edges', [])
            
            products = []
            for edge in product_edges:
                product = edge['node']
                
                # Get barcode (ISBN)
                barcode = None
                if product.get('variants', {}).get('edges'):
                    barcode = product['variants']['edges'][0]['node'].get('barcode')
                
                # Get pub_date
                pub_date = None
                metafields = product.get('metafields', {}).get('edges', [])
                for metafield in metafields:
                    if metafield['node']['key'] == 'pub_date':
                        pub_date = metafield['node']['value']
                        break
                
                # Get collections
                collections = []
                collection_edges = product.get('collections', {}).get('edges', [])
                for collection_edge in collection_edges:
                    collections.append(collection_edge['node']['title'])
                
                products.append({
                    'id': product['id'],
                    'title': product['title'],
                    'barcode': barcode,
                    'pub_date': pub_date,
                    'collections': collections
                })
            
            logger.info(f"Retrieved {len(products)} products from collection '{collection_handle}'")
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving products from collection '{collection_handle}': {e}")
            return []
    
    def get_product_by_barcode(self, barcode):
        """
        Get a product by its barcode (ISBN).
        
        Args:
            barcode (str): Product barcode/ISBN
            
        Returns:
            dict: Product data or None if not found
        """
        query = """
        query($query: String!) {
            products(first: 1, query: $query) {
                edges {
                    node {
                        id
                        title
                        variants(first: 1) {
                            edges {
                                node {
                                    barcode
                                }
                            }
                        }
                        metafields(first: 10, namespace: "custom") {
                            edges {
                                node {
                                    key
                                    value
                                }
                            }
                        }
                        collections(first: 5) {
                            edges {
                                node {
                                    title
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "query": f"barcode:{barcode}"
        }
        
        try:
            data = self.run_query_with_retries(query, variables)
            product_edges = data.get('products', {}).get('edges', [])
            
            if not product_edges:
                logger.warning(f"No product found with barcode '{barcode}'")
                return None
            
            product = product_edges[0]['node']
            
            # Get pub_date
            pub_date = None
            metafields = product.get('metafields', {}).get('edges', [])
            for metafield in metafields:
                if metafield['node']['key'] == 'pub_date':
                    pub_date = metafield['node']['value']
                    break
            
            # Get collections
            collections = []
            collection_edges = product.get('collections', {}).get('edges', [])
            for collection_edge in collection_edges:
                collections.append(collection_edge['node']['title'])
            
            return {
                'id': product['id'],
                'title': product['title'],
                'barcode': barcode,
                'pub_date': pub_date,
                'collections': collections
            }
            
        except Exception as e:
            logger.error(f"Error retrieving product with barcode '{barcode}': {e}")
            return None
    
    def get_preorder_sales(self, days=30):
        """
        Get preorder sales data for the last N days.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            list: List of preorder sales
        """
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        query($first: Int!, $query: String!, $after: String) {
            orders(first: $first, query: $query, after: $after, reverse: false) {
                edges {
                    cursor
                    node {
                        id
                        name
                        createdAt
                        cancelledAt
                        
                        lineItems(first: 25) {
                            edges {
                                node {
                                    id
                                    name
                                    quantity
                                    variant {
                                        id
                                        barcode
                                        product {
                                            id
                                            title
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                }
            }
        }
        """
        
        variables = {
            "first": 250,
            "query": f'created_at:>="{start_date.strftime("%Y-%m-%d")}"',
            "after": None
        }
        
        try:
            preorder_sales = []
            has_next_page = True
            cursor = None
            
            while has_next_page:
                variables["after"] = cursor
                data = self.run_query_with_retries(query, variables)
                
                orders = data.get('orders', {})
                order_edges = orders.get('edges', [])
                
                for edge in order_edges:
                    order = edge['node']
                    
                    # Skip cancelled orders
                    if order.get('cancelledAt'):
                        continue
                    
                    # Process line items
                    line_items = order.get('lineItems', {}).get('edges', [])
                    for item in line_items:
                        line_item = item['node']
                        variant = line_item.get('variant')
                        
                        if variant and variant.get('barcode') and variant.get('product'):
                            product = variant['product']
                            
                            # Check if this is a preorder product
                            # This would require an additional API call to check collections
                            # For now, we'll collect all line items with barcodes starting with 978/979
                            barcode = variant['barcode']
                            if barcode and (str(barcode).startswith('978') or str(barcode).startswith('979')):
                                preorder_sales.append({
                                    'order_id': order['id'],
                                    'order_name': order['name'],
                                    'created_at': order['createdAt'],
                                    'barcode': barcode,
                                    'title': product['title'],
                                    'quantity': line_item['quantity']
                                })
                
                # Check if there are more pages
                has_next_page = orders.get('pageInfo', {}).get('hasNextPage', False)
                if has_next_page and order_edges:
                    cursor = order_edges[-1]['cursor']
            
            logger.info(f"Retrieved {len(preorder_sales)} preorder sales for the last {days} days")
            return preorder_sales
            
        except Exception as e:
            logger.error(f"Error retrieving preorder sales: {e}")
            return []