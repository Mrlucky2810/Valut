import re
from typing import Optional, Tuple

class Validators:
    
    @staticmethod
    def validate_bep20_address(address: str) -> Tuple[bool, str]:
        """
        Validate BEP20 (BSC) address
        Returns: (is_valid, error_message)
        """
        if not address:
            return False, "Address cannot be empty"
        
        # Remove whitespace
        address = address.strip()
        
        # BEP20 addresses are 42 characters long and start with 0x
        bep20_pattern = r'^0x[a-fA-F0-9]{40}$'
        
        if not re.match(bep20_pattern, address):
            return False, "Invalid BEP20 address format. Must be 42 characters starting with 0x"
        
        # Check for common invalid addresses
        invalid_addresses = [
            '0x0000000000000000000000000000000000000000',  # Zero address
            '0x000000000000000000000000000000000000dead',   # Dead address
        ]
        
        if address.lower() in invalid_addresses:
            return False, "Invalid address: Cannot use zero or dead addresses"
        
        return True, "Valid BEP20 address"
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate social media username (Twitter/Instagram)
        Returns: (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
        
        # Remove @ if present
        username = username.lstrip('@').strip()
        
        # Basic length check
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return False, "Username cannot be longer than 30 characters"
        
        # Allow letters, numbers, underscores, and dots (common in social media)
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            return False, "Username can only contain letters, numbers, underscores, and dots"
        
        # Cannot start with underscore or dot
        if username.startswith('_') or username.startswith('.'):
            return False, "Username cannot start with underscore or dot"
        
        # Cannot end with underscore or dot
        if username.endswith('_') or username.endswith('.'):
            return False, "Username cannot end with underscore or dot"
        
        # Cannot have consecutive special characters
        if '__' in username or '..' in username or '._' in username or '_.' in username:
            return False, "Username cannot contain consecutive special characters"
        
        return True, "Valid username"
    
    @staticmethod
    def validate_screenshot(file_size: int, file_name: str) -> Tuple[bool, str]:
        """
        Validate screenshot file
        Returns: (is_valid, error_message)
        """
        # File size limit (5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        
        if file_size > max_size:
            return False, "File size too large. Maximum 5MB allowed"
        
        # Valid image extensions
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        if not any(file_name.lower().endswith(ext) for ext in valid_extensions):
            return False, "Invalid file type. Please send image files only (jpg, png, gif, etc.)"
        
        return True, "Valid screenshot"