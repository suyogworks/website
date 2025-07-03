#!/usr/bin/env python3
"""
Authentication API for Matrica Networks admin panel
Handles admin login and session management
"""

import json
import os
import sys
import urllib.parse
import re
from html import escape
from logger_config import get_logger # Import the logger

# Initialize logger for this script
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

def authenticate_user(username, password):
    """Authenticate admin user"""
    logger.debug(f"Attempting to authenticate user: {username}")
    # Hardcoded credentials for demo purposes
    # In production, this should use a secure database with hashed passwords
    valid_credentials = {
        'psychy': 'Scambanenabler'
    }
    
    return username in valid_credentials and valid_credentials[username] == password

def parse_multipart_form_data(post_data):
    """Parse multipart/form-data format"""
    form_data = {}
    
    # Extract boundary from Content-Type header
    content_type = os.environ.get('CONTENT_TYPE', '')
    boundary_match = re.search(r'boundary=([^;]+)', content_type)
    if not boundary_match:
        return form_data
    
    boundary = '--' + boundary_match.group(1)
    
    # Split by boundary
    parts = post_data.split(boundary)
    
    for part in parts:
        if not part.strip() or part.strip() == '--':
            continue
            
        # Parse each part
        lines = part.split('\r\n')
        if len(lines) < 3:
            continue
            
        # Extract field name
        content_disposition = lines[1]
        name_match = re.search(r'name="([^"]+)"', content_disposition)
        if not name_match:
            continue
            
        field_name = name_match.group(1)
        
        # Extract field value (everything after the empty line)
        value_lines = []
        for i, line in enumerate(lines):
            if line.strip() == '':
                value_lines = lines[i+1:]
                break
        
        field_value = '\r\n'.join(value_lines).strip()
        form_data[field_name] = field_value
    
    return form_data

def parse_form_data():
    """Parse form data from POST request"""
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    if content_length > 0:
        post_data = sys.stdin.read(content_length)
        
        content_type = os.environ.get('CONTENT_TYPE', '')
        
        # Check if it's multipart form data
        if 'multipart/form-data' in content_type:
            parsed_data = parse_multipart_form_data(post_data)
        else:
            # Try to parse as URL-encoded form data
            try:
                parsed_data = urllib.parse.parse_qs(post_data)
            except Exception as e:
                parsed_data = {}
        
        return parsed_data
    return {}

def main():
    """Main handler function"""
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    
    try:
        method = os.environ.get('REQUEST_METHOD', 'GET')
        logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

        if method == 'OPTIONS':
            logger.info("Handling OPTIONS request.")
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'POST':
            logger.info("Processing POST request for login.")
            form_data = parse_form_data()
            
            username_val = form_data.get('username', [''])[0] if isinstance(form_data.get('username'), list) else form_data.get('username', '')
            username = escape(username_val)
            
            password_val = form_data.get('password', [''])[0] if isinstance(form_data.get('password'), list) else form_data.get('password', '')
            # Password is not escaped as it's used for comparison, not display. It's also not logged directly.

            if not username or not password_val:
                logger.warning("Login attempt with missing username or password.")
                print(json.dumps({"success": False, "error": "Username and password are required"}))
                return
            
            if authenticate_user(username, password_val):
                logger.info(f"User '{username}' authenticated successfully.")
                print(json.dumps({
                    "success": True, 
                    "message": "Login successful",
                    "user": {
                        "username": username,
                        "role": "admin"
                    }
                }))
            else:
                logger.warning(f"Failed login attempt for user '{username}'.")
                print(json.dumps({"success": False, "error": "Invalid username or password"}))
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))

if __name__ == "__main__":
    logger.info("auth_api.py script started (likely direct execution or misconfiguration).")
    main()