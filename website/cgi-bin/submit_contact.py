#!/usr/bin/env python3
"""
Resources management API
Handles CRUD operations for resources (blogs, case studies, technical docs)
"""

import cgi
import json
import sqlite3
import os
import sys
from html import escape
import uuid
import mimetypes
import urllib.parse
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
    return sqlite3.connect(db_path)

def get_all_resources():
    """Get all resources"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, type, content, file_path FROM resources ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    resources = []
    for row in rows:
        resources.append({
            'id': row[0],
            'title': row[1],
            'type': row[2],
            'content': row[3],
            'file_path': row[4] if len(row) > 4 else None
        })
    
    return resources

def save_uploaded_file(file_field):
    """Save uploaded PDF file and return the file path"""
    if not file_field or not file_field.filename:
        return None
    
    # Create uploads directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    website_dir = os.path.dirname(script_dir)
    upload_dir = os.path.join(website_dir, 'uploads', 'resources')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file_field.filename)[1].lower()
    if file_ext not in ['.pdf', '.doc', '.docx', '.txt']:
        raise ValueError("Only PDF, DOC, DOCX, and TXT files are allowed")
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_field.file.read())
    
    # Return relative path for web access
    return f"/uploads/resources/{unique_filename}"

def add_resource(data, file_field=None):
    """Add new resource"""
    file_path = ''
    if file_field:
        file_path = save_uploaded_file(file_field)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO resources (title, type, content, file_path) 
        VALUES (?, ?, ?, ?)
    ''', (data['title'], data['type'], data['content'], file_path))
    
    resource_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return resource_id

def update_resource(resource_id, data, file_field=None):
    """Update existing resource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if resource exists
    cursor.execute('SELECT file_path FROM resources WHERE id = ?', (resource_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    
    old_file_path = result[0]
    new_file_path = old_file_path  # Keep existing file by default
    
    # Handle new file upload
    if file_field:
        try:
            new_file_path = save_uploaded_file(file_field)
            # Delete old file if it exists and is a local file
            if old_file_path and old_file_path.startswith('/uploads/'):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                website_dir = os.path.dirname(script_dir)
                old_file_full_path = os.path.join(website_dir, old_file_path.lstrip('/'))
                if os.path.exists(old_file_full_path):
                    os.remove(old_file_full_path)
        except Exception as e:
            conn.close()
            raise e
    
    cursor.execute('''
        UPDATE resources 
        SET title = ?, type = ?, content = ?, file_path = ?
        WHERE id = ?
    ''', (data['title'], data['type'], data['content'], new_file_path, resource_id))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0

def delete_resource(resource_id):
    """Delete resource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get file_path before deleting
    cursor.execute('SELECT file_path FROM resources WHERE id = ?', (resource_id,))
    result = cursor.fetchone()
    
    cursor.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
    affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    # Delete file if it exists and is a local file
    if result and result[0] and result[0].startswith('/uploads/'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        website_dir = os.path.dirname(script_dir)
        file_path = os.path.join(website_dir, result[0].lstrip('/'))
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return affected > 0

def add_contact(data):
    """Add new contact submission"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO contacts (name, email, phone, company, subject, message, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], 
        data['email'], 
        data.get('phone', ''), 
        data.get('company', ''), 
        data.get('subject', ''), 
        data['message'],
        datetime.now().isoformat()
    ))
    
    contact_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return contact_id

def parse_form_data():
    """Parse form data from POST request"""
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    if content_length > 0:
        post_data = sys.stdin.read(content_length)
        return urllib.parse.parse_qs(post_data)
    return {}

def main():
    """Main handler function"""
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()
    
    try:
        method = os.environ.get('REQUEST_METHOD', 'GET')
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'GET':
            # Return all resources
            resources = get_all_resources()
            print(json.dumps({"success": True, "data": resources}))
            
        elif method == 'POST':
            # Process contact form submission
            form_data = parse_form_data()
            
            data = {
                'name': escape(form_data.get('name', [''])[0].strip()),
                'email': form_data.get('email', [''])[0].strip(),
                'phone': form_data.get('phone', [''])[0].strip(),
                'company': escape(form_data.get('company', [''])[0].strip()),
                'subject': escape(form_data.get('subject', [''])[0].strip()),
                'message': escape(form_data.get('message', [''])[0].strip())
            }
            
            # Validate required fields
            if not data['name'] or not data['email'] or not data['message']:
                print(json.dumps({"success": False, "error": "Name, email, and message are required"}))
                return
            
            # Basic email validation
            if '@' not in data['email'] or '.' not in data['email']:
                print(json.dumps({"success": False, "error": "Please enter a valid email address"}))
                return
            
            try:
                contact_id = add_contact(data)
                print(json.dumps({
                    "success": True, 
                    "message": "Thank you for your message! We will get back to you soon.",
                    "id": contact_id
                }))
            except Exception as e:
                print(json.dumps({"success": False, "error": "Failed to save your message. Please try again."}))
        
        elif method == 'PUT':
            # Update existing resource
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' not in query_string:
                print(json.dumps({"error": "Resource ID required for update"}))
                return
            
            resource_id = query_string.split('id=')[1].split('&')[0]
            form = cgi.FieldStorage()
            
            data = {
                'title': escape(form.getvalue('title', '').strip()),
                'type': escape(form.getvalue('type', '').strip()),
                'content': escape(form.getvalue('content', '').strip())
            }
            
            if not data['title'] or not data['type'] or not data['content']:
                print(json.dumps({"error": "Title, type, and content are required"}))
                return
            
            # Validate type
            valid_types = ['Blog', 'Case Study', 'Technical Aspect']
            if data['type'] not in valid_types:
                print(json.dumps({"error": f"Type must be one of: {', '.join(valid_types)}"}))
                return
            
            try:
                # Handle file upload for update
                file_field = form['file'] if 'file' in form else None
                if update_resource(int(resource_id), data, file_field):
                    print(json.dumps({"success": True, "message": "Resource updated successfully"}))
                else:
                    print(json.dumps({"error": "Resource not found"}))
            except Exception as e:
                print(json.dumps({"error": f"Failed to update resource: {str(e)}"}))
                return
            
        elif method == 'DELETE':
            # Delete resource
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