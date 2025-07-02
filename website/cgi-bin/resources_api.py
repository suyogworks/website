#!/usr/bin/env python3
"""
Resources management API
Handles CRUD operations for resources
"""

import json
import os
import sys
import urllib.parse
import sqlite3
import re
from html import escape
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
    return sqlite3.connect(db_path)

def get_all_resources():
    """Get all resources"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, type, content, file_url FROM resources ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    resources = []
    for row in rows:
        resources.append({
            'id': row[0],
            'title': row[1],
            'type': row[2],
            'content': row[3],
            'file_url': row[4]
        })
    
    return resources

def add_resource(data):
    """Add new resource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO resources (title, type, content, file_url) 
        VALUES (?, ?, ?, ?)
    ''', (data['title'], data['type'], data['content'], data.get('file_url', '')))
    
    resource_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return resource_id

def update_resource(resource_id, data):
    """Update existing resource"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if file_url is provided in the update data
    if 'file_url' in data:
        cursor.execute('''
            UPDATE resources SET title = ?, type = ?, content = ?, file_url = ?
            WHERE id = ?
        ''', (data['title'], data['type'], data['content'], data['file_url'], resource_id))
    else: # If file_url is not provided, update other fields but leave existing file_url
        cursor.execute('''
            UPDATE resources SET title = ?, type = ?, content = ?
            WHERE id = ?
        ''', (data['title'], data['type'], data['content'], resource_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def delete_resource(resource_id):
    """Delete resource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
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
            logger.info("Handling GET request for all resources.")
            resources = get_all_resources()
            print(json.dumps({"success": True, "data": resources}))
            
        elif method == 'POST' or method == 'PUT':
            logger.info(f"Handling {method} request for resource.")
            form_data = parse_form_data() # Consider adding logging within parse_form_data if complex

            resource_id_to_update = None
            if method == 'PUT':
                query_string = os.environ.get('QUERY_STRING', '')
                if 'id=' in query_string:
                    try:
                        resource_id_to_update = int(query_string.split('id=')[1].split('&')[0])
                        logger.info(f"Resource ID for PUT: {resource_id_to_update}")
                    except ValueError:
                        logger.error(f"Invalid Resource ID for PUT: {query_string.split('id=')[1].split('&')[0]}")
                        print(json.dumps({"success": False, "error": "Invalid Resource ID format."}))
                        return
                else:
                    logger.warning("Resource ID required for PUT but not provided.")
                    print(json.dumps({"success": False, "error": "Resource ID required for update"}))
                    return
            
            title = escape(form_data.get('title', [''])[0] if isinstance(form_data.get('title'), list) else form_data.get('title', ''))
            type_val = escape(form_data.get('type', [''])[0] if isinstance(form_data.get('type'), list) else form_data.get('type', ''))
            content = escape(form_data.get('content', [''])[0] if isinstance(form_data.get('content'), list) else form_data.get('content', ''))
            file_url = form_data.get('file_url', [''])[0] if isinstance(form_data.get('file_url'), list) else form_data.get('file_url', '')
            # Not escaping file_url as it's a URL

            data = {'title': title, 'type': type_val, 'content': content, 'file_url': file_url}
            logger.debug(f"Parsed data for {method}: {data}")

            if not data['title'] or not data['type'] or not data['content']:
                logger.warning(f"{method} attempt with missing title, type, or content.")
                print(json.dumps({"success": False, "error": "Title, type, and content are required"}))
                return

            if method == 'POST':
                resource_id = add_resource(data)
                logger.info(f"Resource added with ID: {resource_id}")
                print(json.dumps({"success": True, "id": resource_id, "message": "Resource added successfully"}))
            elif method == 'PUT':
                if resource_id_to_update is None:
                    logger.error("Critical: PUT request for resource missing ID at decision point.") # Should have been caught
                    print(json.dumps({"success": False, "error": "Resource ID required for update"}))
                    return
                updated = update_resource(resource_id_to_update, data)
                if updated:
                    logger.info(f"Resource with ID: {resource_id_to_update} updated successfully.")
                    print(json.dumps({"success": True, "id": resource_id_to_update, "message": "Resource updated successfully"}))
                else:
                    logger.warning(f"Failed to update resource with ID: {resource_id_to_update} or resource not found.")
                    print(json.dumps({"success": False, "error": "Failed to update resource or resource not found"}))
            
        elif method == 'DELETE':
            query_string = os.environ.get('QUERY_STRING', '')
            logger.info(f"Handling DELETE request for resource. Query: {query_string}")
            if 'id=' in query_string:
                try:
                    resource_id_str = query_string.split('id=')[1].split('&')[0]
                    resource_id = int(resource_id_str)
                    if delete_resource(resource_id):
                        logger.info(f"Resource with ID: {resource_id} deleted successfully.")
                        print(json.dumps({"success": True, "message": "Resource deleted successfully"}))
                    else:
                        logger.warning(f"Resource with ID: {resource_id} not found for deletion.")
                        print(json.dumps({"success": False, "error": "Resource not found"})) # More specific
                except ValueError:
                    logger.error(f"Invalid Resource ID for DELETE: {resource_id_str}")
                    print(json.dumps({"success": False, "error": "Invalid Resource ID format."}))
            else:
                logger.warning("Resource ID required for DELETE but not provided.")
                print(json.dumps({"success": False, "error": "Resource ID required"})) # More specific
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))


if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()