# gui/utils/form_validation.py
from typing import Dict, List, Tuple
import re
from datetime import datetime

class FormValidator:
    """
    Utility class for form validation with common validation methods.
    """
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        Validate date string format (YYYY-MM-DD) and value.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date is valid, False otherwise
        """
        try:
            if not date_str:
                return False
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_name(name: str) -> bool:
        """
        Validate person name format.
        
        Args:
            name: Name string to validate
            
        Returns:
            True if name is valid, False otherwise
        """
        if not name:
            return False
        # Allow letters, spaces, hyphens, and apostrophes
        return bool(re.match(r"^[A-Za-z\s\-']+$", name))

    @staticmethod
    def validate_folder_name(name: str) -> bool:
        """
        Validate folder name format.
        
        Args:
            name: Folder name to validate
            
        Returns:
            True if folder name is valid, False otherwise
        """
        if not name:
            return False
        # Allow letters, numbers, underscores, and hyphens
        return bool(re.match(r"^[A-Za-z0-9_-]+$", name))