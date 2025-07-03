#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import bcrypt # For password hashing
import uuid
from html import escape
import urllib.parse
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

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
    logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")
    form = cgi.FieldStorage() # Initialize once

    if method == 'OPTIONS':
        logger.info("Handling OPTIONS request.")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    try:
        if method == 'GET':
            logger.info("Handling GET request for all employees.")
            employees = get_all_employees()
            print(json.dumps({"success": True, "data": employees}))

        elif method == 'POST':
            logger.info("Handling POST request to add new employee.")
            data = {field: form.getvalue(field) for field in form if field != 'profile_picture_file'}
            profile_pic_item = form['profile_picture_file'] if 'profile_picture_file' in form else None
            logger.debug(f"Data for POST: { {k:v for k,v in data.items() if k != 'password'} }, ProfilePic: {'Yes' if profile_pic_item and profile_pic_item.filename else 'No'}")

            if not data.get('full_name') or not data.get('username') or not data.get('password'):
                logger.warning("Add employee attempt with missing full name, username, or password.")
                print(json.dumps({"success": False, "error": "Full name, username, and password are required."}))
                sys.exit(0)

            employee_id, error = add_employee(data, profile_pic_item)
            if error:
                logger.error(f"Error adding employee: {error}")
                print(json.dumps({"success": False, "error": error}))
            else:
                logger.info(f"Employee added successfully with ID: {employee_id}")
                print(json.dumps({"success": True, "id": employee_id, "message": "Employee added successfully."}))

        elif method == 'PUT':
            logger.info(f"Handling PUT request to update employee or reset password.")
            # For PUT, ID and action can be in query string or form data. Query string takes precedence for action.
            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            action = query_params.get('action', [form.getvalue('action')])[0]
            employee_id_str = query_params.get('id', [form.getvalue('id')])[0]

            if not employee_id_str:
                logger.warning("Employee ID is required for update/reset password but not provided.")
                print(json.dumps({"success": False, "error": "Employee ID is required for update."}))
                sys.exit(0)

            try:
                employee_id = int(employee_id_str)
            except ValueError:
                logger.error(f"Invalid Employee ID format for PUT: {employee_id_str}")
                print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
                sys.exit(0)

            logger.info(f"Action for PUT: {action}, Employee ID: {employee_id}")

            if action == 'reset_password':
                new_password = form.getvalue('password')
                logger.debug(f"Password reset attempt for employee ID: {employee_id}")
                if not new_password:
                    logger.warning(f"Password reset for employee ID {employee_id} failed: New password not provided.")
                    print(json.dumps({"success": False, "error": "New password is required for reset."}))
                    sys.exit(0)
                if reset_employee_password(employee_id, new_password):
                    logger.info(f"Password for employee ID {employee_id} reset successfully.")
                    print(json.dumps({"success": True, "message": "Password reset successfully."}))
                else:
                    logger.error(f"Failed to reset password for employee ID {employee_id}.")
                    print(json.dumps({"success": False, "error": "Failed to reset password."}))
            else: # Default PUT action is to update employee details
                data = {field: form.getvalue(field) for field in form if field not in ['id', 'action', 'profile_picture_file']}
                profile_pic_item = form['profile_picture_file'] if 'profile_picture_file' in form else None
                logger.debug(f"Data for employee update (ID {employee_id}): { {k:v for k,v in data.items() if k != 'password'} }, ProfilePic: {'Yes' if profile_pic_item and profile_pic_item.filename else 'No'}")


                if not data.get('full_name') or not data.get('username'):
                     logger.warning(f"Update attempt for employee ID {employee_id} with missing full name or username.")
                     print(json.dumps({"success": False, "error": "Full name and username are required for update."}))
                     sys.exit(0)

                success, error = update_employee(employee_id, data, profile_pic_item)
                if error:
                     logger.error(f"Error updating employee ID {employee_id}: {error}")
                     print(json.dumps({"success": False, "error": error}))
                elif success:
                    logger.info(f"Employee ID {employee_id} updated successfully.")
                    print(json.dumps({"success": True, "message": "Employee updated successfully."}))
                else: # Should ideally be caught by specific error or success
                    logger.warning(f"Update for employee ID {employee_id} resulted in no changes or employee not found.")
                    print(json.dumps({"success": False, "error": "Employee not found or no changes made."}))

        elif method == 'DELETE':
            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            employee_id_str = query_params.get('id', [None])[0]
            logger.info(f"Handling DELETE request for employee ID: {employee_id_str}")

            if not employee_id_str:
                logger.warning("Employee ID required for delete but not provided.")
                print(json.dumps({"success": False, "error": "Employee ID is required for delete."}))
                sys.exit(0)
            try:
                employee_id = int(employee_id_str)
                if delete_employee(employee_id):
                    logger.info(f"Employee ID {employee_id} deleted successfully.")
                    print(json.dumps({"success": True, "message": "Employee deleted successfully."}))
                else:
                    logger.warning(f"Employee ID {employee_id} not found for deletion.")
                    print(json.dumps({"success": False, "error": "Employee not found."}))
            except ValueError:
                logger.error(f"Invalid Employee ID format for DELETE: {employee_id_str}")
                print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        logger.error(f"Unhandled server error: {e}", exc_info=True)
        # print(f"Unhandled error in employee_admin_api.py: {e}", file=sys.stderr) # Redundant if logger writes to stderr
        # import traceback # Redundant if logger.exception or exc_info=True is used
        # traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An unexpected server error occurred. Please check server logs."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()
