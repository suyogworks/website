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

# Removed add_contact function as it's handled by contacts_api.py

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
        logger.info(f"Request received by {script_name}: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")
        
        if method == 'OPTIONS':
            logger.info("Handling OPTIONS request.")
            print(json.dumps({"status": "ok"}))
            return
        
        # Note: Contact submission logic was removed from this script. It now primarily handles resources if called.
        # This script is largely redundant with resources_api.py and contacts_api.py.
        # Logging is added for visibility if it's still being invoked.

        if method == 'GET':
            logger.info("Handling GET request (for resources, though resources_api.py is preferred).")
            resources = get_all_resources()
            print(json.dumps({"success": True, "data": resources}))
            
        elif method == 'POST':
            logger.info("Handling POST request (intended for resources, though resources_api.py is preferred).")
            form = cgi.FieldStorage()
            data = {
                'title': escape(form.getvalue('title', '').strip()),
                'type': escape(form.getvalue('type', '').strip()),
                'content': escape(form.getvalue('content', '').strip())
            }
            logger.debug(f"Data for POST: {data}")
            if not data['title'] or not data['type'] or not data['content']:
                logger.warning("Resource POST attempt with missing title, type, or content.")
                print(json.dumps({"success": False, "error": "Title, type, and content are required for resource"}))
                return
            
            valid_types = ['Blog', 'Case Study', 'Technical Aspect']
            if data['type'] not in valid_types:
                logger.warning(f"Invalid resource type: {data['type']}")
                print(json.dumps({"success": False, "error": f"Resource type must be one of: {', '.join(valid_types)}"}))
                return

            try:
                file_field = form['file'] if 'file' in form else None
                resource_id = add_resource(data, file_field)
                logger.info(f"Resource added with ID: {resource_id} via {script_name}")
                print(json.dumps({"success": True, "id": resource_id, "message": f"Resource added successfully via {script_name}"}))
            except Exception as e:
                logger.error(f"Failed to add resource via {script_name}: {e}", exc_info=True)
                print(json.dumps({"success": False, "error": f"Failed to add resource via {script_name}: {str(e)}"}))

        elif method == 'PUT':
            logger.info("Handling PUT request (for resources, though resources_api.py is preferred).")
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' not in query_string:
                logger.warning("Resource ID required for PUT but not provided.")
                print(json.dumps({"success": False, "error": "Resource ID required for update"}))
                return
            
            try:
                resource_id_str = query_string.split('id=')[1].split('&')[0]
                resource_id = int(resource_id_str)
            except ValueError:
                logger.error(f"Invalid Resource ID for PUT: {resource_id_str}")
                print(json.dumps({"success": False, "error": "Invalid Resource ID format."}))
                return

            form = cgi.FieldStorage()
            data = {
                'title': escape(form.getvalue('title', '').strip()),
                'type': escape(form.getvalue('type', '').strip()),
                'content': escape(form.getvalue('content', '').strip())
            }
            logger.debug(f"Data for PUT (ID {resource_id}): {data}")
            
            if not data['title'] or not data['type'] or not data['content']:
                logger.warning(f"Resource PUT attempt (ID {resource_id}) with missing fields.")
                print(json.dumps({"success": False, "error": "Title, type, and content are required"}))
                return
            
            valid_types = ['Blog', 'Case Study', 'Technical Aspect']
            if data['type'] not in valid_types:
                logger.warning(f"Invalid resource type for PUT (ID {resource_id}): {data['type']}")
                print(json.dumps({"success": False, "error": f"Type must be one of: {', '.join(valid_types)}"}))
                return
            
            try:
                file_field = form['file'] if 'file' in form else None
                if update_resource(resource_id, data, file_field):
                    logger.info(f"Resource ID {resource_id} updated successfully via {script_name}.")
                    print(json.dumps({"success": True, "message": "Resource updated successfully"}))
                else:
                    logger.warning(f"Resource ID {resource_id} not found for update via {script_name}.")
                    print(json.dumps({"success": False, "error": "Resource not found"})) # More specific
            except Exception as e:
                logger.error(f"Failed to update resource ID {resource_id} via {script_name}: {e}", exc_info=True)
                print(json.dumps({"success": False, "error": f"Failed to update resource: {str(e)}"}))
            
        elif method == 'DELETE':
            logger.info("Handling DELETE request (for resources, though resources_api.py is preferred).")
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' in query_string:
                try:
                    resource_id_str = query_string.split('id=')[1].split('&')[0]
                    resource_id = int(resource_id_str)
                    if delete_resource(resource_id):
                        logger.info(f"Resource ID {resource_id} deleted successfully via {script_name}.")
                        print(json.dumps({"success": True, "message": "Resource deleted successfully"}))
                    else:
                        logger.warning(f"Resource ID {resource_id} not found for deletion via {script_name}.")
                        print(json.dumps({"success": False, "error": "Resource not found"})) # More specific
                except ValueError:
                    logger.error(f"Invalid Resource ID for DELETE: {resource_id_str}")
                    print(json.dumps({"success": False, "error": "Invalid Resource ID format."}))
            else:
                logger.warning("Resource ID required for DELETE but not provided.")
                print(json.dumps({"success": False, "error": "Resource ID required"}))
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint ({script_name}).")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error in {script_name}: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()