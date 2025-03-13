"""
File I/O Utility for the Preorder Admin Dashboard.

This module provides functionality for reading and writing local files.
"""
import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileIO:
    """
    Utility for reading and writing local files.
    """
    
    def __init__(self, base_dir):
        """
        Initialize the file I/O utility.
        
        Args:
            base_dir (str): Base directory for file operations
        """
        self.base_dir = base_dir
        
        # Define common directories
        self.audit_dir = os.path.join(base_dir, 'audit')
        self.output_dir = os.path.join(base_dir, 'output')
        self.preorders_dir = os.path.join(base_dir, 'preorders')
        self.overrides_dir = os.path.join(base_dir, 'overrides')
        
        # Ensure directories exist
        for directory in [self.audit_dir, self.output_dir, self.preorders_dir, self.overrides_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info(f"Initialized FileIO with base directory: {base_dir}")
    
    def read_json(self, filepath, default=None):
        """
        Read a JSON file.
        
        Args:
            filepath (str): Path to the JSON file (relative or absolute)
            default: Default value to return if file doesn't exist
            
        Returns:
            dict: JSON data or default if file doesn't exist
        """
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return default
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Read JSON file: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error reading JSON file {filepath}: {e}")
            return default
    
    def write_json(self, data, filepath, indent=2):
        """
        Write data to a JSON file.
        
        Args:
            data: Data to write
            filepath (str): Path to the JSON file (relative or absolute)
            indent (int): JSON indentation level
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent)
            logger.info(f"Wrote JSON file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file {filepath}: {e}")
            return False
    
    def read_csv(self, filepath, default=None):
        """
        Read a CSV file using pandas.
        
        Args:
            filepath (str): Path to the CSV file (relative or absolute)
            default: Default value to return if file doesn't exist
            
        Returns:
            pandas.DataFrame: CSV data or default if file doesn't exist
        """
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return default
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Read CSV file: {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error reading CSV file {filepath}: {e}")
            return default
    
    def write_csv(self, df, filepath, index=False):
        """
        Write a pandas DataFrame to a CSV file.
        
        Args:
            df (pandas.DataFrame): Data to write
            filepath (str): Path to the CSV file (relative or absolute)
            index (bool): Whether to include DataFrame index
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            df.to_csv(filepath, index=index)
            logger.info(f"Wrote CSV file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error writing CSV file {filepath}: {e}")
            return False
    
    def append_csv(self, data, filepath, fieldnames=None):
        """
        Append a row or rows to a CSV file.
        
        Args:
            data (dict or list): Row(s) to append
            filepath (str): Path to the CSV file (relative or absolute)
            fieldnames (list): List of column names (required if file doesn't exist)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
        
        # Convert single row to list if needed
        if isinstance(data, dict):
            data = [data]
        
        try:
            # Determine fieldnames if not provided
            if not fieldnames:
                if file_exists:
                    # Read existing headers
                    with open(filepath, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        fieldnames = next(reader)
                elif data:
                    # Use keys from first row
                    fieldnames = list(data[0].keys())
                else:
                    logger.error(f"Cannot determine fieldnames for {filepath}")
                    return False
            
            mode = 'a' if file_exists else 'w'
            with open(filepath, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(data)
            
            logger.info(f"Appended {len(data)} row(s) to CSV file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error appending to CSV file {filepath}: {e}")
            return False
    
    def get_recent_files(self, directory, prefix=None, suffix=None, count=1):
        """
        Get the most recent files in a directory.
        
        Args:
            directory (str): Directory path (relative or absolute)
            prefix (str): File prefix filter
            suffix (str): File suffix filter
            count (int): Number of recent files to return
            
        Returns:
            list: List of file paths sorted by modification time (newest first)
        """
        # Handle relative paths
        if not os.path.isabs(directory):
            directory = os.path.join(self.base_dir, directory)
        
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return []
        
        try:
            files = os.listdir(directory)
            
            # Apply filters
            if prefix:
                files = [f for f in files if f.startswith(prefix)]
            if suffix:
                files = [f for f in files if f.endswith(suffix)]
            
            # Get absolute paths and modification times
            file_info = []
            for filename in files:
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    file_info.append((filepath, mtime))
            
            # Sort by modification time (newest first)
            file_info.sort(key=lambda x: x[1], reverse=True)
            
            # Return the specified number of files
            result = [info[0] for info in file_info[:count]]
            
            logger.info(f"Found {len(result)} recent files in {directory}")
            return result
        except Exception as e:
            logger.error(f"Error getting recent files from {directory}: {e}")
            return []
    
    def backup_file(self, filepath, backup_dir=None):
        """
        Create a backup of a file.
        
        Args:
            filepath (str): Path to the file to backup
            backup_dir (str): Directory to store backups (default: <file_dir>/backups)
            
        Returns:
            str: Path to the backup file, or None if failed
        """
        import shutil
        
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return None
        
        try:
            # Determine backup directory
            if backup_dir is None:
                backup_dir = os.path.join(os.path.dirname(filepath), 'backups')
            
            # Ensure backup directory exists
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}"
            backup_filepath = os.path.join(backup_dir, backup_filename)
            
            # Copy the file
            shutil.copy2(filepath, backup_filepath)
            
            logger.info(f"Created backup: {backup_filepath}")
            return backup_filepath
        except Exception as e:
            logger.error(f"Error creating backup of {filepath}: {e}")
            return None