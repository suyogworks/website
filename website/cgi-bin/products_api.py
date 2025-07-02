#!/usr/bin/env python3
"""
Products management API
Handles CRUD operations for products
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

def get_all_products():
    """Get all products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, logo_url FROM products ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    products = []
    for row in rows:
        products.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'logo_url': row[3]
        })
    
    return products

def add_product(data):
    """Add new product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO products (name, description, logo_url) 
        VALUES (?, ?, ?)
    ''', (data['name'], data['description'], data.get('logo_url', '')))
    
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return product_id

def delete_product(product_id):
    """Delete product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
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
            # Return all products
            products = get_all_products()
            print(json.dumps({"success": True, "data": products}))
            
        elif method == 'POST':
            # Add new product
            form_data = parse_form_data()
            
            # Extract form fields, handling both list and string formats
            name = ''
            description = ''
            logo_url = ''
            
            if 'name' in form_data:
                name_val = form_data['name']
                name = escape(name_val[0] if isinstance(name_val, list) else name_val)
            
            if 'description' in form_data:
                description_val = form_data['description']
                description = escape(description_val[0] if isinstance(description_val, list) else description_val)
            
            if 'logo_url' in form_data:
                logo_url_val = form_data['logo_url']
                logo_url = logo_url_val[0] if isinstance(logo_url_val, list) else logo_url_val
            
            data = {
                'name': name,
                'description': description,
                'logo_url': logo_url
            }
            
            if not data['name'] or not data['description']:
                print(json.dumps({"success": False, "error": "Name and description are required"}))
                return
            
            product_id = add_product(data)
            print(json.dumps({"success": True, "id": product_id, "message": "Product added successfully"}))
            
        elif method == 'DELETE':
            # Delete product
            query_string = os.environ.get('QUERY_STRING', '')
            if 'id=' in query_string:
                product_id = query_string.split('id=')[1].split('&')[0]
                if delete_product(int(product_id)):
                    print(json.dumps({"success": True, "message": "Product deleted successfully"}))
                else:
                    print(json.dumps({"error": "Product not found"}))
            else:
                print(json.dumps({"error": "Product ID required"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main()