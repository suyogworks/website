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

def authenticate_user(username, password):
    """Authenticate admin user"""
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
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'POST':
            # Handle login
            form_data = parse_form_data()
            
            # Extract username and password, handling both list and string formats
            username = ''
            password = ''
            
            if 'username' in form_data:
                username_val = form_data['username']
                username = escape(username_val[0] if isinstance(username_val, list) else username_val)
            
            if 'password' in form_data:
                password_val = form_data['password']
                password = password_val[0] if isinstance(password_val, list) else password_val
            
            if not username or not password:
                print(json.dumps({"success": False, "error": "Username and password are required"}))
                return
            
            if authenticate_user(username, password):
                print(json.dumps({
                    "success": True, 
                    "message": "Login successful",
                    "user": {
                        "username": username,
                        "role": "admin"
                    }
                }))
            else:
                print(json.dumps({"success": False, "error": "Invalid username or password"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main() 