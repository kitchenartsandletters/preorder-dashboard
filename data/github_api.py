"""
GitHub API Connector for the Preorder Admin Dashboard.

This module provides functionality to interact with the GitHub API.
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

class GitHubConnector:
    """
    Connector for GitHub API.
    """
    
    def __init__(self):
        """
        Initialize the GitHub connector.
        """
        # Load environment variables
        load_dotenv('.env.production')
        
        # Get API credentials
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPOSITORY', 'owner/repo')
        
        if not self.github_token:
            logger.error("Missing GitHub API token")
            raise ValueError("Missing required environment variable: GITHUB_TOKEN")
        
        # Split repository into owner and repo
        try:
            self.repo_owner, self.repo_name = self.github_repo.split('/')
        except ValueError:
            logger.error(f"Invalid GitHub repository format: {self.github_repo}")
            raise ValueError(f"Invalid GitHub repository format: {self.github_repo}")
        
        # Set API URL
        self.api_base_url = "https://api.github.com"
        
        # Set headers
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.github_token}"
        }
        
        logger.info(f"Initialized GitHub connector for repository {self.github_repo}")
    
    def get_issues(self, state="all", label=None, limit=100):
        """
        Get issues from the repository.
        
        Args:
            state (str): Issue state (open, closed, all)
            label (str): Filter by label
            limit (int): Maximum number of issues to return
            
        Returns:
            list: List of issues
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
        
        params = {
            "state": state,
            "per_page": min(limit, 100),  # GitHub API limits to 100 per page
        }
        
        if label:
            params["labels"] = label
        
        issues = []
        page = 1
        
        try:
            while len(issues) < limit:
                params["page"] = page
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Error fetching issues: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    break
                
                page_issues = response.json()
                
                if not page_issues:
                    break  # No more issues
                
                issues.extend(page_issues)
                
                if len(page_issues) < params["per_page"]:
                    break  # Last page
                
                page += 1
            
            # Truncate to requested limit
            issues = issues[:limit]
            
            logger.info(f"Retrieved {len(issues)} issues with state='{state}'{f' and label={label}' if label else ''}")
            return issues
            
        except Exception as e:
            logger.error(f"Error retrieving issues: {e}")
            return []
    
    def get_issue(self, issue_number):
        """
        Get a specific issue by number.
        
        Args:
            issue_number (int): Issue number
            
        Returns:
            dict: Issue data or None if not found
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching issue {issue_number}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            issue = response.json()
            logger.info(f"Retrieved issue #{issue_number}: {issue.get('title')}")
            return issue
            
        except Exception as e:
            logger.error(f"Error retrieving issue {issue_number}: {e}")
            return None
    
    def create_issue(self, title, body, labels=None):
        """
        Create a new issue.
        
        Args:
            title (str): Issue title
            body (str): Issue body
            labels (list): List of label names
            
        Returns:
            dict: Created issue data or None if failed
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
        
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code != 201:
                logger.error(f"Error creating issue: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            issue = response.json()
            logger.info(f"Created issue #{issue.get('number')}: {issue.get('title')}")
            return issue
            
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return None
    
    def update_issue(self, issue_number, title=None, body=None, state=None, labels=None):
        """
        Update an existing issue.
        
        Args:
            issue_number (int): Issue number
            title (str): New title (optional)
            body (str): New body (optional)
            state (str): New state (open, closed) (optional)
            labels (list): New list of label names (optional)
            
        Returns:
            dict: Updated issue data or None if failed
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
        
        data = {}
        
        if title is not None:
            data["title"] = title
        
        if body is not None:
            data["body"] = body
        
        if state is not None:
            data["state"] = state
        
        if labels is not None:
            data["labels"] = labels
        
        if not data:
            logger.warning(f"No update data provided for issue {issue_number}")
            return None
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"Error updating issue {issue_number}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            issue = response.json()
            logger.info(f"Updated issue #{issue_number}: {issue.get('title')}")
            return issue
            
        except Exception as e:
            logger.error(f"Error updating issue {issue_number}: {e}")
            return None
    
    def add_comment(self, issue_number, body):
        """
        Add a comment to an issue.
        
        Args:
            issue_number (int): Issue number
            body (str): Comment body
            
        Returns:
            dict: Created comment data or None if failed
        """
        url = f"{self.api_base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
        
        data = {
            "body": body
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code != 201:
                logger.error(f"Error adding comment to issue {issue_number}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            comment = response.json()
            logger.info(f"Added comment to issue #{issue_number}")
            return comment
            
        except Exception as e:
            logger.error(f"Error adding comment to issue {issue_number}: {e}")
            return None