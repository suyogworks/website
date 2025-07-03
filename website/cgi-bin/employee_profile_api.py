#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
from html import escape
import urllib.parse
from logger_config import get_logger # Import the logger
import uuid # For unique filenames, if needed for profile pic path generation

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

# A simple mock for session management - in a real app, use secure session handling
# For now, we'll assume employee_id might be passed or somehow available.
# This part needs to be integrated with the actual employee login/session mechanism.
# For CGI, this is tricky without a proper framework.
# Let's assume for now the JS will send an employee_id if it has one,
# or this API is called in a context where employee_id is known (e.g. future token auth).
# For this step, we'll make it require an 'employee_id' parameter for GET/PUT for simplicity.
# This is NOT secure for a real application without proper session validation.

UPLOAD_DIR_EMPLOYEE_PROFILE_PICS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'employee_profiles')
os.makedirs(UPLOAD_DIR_EMPLOYEE_PROFILE_PICS, exist_ok=True)


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def save_employee_profile_picture(file_item):
    """Save uploaded profile picture and return its web-accessible path."""
    if not file_item or not file_item.filename:
        return None, "No file provided or filename missing."

    _, ext = os.path.splitext(file_item.filename)
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif']:
        return None, "Invalid file type. Only JPG, PNG, GIF allowed."

    unique_filename = str(uuid.uuid4()) + ext.lower()
    file_path_on_disk = os.path.join(UPLOAD_DIR_EMPLOYEE_PROFILE_PICS, unique_filename)

    try:
        with open(file_path_on_disk, 'wb') as f:
            f.write(file_item.file.read())
        web_accessible_path = f"/uploads/employee_profiles/{unique_filename}"
        return web_accessible_path, None
    except Exception as e:
        return None, f"Error saving file: {str(e)}"

def get_employee_profile(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, username, designation, profile_picture_url, email, phone
        FROM employees WHERE id = ?
    """, (employee_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "full_name": row[1], "username": row[2],
            "designation": row[3], "profile_picture_url": row[4],
            "email": row[5], "phone": row[6]
        }
    return None

def update_employee_basic_info(employee_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    fields_to_update = {
        'full_name': data.get('full_name', ''),
        'email': data.get('email', ''),
        'phone': data.get('phone', '')
    }
    # Conditionally add profile_picture_url to update if it's in data
    # This means either a new file was uploaded and its path is here,
    # or a text URL was provided and no file was uploaded.
    if 'profile_picture_url' in data:
        fields_to_update['profile_picture_url'] = data['profile_picture_url']

    set_parts = [f"{key} = ?" for key in fields_to_update.keys()]
    values = list(fields_to_update.values()) + [employee_id]

    sql = f"UPDATE employees SET {', '.join(set_parts)} WHERE id = ?"

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0, None
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: employees.email" in str(e) and data.get('email'):
            return False, "Email already exists for another user."
        return False, "Database integrity error."
    except Exception as e:
        conn.rollback()
        return False, f"An error occurred: {str(e)}"
    finally:
        conn.close()

def update_employee_profile_picture(employee_id, new_picture_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE employees SET profile_picture_url = ? WHERE id = ?", (new_picture_url, employee_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, PUT, POST, OPTIONS") # Added POST for potential separate pic upload
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')
    logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

    if method == 'OPTIONS':
        logger.info("Handling OPTIONS request.")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    form = cgi.FieldStorage() # Initialize for PUT if needed

    if not employee_id_str:
        if method in ['PUT', 'POST']: # Check form data for employee_id if not in header
            employee_id_str = form.getvalue('employee_id')
        elif method == 'GET': # For GET, try query param if not in header
            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            employee_id_str = query_params.get('employee_id', [None])[0]

    if not employee_id_str:
        logger.warning("Authentication required: Employee ID missing.")
        print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing."}))
        sys.exit(0)

    try:
        employee_id = int(employee_id_str)
    except ValueError:
        logger.error(f"Invalid Employee ID format: {employee_id_str}")
        print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        sys.exit(0)

    logger.debug(f"Processing request for employee_id: {employee_id}")

    try:
        if method == 'GET':
            logger.info(f"Handling GET request for employee profile ID: {employee_id}")
            profile = get_employee_profile(employee_id)
            if profile:
                print(json.dumps({"success": True, "data": profile}))
            else:
                logger.warning(f"Profile not found for employee ID: {employee_id}")
                print(json.dumps({"success": False, "error": "Profile not found."}))

        elif method == 'PUT':
            logger.info(f"Handling PUT request for employee profile ID: {employee_id}")
            # cgi.FieldStorage 'form' is already initialized

            data = {
                'full_name': escape(form.getvalue('full_name', '')),
                'email': escape(form.getvalue('email', '')), # Email is validated by client, escaping is fine
                'phone': escape(form.getvalue('phone', '')),
            }
            # Text input for profile_picture_url is not part of employee self-edit form
            # It's handled if admin sends it. For employee, only file upload.

            profile_pic_file_item = form['profile_picture_file'] if 'profile_picture_file' in form else None
            file_error = None

            if profile_pic_file_item and profile_pic_file_item.filename:
                logger.info(f"Processing profile picture upload for employee ID: {employee_id}")
                current_profile = get_employee_profile(employee_id)
                old_pic_path_web = current_profile.get('profile_picture_url') if current_profile else None

                new_profile_pic_web_path, file_error = save_employee_profile_picture(profile_pic_file_item)
                if file_error:
                    logger.error(f"File upload error for employee ID {employee_id}: {file_error}")
                    print(json.dumps({"success": False, "error": file_error}))
                    sys.exit(0)

                data['profile_picture_url'] = new_profile_pic_web_path
                logger.info(f"New profile picture URL for employee ID {employee_id}: {new_profile_pic_web_path}")

                if old_pic_path_web and old_pic_path_web.startswith('/uploads/employee_profiles/'):
                    old_pic_disk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), old_pic_path_web.lstrip('/'))
                    if os.path.exists(old_pic_disk_path):
                        try:
                            os.remove(old_pic_disk_path)
                            logger.info(f"Old profile picture deleted: {old_pic_disk_path}")
                        except OSError as e:
                            logger.warning(f"Could not delete old profile picture {old_pic_disk_path}: {e}")
            # If no new file, data['profile_picture_url'] will not be set here,
            # so update_employee_basic_info will preserve existing if 'profile_picture_url' not in data.
            # This is correct as employee form doesn't send text URL.

            logger.debug(f"Data for profile update (ID {employee_id}): {data}")
            if not data.get('full_name') or not data.get('email'):
                 logger.warning(f"Update attempt for employee ID {employee_id} with missing full name or email.")
                 print(json.dumps({"success": False, "error": "Full name and email are required."}))
                 sys.exit(0)

            success, error_msg = update_employee_basic_info(employee_id, data)

            if success:
                updated_profile = get_employee_profile(employee_id) # Fetch fresh data
                logger.info(f"Profile for employee ID {employee_id} updated successfully.")
                print(json.dumps({"success": True, "message": "Profile updated successfully.", "data": updated_profile}))
            else:
                logger.error(f"Failed to update profile for employee ID {employee_id}: {error_msg}")
                print(json.dumps({"success": False, "error": error_msg or "Failed to update profile."}))
        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        logger.error(f"Unhandled error in employee_profile_api.py: {e}", exc_info=True)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()
