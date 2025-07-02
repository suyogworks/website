#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
from html import escape
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_education_history(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, institution_name, degree, year_of_completion, details
        FROM education_history
        WHERE employee_id = ? ORDER BY year_of_completion DESC, id DESC
    """, (employee_id,))
    history = [{
        "id": row[0], "institution_name": row[1], "degree": row[2],
        "year_of_completion": row[3], "details": row[4]
    } for row in cursor.fetchall()]
    conn.close()
    return history

def add_education_record(employee_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO education_history (employee_id, institution_name, degree, year_of_completion, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            employee_id,
            data['institution_name'],
            data['degree'],
            data.get('year_of_completion'), # Can be None if not provided
            data.get('details', '')
        ))
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        conn.rollback()
        return None, f"Database error: {str(e)}"
    finally:
        conn.close()

def update_education_record(record_id, employee_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE education_history
            SET institution_name = ?, degree = ?, year_of_completion = ?, details = ?
            WHERE id = ? AND employee_id = ?
        """, (
            data['institution_name'],
            data['degree'],
            data.get('year_of_completion'),
            data.get('details', ''),
            record_id,
            employee_id
        ))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Record not found or not owned by user."
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def delete_education_record(record_id, employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM education_history WHERE id = ? AND employee_id = ?", (record_id, employee_id))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Record not found or not owned by user."
        return True, None
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    form = cgi.FieldStorage() # Initialize FieldStorage for POST/PUT

    if not employee_id_str: # Fallback for POST/PUT if ID is in form data
        if method in ['POST', 'PUT']:
             employee_id_str = form.getvalue('employee_id') # Standard way for form data

    if not employee_id_str: # Final check
        print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing."}))
        sys.exit(0)

    try:
        employee_id = int(employee_id_str)
    except ValueError:
        print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        sys.exit(0)

    try:
        if method == 'GET':
            history = get_education_history(employee_id)
            print(json.dumps({"success": True, "data": history}))

        elif method == 'POST':
            data = {
                'institution_name': escape(form.getvalue('institution_name', '')),
                'degree': escape(form.getvalue('degree', '')),
                'year_of_completion': form.getvalue('year_of_completion'),
                'details': escape(form.getvalue('details', ''))
            }
            if not data['institution_name'] or not data['degree']:
                print(json.dumps({"success": False, "error": "Institution name and degree are required."}))
                sys.exit(0)

            # Convert year to int if provided, else None
            try:
                if data['year_of_completion']:
                    data['year_of_completion'] = int(data['year_of_completion'])
                else:
                    data['year_of_completion'] = None
            except ValueError:
                 print(json.dumps({"success": False, "error": "Invalid year format."}))
                 sys.exit(0)

            record_id, error = add_education_record(employee_id, data)
            if error:
                print(json.dumps({"success": False, "error": error}))
            else:
                # Fetch the newly added record to return it with its ID
                new_record_query = get_db_connection().execute("SELECT * FROM education_history WHERE id = ?", (record_id,)).fetchone()
                new_record_data = {
                     "id": new_record_query[0], "employee_id": new_record_query[1],
                     "institution_name": new_record_query[2], "degree": new_record_query[3],
                     "year_of_completion": new_record_query[4], "details": new_record_query[5]
                } if new_record_query else None
                print(json.dumps({"success": True, "message": "Education record added.", "data": new_record_data}))


        elif method == 'PUT':
            record_id_str = form.getvalue('id')
            if not record_id_str:
                print(json.dumps({"success": False, "error": "Record ID is required for update."}))
                sys.exit(0)
            try:
                record_id = int(record_id_str)
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Record ID format."}))
                sys.exit(0)

            data = {
                'institution_name': escape(form.getvalue('institution_name', '')),
                'degree': escape(form.getvalue('degree', '')),
                'year_of_completion': form.getvalue('year_of_completion'),
                'details': escape(form.getvalue('details', ''))
            }
            if not data['institution_name'] or not data['degree']:
                print(json.dumps({"success": False, "error": "Institution name and degree are required."}))
                sys.exit(0)
            try:
                if data['year_of_completion']:
                    data['year_of_completion'] = int(data['year_of_completion'])
                else:
                    data['year_of_completion'] = None # Allow clearing the year
            except ValueError:
                 print(json.dumps({"success": False, "error": "Invalid year format."}))
                 sys.exit(0)

            success, error = update_education_record(record_id, employee_id, data)
            if error:
                 print(json.dumps({"success": False, "error": error}))
            elif success:
                 updated_record_query = get_db_connection().execute("SELECT * FROM education_history WHERE id = ?", (record_id,)).fetchone()
                 updated_record_data = {
                     "id": updated_record_query[0], "employee_id": updated_record_query[1],
                     "institution_name": updated_record_query[2], "degree": updated_record_query[3],
                     "year_of_completion": updated_record_query[4], "details": updated_record_query[5]
                 } if updated_record_query else None
                 print(json.dumps({"success": True, "message": "Education record updated.", "data": updated_record_data}))
            else:
                print(json.dumps({"success": False, "error": "Failed to update record or record not found."}))


        elif method == 'DELETE':
            query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
            record_id_str = query_params.get('id', [None])[0]
            if not record_id_str:
                print(json.dumps({"success": False, "error": "Record ID required for delete."}))
                sys.exit(0)
            try:
                record_id = int(record_id_str)
            except ValueError:
                print(json.dumps({"success": False, "error": "Invalid Record ID format."}))
                sys.exit(0)

            success, error = delete_education_record(record_id, employee_id)
            if error:
                print(json.dumps({"success": False, "error": error}))
            elif success:
                print(json.dumps({"success": True, "message": "Education record deleted."}))
            else:
                 print(json.dumps({"success": False, "error": "Failed to delete record or record not found."}))

        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        print(f"Error in education_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    main()
