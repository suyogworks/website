#!/usr/bin/env python3
"""
Team management API
Handles CRUD operations for team members
"""

import json
import os
import sys
import urllib.parse
import sqlite3
import re
from html import escape
from logger_config import get_logger # Import the logger
import uuid # For file uploads, though not used in current version of team_api.py

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
    return sqlite3.connect(db_path)

def get_all_team_members():
    """Get all team members"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, title, bio, photo_url FROM team ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    team = []
    for row in rows:
        team.append({
            'id': row[0],
            'name': row[1],
            'title': row[2],
            'bio': row[3],
            'photo_url': row[4]
        })
    
    return team

def add_team_member(data):
    """Add new team member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO team (name, title, bio, photo_url) 
        VALUES (?, ?, ?, ?)
    ''', (data['name'], data['title'], data.get('bio', ''), data.get('photo_url', '')))
    
    member_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return member_id

def delete_team_member(member_id):
    """Delete team member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM team WHERE id = ?', (member_id,))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected > 0

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
    print("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS") # Added PUT
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    
    try:
        method = os.environ.get('REQUEST_METHOD', 'GET')
        logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

        if method == 'OPTIONS':
            logger.info("Handling OPTIONS request.")
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'GET':
            logger.info("Handling GET request for all team members.")
            team = get_all_team_members()
            print(json.dumps({"success": True, "data": team}))
            
        elif method == 'POST':
            logger.info("Handling POST request for new team member.")
            form_data = parse_form_data() # This function might need logging if it were more complex
            
            name = escape(form_data.get('name', [''])[0] if isinstance(form_data.get('name'), list) else form_data.get('name', ''))
            title = escape(form_data.get('title', [''])[0] if isinstance(form_data.get('title'), list) else form_data.get('title', ''))
            bio = escape(form_data.get('bio', [''])[0] if isinstance(form_data.get('bio'), list) else form_data.get('bio', ''))
            photo_url = form_data.get('photo_url', [''])[0] if isinstance(form_data.get('photo_url'), list) else form_data.get('photo_url', '')
            # Not escaping photo_url as it's a URL

            data = {'name': name, 'title': title, 'bio': bio, 'photo_url': photo_url}
            logger.debug(f"Parsed data for POST: {data}")
            
            if not data['name'] or not data['title']:
                logger.warning("POST attempt with missing name or title for team member.")
                print(json.dumps({"success": False, "error": "Name and title are required"}))
                return
            
            member_id = add_team_member(data)
            logger.info(f"Team member added with ID: {member_id}")
            print(json.dumps({"success": True, "id": member_id, "message": "Team member added successfully"}))

        elif method == 'PUT':
            # PUT for team members is not fully implemented in this version of team_api.py
            # The dashboard.js might attempt to use it.
            logger.warning(f"Received PUT request for team member, but update functionality is not implemented in this API version.")
            # To make it behave somewhat predictably if called:
            query_string = os.environ.get('QUERY_STRING', '')
            member_id_to_update_str = query_string.split('id=')[-1] if 'id=' in query_string else None
            # form_data = parse_form_data() # If it were implemented, you'd parse data here
            # logger.debug(f"Data received for unimplemented PUT: ID={member_id_to_update_str}, Form Data (summary)={ {k:v for k,v in form_data.items() if k != 'photo'} }")
            print(json.dumps({"success": False, "error": "Update (PUT) for team members is not implemented in this API version."}))

        elif method == 'DELETE':
            query_string = os.environ.get('QUERY_STRING', '')
            logger.info(f"Handling DELETE request for team member. Query: {query_string}")
            if 'id=' in query_string:
                try:
                    member_id_str = query_string.split('id=')[1].split('&')[0]
                    member_id = int(member_id_str)
                    if delete_team_member(member_id):
                        logger.info(f"Team member with ID: {member_id} deleted successfully.")
                        print(json.dumps({"success": True, "message": "Team member deleted successfully"}))
                    else:
                        logger.warning(f"Team member with ID: {member_id} not found for deletion.")
                        print(json.dumps({"success": False, "error": "Team member not found"})) # More specific
                except ValueError:
                    logger.error(f"Invalid Member ID for DELETE: {member_id_str}")
                    print(json.dumps({"success": False, "error": "Invalid Member ID format."}))
            else:
                logger.warning("Member ID required for DELETE but not provided.")
                print(json.dumps({"success": False, "error": "Member ID required"})) # More specific
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()