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
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

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

def update_product(product_id, data):
    """Update existing product"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure logo_url is handled correctly, even if not provided in data
    # If 'logo_url' is in data and is empty, it means the user might want to clear it.
    # If 'logo_url' is not in data, we should not change the existing one unless specific logic dictates.
    # For this implementation, we'll update it if provided, otherwise keep existing.
    # A more robust solution might involve fetching the product first to see if logo_url exists.

    if 'logo_url' in data:
        cursor.execute('''
            UPDATE products SET name = ?, description = ?, logo_url = ?
            WHERE id = ?
        ''', (data['name'], data['description'], data['logo_url'], product_id))
    else:
        # If logo_url is not part of the update data, don't change it
        cursor.execute('''
            UPDATE products SET name = ?, description = ?
            WHERE id = ?
        ''', (data['name'], data['description'], product_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

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
            logger.info("Handling GET request for all products.")
            products = get_all_products()
            print(json.dumps({"success": True, "data": products}))
            
        elif method == 'POST' or method == 'PUT':
            logger.info(f"Handling {method} request for product.")
            form_data = parse_form_data() # This function might need logging if complex
            
            product_id_to_update = None
            if method == 'PUT':
                query_string = os.environ.get('QUERY_STRING', '')
                if 'id=' in query_string:
                    try:
                        product_id_to_update = int(query_string.split('id=')[1].split('&')[0])
                        logger.info(f"Product ID for PUT: {product_id_to_update}")
                    except ValueError:
                        logger.error(f"Invalid Product ID for PUT: {query_string.split('id=')[1].split('&')[0]}")
                        print(json.dumps({"success": False, "error": "Invalid Product ID format."}))
                        return
                else:
                    logger.warning("Product ID required for PUT request but not provided.")
                    print(json.dumps({"success": False, "error": "Product ID required for update"}))
                    return
            
            name = escape(form_data.get('name', [''])[0] if isinstance(form_data.get('name'), list) else form_data.get('name', ''))
            description = escape(form_data.get('description', [''])[0] if isinstance(form_data.get('description'), list) else form_data.get('description', ''))
            logo_url = form_data.get('logo_url', [''])[0] if isinstance(form_data.get('logo_url'), list) else form_data.get('logo_url', '')
            # Not escaping logo_url as it's a URL

            data = {'name': name, 'description': description, 'logo_url': logo_url}
            logger.debug(f"Parsed data for {method}: { {k:v for k,v in data.items() if k != 'password_hash'} }")


            if not data['name'] or not data['description']:
                logger.warning(f"{method} attempt with missing name or description.")
                print(json.dumps({"success": False, "error": "Name and description are required"}))
                return

            if method == 'POST':
                product_id = add_product(data)
                logger.info(f"Product added with ID: {product_id}")
                print(json.dumps({"success": True, "id": product_id, "message": "Product added successfully"}))
            elif method == 'PUT':
                updated = update_product(product_id_to_update, data)
                if updated:
                    logger.info(f"Product with ID: {product_id_to_update} updated successfully.")
                    print(json.dumps({"success": True, "id": product_id_to_update, "message": "Product updated successfully"}))
                else:
                    logger.warning(f"Failed to update product with ID: {product_id_to_update} or product not found.")
                    print(json.dumps({"success": False, "error": "Failed to update product or product not found"}))
            
        elif method == 'DELETE':
            query_string = os.environ.get('QUERY_STRING', '')
            logger.info(f"Handling DELETE request for product. Query: {query_string}")
            if 'id=' in query_string:
                try:
                    product_id_str = query_string.split('id=')[1].split('&')[0]
                    product_id = int(product_id_str)
                    if delete_product(product_id):
                        logger.info(f"Product with ID: {product_id} deleted successfully.")
                        print(json.dumps({"success": True, "message": "Product deleted successfully"}))
                    else:
                        logger.warning(f"Product with ID: {product_id} not found for deletion.")
                        print(json.dumps({"success": False, "error": "Product not found"})) # Changed from generic error
                except ValueError:
                    logger.error(f"Invalid Product ID for DELETE: {product_id_str}")
                    print(json.dumps({"success": False, "error": "Invalid Product ID format."}))
            else:
                logger.warning("Product ID required for DELETE request but not provided.")
                print(json.dumps({"success": False, "error": "Product ID required"})) # Changed from generic error
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))


if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()