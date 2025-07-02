#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import uuid
from datetime import datetime

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
UPLOAD_DIR_HANDBOOK = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'company_handbook')
os.makedirs(UPLOAD_DIR_HANDBOOK, exist_ok=True)

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def get_current_handbook():
    """Retrieve current handbook details from DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Assuming only one handbook record, or the latest one if multiple were possible
    cursor.execute("SELECT id, file_name, file_path, uploaded_at FROM company_handbook ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "file_name": row[1], "file_path": row[2], "uploaded_at": row[3]}
    return None

def save_handbook_file(file_item):
    """Save uploaded handbook PDF and return its web-accessible path and original filename."""
    if not file_item or not file_item.filename:
        raise ValueError("No file provided.")

    original_filename = file_item.filename
    _, ext = os.path.splitext(original_filename)
    if ext.lower() != '.pdf':
        raise ValueError("Invalid file type. Only PDF files are allowed for the handbook.")

    # Use a fixed name or a name derived from original, but ensure uniqueness if multiple versions were stored.
    # For a single handbook system, a fixed name like 'company_handbook.pdf' is simplest.
    # unique_filename = "company_handbook" + ext.lower()
    # Or, to allow different names if admin uploads "MyCompanyHandbook_v2.pdf"
    unique_filename = str(uuid.uuid4()) + ext.lower() # Keep it unique to avoid caching issues if replaced

    file_path_on_disk = os.path.join(UPLOAD_DIR_HANDBOOK, unique_filename)

    with open(file_path_on_disk, 'wb') as f:
        f.write(file_item.file.read())

    web_accessible_path = f"/uploads/company_handbook/{unique_filename}"
    return web_accessible_path, original_filename

def add_or_replace_handbook(web_file_path, original_file_name):
    """Adds a new handbook record, deleting any old ones."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete any existing handbook records and their files first
        cursor.execute("SELECT file_path FROM company_handbook")
        old_files = cursor.fetchall()
        for old_file_row in old_files:
            old_file_disk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), old_file_row[0].lstrip('/'))
            if os.path.exists(old_file_disk_path):
                try:
                    os.remove(old_file_disk_path)
                except OSError:
                    # Log this error, but continue. Maybe file is locked or permissions issue.
                    print(f"Warning: Could not delete old handbook file: {old_file_disk_path}", file=sys.stderr)


        cursor.execute("DELETE FROM company_handbook") # Clear all old records

        # Insert the new handbook record
        cursor.execute("""
            INSERT INTO company_handbook (file_name, file_path, uploaded_at)
            VALUES (?, ?, ?)
        """, (original_file_name, web_file_path, datetime.now().isoformat()))
        handbook_id = cursor.lastrowid
        conn.commit()
        return handbook_id
    except Exception as e:
        conn.rollback()
        raise e # Re-raise to be caught by main error handler
    finally:
        conn.close()

def delete_current_handbook():
    """Deletes the handbook record and its associated file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT file_path FROM company_handbook ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row and row[0]:
            file_to_delete_web_path = row[0]
            # Convert web path to disk path
            # Assumes UPLOAD_DIR_HANDBOOK is at website_root/uploads/company_handbook
            # and web_accessible_path is /uploads/company_handbook/filename.pdf
            base_website_dir = os.path.dirname(os.path.dirname(__file__)) # .../website/
            file_to_delete_disk_path = os.path.join(base_website_dir, file_to_delete_web_path.lstrip('/'))

            if os.path.exists(file_to_delete_disk_path):
                try:
                    os.remove(file_to_delete_disk_path)
                except OSError as e:
                    # Log this error, but proceed to delete DB record
                    print(f"Warning: Could not delete handbook file {file_to_delete_disk_path}: {e}", file=sys.stderr)

        cursor.execute("DELETE FROM company_handbook") # Deletes all records, assuming only one matters
        conn.commit()
        return cursor.rowcount > 0 # True if any record was deleted
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    try:
        if method == 'GET':
            handbook = get_current_handbook()
            if handbook:
                print(json.dumps({"success": True, "data": handbook}))
            else:
                print(json.dumps({"success": True, "data": None, "message": "No handbook uploaded."}))

        elif method == 'POST':
            form = cgi.FieldStorage()
            file_item = form['handbook_file'] if 'handbook_file' in form else None

            if not file_item or not file_item.filename:
                print(json.dumps({"success": False, "error": "No handbook file provided."}))
                sys.exit(0)

            try:
                web_path, original_name = save_handbook_file(file_item)
                add_or_replace_handbook(web_path, original_name)
                print(json.dumps({"success": True, "message": "Handbook uploaded successfully.", "data": {"file_name": original_name, "file_path": web_path, "uploaded_at": datetime.now().isoformat()}}))
            except ValueError as ve: # Catch specific errors like invalid file type
                print(json.dumps({"success": False, "error": str(ve)}))
            except Exception as e:
                print(f"Error during handbook upload: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                print(json.dumps({"success": False, "error": "Failed to process handbook upload."}))


        elif method == 'DELETE':
            if delete_current_handbook():
                print(json.dumps({"success": True, "message": "Handbook deleted successfully."}))
            else:
                # This might mean no handbook was there to delete, which isn't strictly an error.
                print(json.dumps({"success": True, "message": "No handbook found to delete or already deleted."}))

        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        # Log the actual error to server logs
        print(f"Unhandled error in handbook_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An unexpected server error occurred."}))

if __name__ == "__main__":
    main()
