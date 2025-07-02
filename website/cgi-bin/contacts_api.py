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
        
        # Handle OPTIONS request for CORS
        if method == 'OPTIONS':
            print(json.dumps({"status": "ok"}))
            return
        
        if method == 'GET':
            # Return all contacts
            contacts = get_all_contacts()
            print(json.dumps({"success": True, "data": contacts}))
            
        elif method == 'POST':
            # Add new contact
            form_data = parse_form_data()
            
            data = {
                'name': escape(form_data.get('name', [''])[0].strip()),
                'email': form_data.get('email', [''])[0].strip(),
                'phone': form_data.get('phone', [''])[0].strip(),
                'company': escape(form_data.get('company', [''])[0].strip()),
                'subject': escape(form_data.get('subject', [''])[0].strip()),
                'message': escape(form_data.get('message', [''])[0].strip())
            }
            
            if not data['name'] or not data['email'] or not data['message']:
                print(json.dumps({"success": False, "error": "Name, email, and message are required"}))
                return
            
            contact_id = add_contact(data)
            print(json.dumps({"success": True, "id": contact_id, "message": "Contact submission added successfully"}))
        
        else:
            print(json.dumps({"error": "Method not allowed"}))
            
    except Exception as e:
        print(json.dumps({"error": "Server error", "details": str(e)}))

if __name__ == "__main__":
    main()