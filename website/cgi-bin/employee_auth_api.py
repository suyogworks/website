#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import bcrypt # For password hashing
from html import escape
import urllib.parse

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def verify_password(plain_password, hashed_password_hex):
    """Verify a plain password against a stored hex-encoded hashed password."""
    try:
        hashed_password = bytes.fromhex(hashed_password_hex)
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    except (ValueError, TypeError):
        return False

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    if method == 'POST':
        try:
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            post_data_raw = sys.stdin.read(content_length)
            form_data = urllib.parse.parse_qs(post_data_raw)

            username = form_data.get('username', [''])[0].strip()
            password = form_data.get('password', [''])[0].strip()

            if not username or not password:
                print(json.dumps({"success": False, "error": "Username and password are required."}))
                sys.exit(0)

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, full_name, username, password_hash, designation, profile_picture_url, email, phone FROM employees WHERE username = ?", (username,))
            employee_row = cursor.fetchone()
            conn.close()

            if employee_row:
                employee_id, full_name, emp_username, stored_password_hash, designation, profile_pic, email, phone = employee_row
                if verify_password(password, stored_password_hash):
                    employee_data = {
                        "id": employee_id,
                        "full_name": full_name,
                        "username": emp_username,
                        "designation": designation,
                        "profile_picture_url": profile_pic,
                        "email": email,
                        "phone": phone
                    }
                    print(json.dumps({"success": True, "employee": employee_data}))
                else:
                    print(json.dumps({"success": False, "error": "Invalid username or password."}))
            else:
                print(json.dumps({"success": False, "error": "Invalid username or password."}))

        except Exception as e:
            # Log the exception details to stderr for server logs (won't go to client)
            print(f"Error in employee_auth_api.py: {e}", file=sys.stderr)
            print(json.dumps({"success": False, "error": "An internal server error occurred."}))
    else:
        print(json.dumps({"success": False, "error": "Method not allowed."}))

if __name__ == "__main__":
    main()
