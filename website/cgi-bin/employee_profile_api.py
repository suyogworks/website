#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
from html import escape
import urllib.parse

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

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    if not employee_id_str:
        # For PUT/POST with FormData, employee_id might be a form field instead of header/query.
        # cgi.FieldStorage needs to be initialized to check this.
        # We'll handle this inside the PUT/POST blocks.
        pass


    try:
        if method == 'GET':
            if not employee_id_str: # GET must have employee_id from header or query
                query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
                employee_id_str = query_params.get('employee_id', [None])[0]

            if not employee_id_str:
                 print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing for GET."}))
                 sys.exit(0)
            try:
                employee_id = int(employee_id_str)
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Employee ID format for GET."}))
                sys.exit(0)

            profile = get_employee_profile(employee_id)
            if profile:
                print(json.dumps({"success": True, "data": profile}))
            else:
                print(json.dumps({"success": False, "error": "Profile not found."}))

        elif method == 'PUT': # PUT is now primarily for profile picture and other form data.
            form = cgi.FieldStorage()

            # Get employee_id from X-Employee-ID header first, then fallback to form field.
            if not employee_id_str:
                employee_id_str = form.getvalue('employee_id') # Assuming JS sends employee_id in FormData for PUT

            if not employee_id_str:
                print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing for PUT."}))
                sys.exit(0)
            try:
                employee_id = int(employee_id_str)
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Employee ID format for PUT."}))
                sys.exit(0)

            data = {
                'full_name': escape(form.getvalue('full_name', '')),
                'email': escape(form.getvalue('email', '')),
                'phone': escape(form.getvalue('phone', '')),
            }
            # Profile picture URL from text input (if any)
            profile_picture_url_text = form.getvalue('profile_picture_url')


            profile_pic_file_item = form['profile_picture_file'] if 'profile_picture_file' in form else None
            new_profile_pic_web_path = None
            file_error = None

            if profile_pic_file_item and profile_pic_file_item.filename:
                # Fetch old picture URL to delete it
                current_profile = get_employee_profile(employee_id)
                old_pic_path_web = current_profile.get('profile_picture_url') if current_profile else None

                new_profile_pic_web_path, file_error = save_employee_profile_picture(profile_pic_file_item)
                if file_error:
                    print(json.dumps({"success": False, "error": file_error}))
                    sys.exit(0)

                data['profile_picture_url'] = new_profile_pic_web_path # Prioritize uploaded file

                # Delete old file if it existed and was managed by uploads
                if old_pic_path_web and old_pic_path_web.startswith('/uploads/employee_profiles/'):
                    old_pic_disk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), old_pic_path_web.lstrip('/'))
                    if os.path.exists(old_pic_disk_path):
                        try:
                            os.remove(old_pic_disk_path)
                        except OSError as e:
                            print(f"Warning: Could not delete old profile picture {old_pic_disk_path}: {e}", file=sys.stderr)
            elif profile_picture_url_text is not None: # If no file uploaded, but URL field was sent
                 data['profile_picture_url'] = escape(profile_picture_url_text)


            if not data.get('full_name') or not data.get('email'): # Basic validation
                 print(json.dumps({"success": False, "error": "Full name and email are required."}))
                 sys.exit(0)

            success, error_msg = update_employee_basic_info(employee_id, data) # This function needs to handle profile_picture_url

            if success:
                updated_profile = get_employee_profile(employee_id)
                print(json.dumps({"success": True, "message": "Profile updated successfully.", "data": updated_profile}))
            else:
                print(json.dumps({"success": False, "error": error_msg or "Failed to update profile."}))

        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        print(f"Error in employee_profile_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    main()
