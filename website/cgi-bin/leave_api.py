#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
from datetime import datetime, date as datetime_date
from html import escape
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_employee_leave_history(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, start_date, end_date, reason, status, requested_at
        FROM leave_requests
        WHERE employee_id = ?
        ORDER BY requested_at DESC
    """, (employee_id,))
    history = [{
        "id": row[0], "start_date": row[1], "end_date": row[2], "reason": row[3],
        "status": row[4], "requested_at": row[5]
    } for row in cursor.fetchall()]
    conn.close()
    return history

def add_leave_request(employee_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Basic validation for dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if end_date < start_date:
            return None, "End date cannot be before start date."
        if start_date < datetime_date.today():
             return None, "Start date cannot be in the past."


        cursor.execute("""
            INSERT INTO leave_requests (employee_id, start_date, end_date, reason, status, requested_at)
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """, (
            employee_id,
            data['start_date'],
            data['end_date'],
            data['reason'],
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid, None
    except ValueError:
        return None, "Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        conn.rollback()
        return None, f"Database error: {str(e)}"
    finally:
        conn.close()

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')

    if not employee_id_str: # Fallback for POST if ID is in form data (though header is preferred)
        if method == 'POST':
            # For POST, Content-Type might be application/x-www-form-urlencoded
            # We need to parse it to check for employee_id if not in header
            # This is a simplified approach; robust parsing would use cgi.FieldStorage earlier
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                post_body = sys.stdin.read(content_length)
                form_params = urllib.parse.parse_qs(post_body)
                employee_id_str = form_params.get('employee_id', [None])[0]


    if not employee_id_str:
        print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing."}))
        sys.exit(0)

    try:
        employee_id = int(employee_id_str)
    except ValueError:
        print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        sys.exit(0)

    try:
        if method == 'GET':
            history = get_employee_leave_history(employee_id)
            print(json.dumps({"success": True, "data": history}))

        elif method == 'POST':
            # For POST, data is expected as application/x-www-form-urlencoded
            # Re-parse if not already done (if employee_id was from header)
            # A more structured approach would parse once using cgi.FieldStorage at the start
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            post_body_for_data = sys.stdin.read(content_length) if not 'form_params' in locals() else urllib.parse.urlencode(form_params, doseq=True)

            parsed_data = urllib.parse.parse_qs(post_body_for_data)

            data = {
                'start_date': parsed_data.get('start_date', [''])[0],
                'end_date': parsed_data.get('end_date', [''])[0],
                'reason': escape(parsed_data.get('reason', [''])[0])
            }

            if not all([data['start_date'], data['end_date'], data['reason']]):
                print(json.dumps({"success": False, "error": "Start date, end date, and reason are required."}))
                sys.exit(0)

            record_id, error = add_leave_request(employee_id, data)
            if error:
                print(json.dumps({"success": False, "error": error}))
            else:
                # Fetch the newly added record to return it
                conn_temp = get_db_connection()
                new_req_cursor = conn_temp.execute("SELECT id, start_date, end_date, reason, status, requested_at FROM leave_requests WHERE id = ?", (record_id,))
                new_req_row = new_req_cursor.fetchone()
                conn_temp.close()
                new_req_data = {
                    "id": new_req_row[0], "start_date": new_req_row[1], "end_date": new_req_row[2],
                    "reason": new_req_row[3], "status": new_req_row[4], "requested_at": new_req_row[5]
                } if new_req_row else None
                print(json.dumps({"success": True, "message": "Leave request submitted.", "data": new_req_data}))

        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        print(f"Error in leave_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    main()
