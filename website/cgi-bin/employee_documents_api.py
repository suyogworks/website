#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import uuid
from datetime import datetime
import urllib.parse

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')
UPLOAD_DIR_EMPLOYEE_DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'employee_documents')
os.makedirs(UPLOAD_DIR_EMPLOYEE_DOCS, exist_ok=True)

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def save_employee_document(employee_id, file_item, document_type):
    if not file_item or not file_item.filename:
        return None, "No file provided or filename missing."

    original_filename = file_item.filename
    _, ext = os.path.splitext(original_filename)
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    if ext.lower() not in allowed_extensions:
        return None, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"

    # Sanitize document_type and original_filename for path construction (though uuid is main part)
    sane_doc_type = "".join(c if c.isalnum() else "_" for c in document_type)
    unique_filename_base = str(uuid.uuid4())

    # Create a subdirectory for each employee if it doesn't exist
    employee_specific_dir = os.path.join(UPLOAD_DIR_EMPLOYEE_DOCS, str(employee_id))
    os.makedirs(employee_specific_dir, exist_ok=True)

    unique_filename = f"{sane_doc_type}_{unique_filename_base}{ext.lower()}"
    file_path_on_disk = os.path.join(employee_specific_dir, unique_filename)

    try:
        with open(file_path_on_disk, 'wb') as f:
            f.write(file_item.file.read())
        web_accessible_path = f"/uploads/employee_documents/{employee_id}/{unique_filename}"
        return web_accessible_path, original_filename, None
    except Exception as e:
        return None, None, f"Error saving file: {str(e)}"

def add_document_record(employee_id, document_type, file_name, file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO employee_documents (employee_id, document_type, file_name, file_path, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, document_type, file_name, file_path, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        conn.rollback()
        return None, f"Database error: {str(e)}"
    finally:
        conn.close()

def get_employee_documents(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, document_type, file_name, file_path, uploaded_at
        FROM employee_documents WHERE employee_id = ? ORDER BY uploaded_at DESC
    """, (employee_id,))
    documents = [{
        "id": row[0], "document_type": row[1], "file_name": row[2],
        "file_path": row[3], "uploaded_at": row[4]
    } for row in cursor.fetchall()]
    conn.close()
    return documents

def delete_document_record(doc_id, employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First, get the file path to delete the actual file
        cursor.execute("SELECT file_path FROM employee_documents WHERE id = ? AND employee_id = ?", (doc_id, employee_id))
        row = cursor.fetchone()
        if not row:
            return False, "Document not found or access denied."

        file_path_web = row[0]

        # Delete DB record
        cursor.execute("DELETE FROM employee_documents WHERE id = ? AND employee_id = ?", (doc_id, employee_id))
        if cursor.rowcount == 0:
            conn.rollback() # Should not happen if select found it, but as a safeguard
            return False, "Document not found or failed to delete DB record."

        conn.commit()

        # Delete the actual file from disk
        if file_path_web:
            base_website_dir = os.path.dirname(os.path.dirname(__file__))
            file_path_disk = os.path.join(base_website_dir, file_path_web.lstrip('/'))
            if os.path.exists(file_path_disk):
                try:
                    os.remove(file_path_disk)
                except OSError as e:
                    # Log this, but DB record is already deleted.
                    print(f"Warning: Could not delete document file {file_path_disk}: {e}", file=sys.stderr)
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Error deleting document: {str(e)}"
    finally:
        conn.close()

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    # For POST (file upload), employee_id might come from form data if not in header
    # For DELETE, it might be in query string for doc_id, but employee_id should still be from header for auth.

    if not employee_id_str and method != 'POST': # POST will check for employee_id from form if not in header
         query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
         employee_id_str = query_params.get('employee_id', [None])[0]


    if not employee_id_str and method != 'POST': # Re-check after attempting query param
        print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing."}))
        sys.exit(0)

    employee_id = None
    if employee_id_str:
        try:
            employee_id = int(employee_id_str)
        except ValueError:
            print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
            sys.exit(0)

    try:
        if method == 'GET':
            if not employee_id:
                 print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing for GET."}))
                 sys.exit(0)
            documents = get_employee_documents(employee_id)
            print(json.dumps({"success": True, "data": documents}))

        elif method == 'POST':
            form = cgi.FieldStorage()

            # If employee_id wasn't in header, try to get it from form data
            if not employee_id:
                employee_id_form_str = form.getvalue('employee_id')
                if not employee_id_form_str:
                    print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing in POST."}))
                    sys.exit(0)
                try:
                    employee_id = int(employee_id_form_str)
                except ValueError:
                    print(json.dumps({"success": False, "error": "Invalid Employee ID format in POST form."}))
                    sys.exit(0)

            document_type = form.getvalue('document_type')
            file_item = form['document_file'] if 'document_file' in form else None

            if not document_type or not file_item or not file_item.filename:
                print(json.dumps({"success": False, "error": "Document type and file are required."}))
                sys.exit(0)

            web_path, original_name, error_save = save_employee_document(employee_id, file_item, document_type)
            if error_save:
                print(json.dumps({"success": False, "error": error_save}))
                sys.exit(0)

            doc_db_id, error_db = add_document_record(employee_id, document_type, original_name, web_path)
            if error_db:
                # Attempt to delete the saved file if DB record fails
                if web_path:
                    disk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), web_path.lstrip('/'))
                    if os.path.exists(disk_path): os.remove(disk_path)
                print(json.dumps({"success": False, "error": error_db}))
                sys.exit(0)

            print(json.dumps({
                "success": True,
                "message": "Document uploaded successfully.",
                "data": {"id": doc_db_id, "document_type": document_type, "file_name": original_name, "file_path": web_path, "uploaded_at": datetime.now().isoformat()}
            }))

        elif method == 'DELETE':
            if not employee_id: # Must have employee_id from header for DELETE authorization
                 print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing for DELETE."}))
                 sys.exit(0)

            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            doc_id_str = query_params.get('id', [None])[0] # Document ID to delete

            if not doc_id_str:
                print(json.dumps({"success": False, "error": "Document ID required for delete."}))
                sys.exit(0)
            try:
                doc_id = int(doc_id_str)
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Document ID format."}))
                sys.exit(0)

            success, error_msg = delete_document_record(doc_id, employee_id)
            if success:
                print(json.dumps({"success": True, "message": "Document deleted successfully."}))
            else:
                print(json.dumps({"success": False, "error": error_msg or "Failed to delete document."}))

        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        print(f"Error in employee_documents_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    main()
