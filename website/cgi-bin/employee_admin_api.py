#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import bcrypt # For password hashing
import uuid # For unique filenames
from html import escape
import urllib.parse

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
UPLOAD_DIR_PROFILE_PICS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'profile_pictures')
os.makedirs(UPLOAD_DIR_PROFILE_PICS, exist_ok=True)

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def hash_password(plain_password):
    """Hash a plain password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed_bytes.hex() # Store as hex string

def save_profile_picture(file_item):
    """Save uploaded profile picture and return its web-accessible path."""
    if not file_item or not file_item.filename:
        return None

    _, ext = os.path.splitext(file_item.filename)
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise ValueError("Invalid file type for profile picture. Only JPG, PNG, GIF allowed.")

    unique_filename = str(uuid.uuid4()) + ext.lower()
    file_path = os.path.join(UPLOAD_DIR_PROFILE_PICS, unique_filename)

    with open(file_path, 'wb') as f:
        f.write(file_item.file.read())

    return f"/uploads/profile_pictures/{unique_filename}"

def get_all_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, username, designation, profile_picture_url, email, phone FROM employees ORDER BY full_name")
    employees = [{
        "id": row[0], "full_name": row[1], "username": row[2], "designation": row[3],
        "profile_picture_url": row[4], "email": row[5], "phone": row[6]
    } for row in cursor.fetchall()]
    conn.close()
    return employees

def add_employee(data, profile_pic_item):
    profile_picture_url = data.get('profile_picture_url', '')
    if profile_pic_item and profile_pic_item.filename:
        try:
            profile_picture_url = save_profile_picture(profile_pic_item)
        except ValueError as e:
            return None, str(e) # Return error message

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO employees (full_name, username, password_hash, designation, profile_picture_url, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['full_name'], data['username'], hash_password(data['password']),
            data.get('designation', ''), profile_picture_url,
            data.get('email', ''), data.get('phone', '')
        ))
        employee_id = cursor.lastrowid
        conn.commit()
        return employee_id, None
    except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations (e.g., username, email)
        conn.rollback()
        if "UNIQUE constraint failed: employees.username" in str(e):
            return None, "Username already exists."
        elif "UNIQUE constraint failed: employees.email" in str(e) and data.get('email'):
            return None, "Email already exists."
        return None, f"Database integrity error: {str(e)}"
    finally:
        conn.close()

def update_employee(employee_id, data, profile_pic_item):
    profile_picture_url = data.get('profile_picture_url') # Might be None if not provided

    # If a new file is uploaded, it takes precedence
    if profile_pic_item and profile_pic_item.filename:
        try:
            # Consider deleting old picture if one exists and is managed by this system
            profile_picture_url = save_profile_picture(profile_pic_item)
        except ValueError as e:
            return False, str(e)

    conn = get_db_connection()
    cursor = conn.cursor()

    fields_to_update = {
        "full_name": data['full_name'],
        "username": data['username'],
        "designation": data.get('designation', ''),
        "email": data.get('email', ''),
        "phone": data.get('phone', '')
    }
    if profile_picture_url is not None: # Only update if new URL or file was processed
        fields_to_update["profile_picture_url"] = profile_picture_url

    # Conditionally update password if provided
    if data.get('password'):
        fields_to_update["password_hash"] = hash_password(data['password'])

    set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
    values = list(fields_to_update.values()) + [employee_id]

    try:
        cursor.execute(f"UPDATE employees SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
        return cursor.rowcount > 0, None
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: employees.username" in str(e):
            return False, "Username already exists for another employee."
        elif "UNIQUE constraint failed: employees.email" in str(e) and data.get('email'):
            return False, "Email already exists for another employee."
        return False, f"Database integrity error: {str(e)}"
    finally:
        conn.close()

def reset_employee_password(employee_id, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE employees SET password_hash = ? WHERE id = ?", (hash_password(new_password), employee_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_employee(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Consider deleting profile picture file if it exists
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')
    form = cgi.FieldStorage()

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    try:
        if method == 'GET':
            employees = get_all_employees()
            print(json.dumps({"success": True, "data": employees}))

        elif method == 'POST':
            data = {field: form.getvalue(field) for field in form if field != 'profile_picture_file'}
            profile_pic_item = form['profile_picture_file'] if 'profile_picture_file' in form else None

            if not data.get('full_name') or not data.get('username') or not data.get('password'):
                print(json.dumps({"success": False, "error": "Full name, username, and password are required."}))
                sys.exit(0)

            employee_id, error = add_employee(data, profile_pic_item)
            if error:
                print(json.dumps({"success": False, "error": error}))
            else:
                print(json.dumps({"success": True, "id": employee_id, "message": "Employee added successfully."}))

        elif method == 'PUT':
            employee_id = form.getvalue('id')
            action = form.getvalue('action') # For query string params like ?action=reset_password

            if not employee_id and 'id=' in os.environ.get('QUERY_STRING', ''): # For ID in query string
                 query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
                 employee_id = query_params.get('id', [None])[0]
                 action = query_params.get('action', [None])[0]


            if not employee_id:
                print(json.dumps({"success": False, "error": "Employee ID is required for update."}))
                sys.exit(0)

            employee_id = int(employee_id)

            if action == 'reset_password':
                new_password = form.getvalue('password')
                if not new_password:
                    print(json.dumps({"success": False, "error": "New password is required for reset."}))
                    sys.exit(0)
                if reset_employee_password(employee_id, new_password):
                    print(json.dumps({"success": True, "message": "Password reset successfully."}))
                else:
                    print(json.dumps({"success": False, "error": "Failed to reset password."}))
            else:
                data = {field: form.getvalue(field) for field in form if field not in ['id', 'profile_picture_file']}
                profile_pic_item = form['profile_picture_file'] if 'profile_picture_file' in form else None

                if not data.get('full_name') or not data.get('username'):
                     print(json.dumps({"success": False, "error": "Full name and username are required for update."}))
                     sys.exit(0)

                success, error = update_employee(employee_id, data, profile_pic_item)
                if error:
                     print(json.dumps({"success": False, "error": error}))
                elif success:
                    print(json.dumps({"success": True, "message": "Employee updated successfully."}))
                else:
                    print(json.dumps({"success": False, "error": "Employee not found or no changes made."}))

        elif method == 'DELETE':
            employee_id_str = os.environ.get('QUERY_STRING', '').split('id=')[-1]
            if not employee_id_str:
                print(json.dumps({"success": False, "error": "Employee ID is required for delete."}))
                sys.exit(0)
            try:
                employee_id = int(employee_id_str)
                if delete_employee(employee_id):
                    print(json.dumps({"success": True, "message": "Employee deleted successfully."}))
                else:
                    print(json.dumps({"success": False, "error": "Employee not found."}))
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        # Log the actual error to server logs
        print(f"Unhandled error in employee_admin_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An unexpected server error occurred. Please check server logs."}))

if __name__ == "__main__":
    main()
