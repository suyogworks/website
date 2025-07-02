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
    print("Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    
    try:
        method = os.environ.get('REQUEST_METHOD', 'GET')
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'GET':
            # Return all team members
            team = get_all_team_members()
            print(json.dumps({"success": True, "data": team}))
            
        elif method == 'POST':
            # Add new team member
            form_data = parse_form_data()
            
            # Extract form fields, handling both list and string formats
            name = ''
            title = ''
            bio = ''
            photo_url = ''
            
            if 'name' in form_data:
                name_val = form_data['name']
                name = escape(name_val[0] if isinstance(name_val, list) else name_val)
            
            if 'title' in form_data:
                title_val = form_data['title']
                title = escape(title_val[0] if isinstance(title_val, list) else title_val)
            
            if 'bio' in form_data:
                bio_val = form_data['bio']
                bio = escape(bio_val[0] if isinstance(bio_val, list) else bio_val)
            
            if 'photo_url' in form_data:
                photo_url_val = form_data['photo_url']
                photo_url = photo_url_val[0] if isinstance(photo_url_val, list) else photo_url_val
            
            data = {
                'name': name,
                'title': title,
                'bio': bio,
                'photo_url': photo_url
            }
            
            if not data['name'] or not data['title']:
                print(json.dumps({"success": False, "error": "Name and title are required"}))
                return
            
            member_id = add_team_member(data)
            print(json.dumps({"success": True, "id": member_id, "message": "Team member added successfully"}))
            
        elif method == 'DELETE':
            # Delete team member
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' in query_string:
                member_id = query_string.split('id=')[1].split('&')[0]
                if delete_team_member(int(member_id)):
                    print(json.dumps({"success": True, "message": "Team member deleted successfully"}))
                else:
                    print(json.dumps({"error": "Team member not found"}))
            else:
                print(json.dumps({"error": "Member ID required"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main()