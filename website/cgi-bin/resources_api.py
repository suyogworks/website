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
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            print(json.dumps({"status": "ok"}))
            return

        if method == 'GET':
            resources = get_all_resources()
            print(json.dumps({"success": True, "data": resources}))
            
        elif method == 'POST' or method == 'PUT': # Added PUT
            form_data = parse_form_data()

            # For PUT, get resource_id from query string
            resource_id_to_update = None
            if method == 'PUT':
                query_string = os.environ.get('QUERY_STRING', '')
                if 'id=' in query_string:
                    resource_id_to_update = int(query_string.split('id=')[1].split('&')[0])
                else:
                    print(json.dumps({"success": False, "error": "Resource ID required for update"}))
                    return
            
            # Extract form fields, handling both list and string formats
            title = ''
            type_val = ''
            content = ''
            file_url = ''
            
            if 'title' in form_data:
                title_val = form_data['title']
                title = escape(title_val[0] if isinstance(title_val, list) else title_val)
            
            if 'type' in form_data:
                type_val = form_data['type']
                type_val = escape(type_val[0] if isinstance(type_val, list) else type_val)
            
            if 'content' in form_data:
                content_val = form_data['content']
                content = escape(content_val[0] if isinstance(content_val, list) else content_val)
            
            if 'file_url' in form_data:
                file_url_val = form_data['file_url']
                file_url = file_url_val[0] if isinstance(file_url_val, list) else file_url_val
            
            data = {
                'title': title,
                'type': type_val,
                'content': content,
                'file_url': file_url
            }
            
            if not data['title'] or not data['type'] or not data['content']:
                print(json.dumps({"success": False, "error": "Title, type, and content are required"}))
                return

            if method == 'POST':
                resource_id = add_resource(data)
                print(json.dumps({"success": True, "id": resource_id, "message": "Resource added successfully"}))
            elif method == 'PUT':
                if resource_id_to_update is None: # Should have been caught earlier, but double check
                    print(json.dumps({"success": False, "error": "Resource ID required for update"}))
                    return
                updated = update_resource(resource_id_to_update, data)
                if updated:
                    print(json.dumps({"success": True, "id": resource_id_to_update, "message": "Resource updated successfully"}))
                else:
                    print(json.dumps({"success": False, "error": "Failed to update resource or resource not found"}))
            
        elif method == 'DELETE':
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' in query_string:
                resource_id = query_string.split('id=')[1].split('&')[0]
                if delete_resource(int(resource_id)):
                    print(json.dumps({"success": True, "message": "Resource deleted successfully"}))
                else:
                    print(json.dumps({"error": "Resource not found"}))
            else:
                print(json.dumps({"error": "Resource ID required"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main()