#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import bcrypt
from html import escape
import urllib.parse
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

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
    logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

    if method == 'OPTIONS':
        logger.info("Handling OPTIONS request.")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    if method == 'POST':
        logger.info("Processing POST request for employee login.")
        try:
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            post_data_raw = sys.stdin.read(content_length)
            form_data = urllib.parse.parse_qs(post_data_raw)

            username = form_data.get('username', [''])[0].strip()
            # Password is not logged for security
            password = form_data.get('password', [''])[0].strip()
            logger.debug(f"Attempting login for username: {username}")


            if not username or not password:
                logger.warning("Employee login attempt with missing username or password.")
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
                    logger.info(f"Employee '{username}' (ID: {employee_id}) authenticated successfully.")
                    employee_data = {
                        "id": employee_id, "full_name": full_name, "username": emp_username,
                        "designation": designation, "profile_picture_url": profile_pic,
                        "email": email, "phone": phone
                    }
                    print(json.dumps({"success": True, "employee": employee_data}))
                else:
                    logger.warning(f"Invalid password for employee '{username}'.")
                    print(json.dumps({"success": False, "error": "Invalid username or password."}))
            else:
                logger.warning(f"Employee username '{username}' not found.")
                print(json.dumps({"success": False, "error": "Invalid username or password."}))

        except Exception as e:
            logger.error(f"Error during employee login processing: {e}", exc_info=True)
            print(json.dumps({"success": False, "error": "An internal server error occurred."}))
    else:
        logger.warning(f"Method {method} not allowed for this endpoint.")
        print(json.dumps({"success": False, "error": "Method not allowed."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()
