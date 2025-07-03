#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
import uuid
from datetime import datetime
import urllib.parse
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

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
    logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

    if method == 'OPTIONS':
        logger.info("Handling OPTIONS request.")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    form = cgi.FieldStorage() # Initialize once for POST

    if not employee_id_str:
        if method == 'POST': # For POST, employee_id might be in form data
            employee_id_str = form.getvalue('employee_id')
        elif method == 'GET' or method == 'DELETE': # For GET/DELETE, try query param if not in header
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
            logger.info(f"Handling GET request for documents, employee_id: {employee_id}")
            documents = get_employee_documents(employee_id)
            print(json.dumps({"success": True, "data": documents}))

        elif method == 'POST':
            logger.info(f"Handling POST request to upload document for employee_id: {employee_id}")
            # 'form' is already initialized. Employee ID for POST is confirmed above.
            document_type = form.getvalue('document_type')
            file_item = form['document_file'] if 'document_file' in form else None
            logger.debug(f"Document Type: {document_type}, File: {'Yes' if file_item and file_item.filename else 'No'}")

            if not document_type or not file_item or not file_item.filename:
                logger.warning("Document upload attempt with missing type or file.")
                print(json.dumps({"success": False, "error": "Document type and file are required."}))
                sys.exit(0)

            web_path, original_name, error_save = save_employee_document(employee_id, file_item, document_type)
            if error_save:
                logger.error(f"Error saving document file for employee {employee_id}: {error_save}")
                print(json.dumps({"success": False, "error": error_save}))
                sys.exit(0)

            logger.info(f"Document file saved for employee {employee_id} at {web_path}")
            doc_db_id, error_db = add_document_record(employee_id, document_type, original_name, web_path)
            if error_db:
                logger.error(f"Error adding document record to DB for employee {employee_id}: {error_db}")
                if web_path: # Attempt to delete the saved file if DB record fails
                    disk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), web_path.lstrip('/'))
                    if os.path.exists(disk_path):
                        try:
                            os.remove(disk_path)
                            logger.info(f"Cleaned up orphaned file: {disk_path}")
                        except Exception as e_rm:
                            logger.error(f"Failed to cleanup orphaned file {disk_path}: {e_rm}")
                print(json.dumps({"success": False, "error": error_db}))
                sys.exit(0)

            logger.info(f"Document record added to DB with ID: {doc_db_id} for employee {employee_id}")
            print(json.dumps({
                "success": True, "message": "Document uploaded successfully.",
                "data": {"id": doc_db_id, "document_type": document_type, "file_name": original_name, "file_path": web_path, "uploaded_at": datetime.now().isoformat()}
            }))

        elif method == 'DELETE':
            # Employee ID for authorization is already fetched from header.
            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            doc_id_str = query_params.get('id', [None])[0]
            logger.info(f"Handling DELETE request for document ID: {doc_id_str}, employee_id: {employee_id}")


            if not doc_id_str:
                logger.warning("Document ID required for delete but not provided.")
                print(json.dumps({"success": False, "error": "Document ID required for delete."}))
                sys.exit(0)
            try:
                doc_id = int(doc_id_str)
            except ValueError:
                logger.error(f"Invalid Document ID format for DELETE: {doc_id_str}")
                print(json.dumps({"success": False, "error": "Invalid Document ID format."}))
                sys.exit(0)

            success, error_msg = delete_document_record(doc_id, employee_id)
            if success:
                logger.info(f"Document ID {doc_id} deleted successfully for employee ID {employee_id}.")
                print(json.dumps({"success": True, "message": "Document deleted successfully."}))
            else:
                logger.error(f"Failed to delete document ID {doc_id} for employee ID {employee_id}: {error_msg}")
                print(json.dumps({"success": False, "error": error_msg or "Failed to delete document."}))

        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        logger.error(f"Unhandled error in {script_name}: {e}", exc_info=True)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()
