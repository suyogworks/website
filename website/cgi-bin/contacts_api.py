#!/usr/bin/env python3
"""
Contacts management API
Handles contact form submissions
"""

import json
import os
import sys
import urllib.parse
import sqlite3
from html import escape
from datetime import datetime
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
    return sqlite3.connect(db_path)

def get_all_contacts():
    """Get all contact submissions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, phone, company, subject, message, timestamp FROM contacts ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    
    contacts = []
    for row in rows:
        contacts.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'company': row[4],
            'subject': row[5],
            'message': row[6],
            'timestamp': row[7]
        })
    
    return contacts

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
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
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
            logger.info("Handling GET request for all contacts.")
            contacts = get_all_contacts()
            print(json.dumps({"success": True, "data": contacts}))
            
        elif method == 'POST':
            logger.info("Handling POST request for new contact submission.")
            form_data = parse_form_data() # Consider logging inside if complex
            
            data = {
                'name': escape(form_data.get('name', [''])[0].strip()),
                'email': form_data.get('email', [''])[0].strip(), # Email not typically escaped if used for sending
                'phone': form_data.get('phone', [''])[0].strip(),
                'company': escape(form_data.get('company', [''])[0].strip()),
                'subject': escape(form_data.get('subject', [''])[0].strip()),
                'message': escape(form_data.get('message', [''])[0].strip())
            }
            logger.debug(f"Parsed contact form data: Name='{data['name']}', Email='{data['email']}', Subject='{data['subject']}'")

            if not data['name'] or not data['email'] or not data['message']:
                logger.warning("Contact submission attempt with missing name, email, or message.")
                print(json.dumps({"success": False, "error": "Name, email, and message are required"}))
                return
            
            # Basic email validation (already in submit_contact, good to have here too if this is the main endpoint)
            if '@' not in data['email'] or '.' not in data['email'].split('@')[-1]:
                logger.warning(f"Invalid email format in contact submission: {data['email']}")
                print(json.dumps({"success": False, "error": "Please enter a valid email address."}))
                return

            contact_id = add_contact(data)
            logger.info(f"Contact submission added successfully with ID: {contact_id}")
            print(json.dumps({"success": True, "id": contact_id, "message": "Contact submission added successfully"}))
        
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        print(json.dumps({"error": "Server error", "details": "An unexpected error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()