#!/usr/bin/env python3
import json
import sqlite3
import os
import sys
from html import escape
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_employee_tasks(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, description, due_date, status, created_at, updated_at
        FROM tasks
        WHERE assigned_to_employee_id = ?
        ORDER BY due_date ASC, created_at DESC
    """, (employee_id,))
    tasks = [{
        "id": row[0], "title": row[1], "description": row[2], "due_date": row[3],
        "status": row[4], "created_at": row[5], "updated_at": row[6]
    } for row in cursor.fetchall()]
    conn.close()
    return tasks

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, OPTIONS") # Initially only GET for employees
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    if not employee_id_str:
        query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
        employee_id_str = query_params.get('employee_id', [None])[0]


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
            tasks = get_employee_tasks(employee_id)
            print(json.dumps({"success": True, "data": tasks}))

        # POST, PUT, DELETE for tasks will be handled by an admin-specific API or an enhanced version of this one
        # For now, employees can only view their tasks.
        else:
            print(json.dumps({"success": False, "error": f"Method {method} not allowed for employees on this resource."}))

    except Exception as e:
        print(f"Error in tasks_api.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    main()
