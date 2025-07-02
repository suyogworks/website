#!/usr/bin/env python3
"""
Careers management API
Handles CRUD operations for job listings
"""

import json
import os
import sys
import urllib.parse
import sqlite3
from html import escape
import re

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
    return sqlite3.connect(db_path)

def get_all_careers():
    """Get all career opportunities"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, experience_required, location FROM careers ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    careers = []
    for row in rows:
        careers.append({
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'experience_required': row[3],
            'location': row[4]
        })
    
    return careers

def add_career(data):
    """Add new career opportunity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO careers (title, description, experience_required, location) 
        VALUES (?, ?, ?, ?)
    ''', (data['title'], data['description'], data['experience_required'], data['location']))
    
    career_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return career_id

def delete_career(career_id):
    """Delete career opportunity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM careers WHERE id = ?', (career_id,))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return affected > 0

def update_career(career_id, data):
    """Update existing career opportunity"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE careers
        SET title = ?, description = ?, experience_required = ?, location = ?
        WHERE id = ?
    ''', (data['title'], data['description'], data['experience_required'], data['location'], career_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0

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
            careers = get_all_careers()
            print(json.dumps({"success": True, "data": careers}))
            
        elif method == 'POST' or method == 'PUT': # Added PUT
            form_data = parse_form_data()

            career_id_to_update = None
            if method == 'PUT':
                query_string = os.environ.get('QUERY_STRING', '')
                if 'id=' in query_string:
                    try:
                        career_id_to_update = int(query_string.split('id=')[1].split('&')[0])
                    except ValueError:
                        print(json.dumps({"success": False, "error": "Invalid Career ID format for update"}))
                        return
                else:
                    print(json.dumps({"success": False, "error": "Career ID required for update"}))
                    return
            
            # Extract form fields, handling both list and string formats
            title = ''
            description = ''
            experience_required = 0
            location = ''
            
            if 'title' in form_data:
                title_val = form_data['title']
                title = escape(title_val[0] if isinstance(title_val, list) else title_val)
            
            if 'description' in form_data:
                description_val = form_data['description']
                description = escape(description_val[0] if isinstance(description_val, list) else description_val)
            
            if 'experience_required' in form_data:
                experience_val = form_data['experience_required']
                try:
                    experience_required = int(experience_val[0] if isinstance(experience_val, list) else experience_val)
                except (ValueError, TypeError):
                    experience_required = 0
            
            if 'location' in form_data:
                location_val = form_data['location']
                location = escape(location_val[0] if isinstance(location_val, list) else location_val)
            
            data = {
                'title': title,
                'description': description,
                'experience_required': experience_required,
                'location': location
            }
            
            if not data['title'] or not data['description'] or not data['location']:
                print(json.dumps({"success": False, "error": "Title, description, and location are required"}))
                return

            if method == 'POST':
                career_id = add_career(data)
                print(json.dumps({"success": True, "id": career_id, "message": "Career opportunity added successfully"}))
            elif method == 'PUT':
                if career_id_to_update is None: # Should be caught earlier
                    print(json.dumps({"success": False, "error": "Career ID required for update"}))
                    return
                updated = update_career(career_id_to_update, data)
                if updated:
                    print(json.dumps({"success": True, "id": career_id_to_update, "message": "Career opportunity updated successfully"}))
                else:
                    print(json.dumps({"success": False, "error": "Failed to update career opportunity or not found"}))
            
        elif method == 'DELETE':
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' in query_string:
                try:
                    career_id = int(query_string.split('id=')[1].split('&')[0])
                    if delete_career(career_id):
                        print(json.dumps({"success": True, "message": "Career opportunity deleted successfully"}))
                    else:
                        print(json.dumps({"success": False, "error": "Career opportunity not found"}))
                except ValueError:
                    print(json.dumps({"success": False, "error": "Invalid Career ID format for delete"}))
            else:
                print(json.dumps({"success": False, "error": "Career ID required for delete"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main()