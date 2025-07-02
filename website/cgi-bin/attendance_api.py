#!/usr/bin/env python3
import cgi
import json
import sqlite3
import os
import sys
from datetime import datetime, date as datetime_date
import urllib.parse
from logger_config import get_logger # Import the logger

# Initialize logger
script_name = os.path.basename(__file__)
logger = get_logger(script_name)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'matrica.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_today_attendance(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime_date.today().isoformat()
    cursor.execute("""
        SELECT id, punch_in_time, punch_out_time
        FROM attendance
        WHERE employee_id = ? AND date = ?
    """, (employee_id, today_str))
    record = cursor.fetchone()
    conn.close()
    if record:
        return {"id": record[0], "punch_in_time": record[1], "punch_out_time": record[2], "date": today_str}
    return None

def punch_in(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime_date.today().isoformat()
    now_iso = datetime.now().isoformat()

    try:
        # Check if already punched in today
        cursor.execute("SELECT id FROM attendance WHERE employee_id = ? AND date = ?", (employee_id, today_str))
        if cursor.fetchone():
            return False, "Already punched in today."

        cursor.execute("""
            INSERT INTO attendance (employee_id, date, punch_in_time)
            VALUES (?, ?, ?)
        """, (employee_id, today_str, now_iso))
        conn.commit()
        return True, {"punch_in_time": now_iso, "date": today_str}
    except sqlite3.IntegrityError: # Should be caught by the SELECT, but as a fallback
        conn.rollback()
        return False, "Already punched in today (Integrity Error)."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def punch_out(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime_date.today().isoformat()
    now_iso = datetime.now().isoformat()

    try:
        # Check if punched in today and not yet punched out
        cursor.execute("""
            SELECT id, punch_in_time FROM attendance
            WHERE employee_id = ? AND date = ? AND punch_out_time IS NULL
        """, (employee_id, today_str))
        record = cursor.fetchone()

        if not record:
            return False, "Not punched in today or already punched out."

        attendance_id = record[0]
        punch_in_time = record[1]

        cursor.execute("""
            UPDATE attendance SET punch_out_time = ?
            WHERE id = ?
        """, (now_iso, attendance_id))
        conn.commit()
        return True, {"punch_in_time": punch_in_time, "punch_out_time": now_iso, "date": today_str}
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def main():
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type, X-Employee-ID")
    print()

    method = os.environ.get('REQUEST_METHOD', 'GET')
    logger.info(f"Request received: Method={method}, Path={os.environ.get('PATH_INFO', '')}, Query={os.environ.get('QUERY_STRING', '')}")

    if method == 'OPTIONS':
        logger.info("Handling OPTIONS request.")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    employee_id_str = os.environ.get('HTTP_X_EMPLOYEE_ID')
    query_params = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', ''))
    action = query_params.get('action', [None])[0]

    if not employee_id_str:
        logger.warning("Authentication required: Employee ID missing from header.")
        print(json.dumps({"success": False, "error": "Authentication required: Employee ID missing."}))
        sys.exit(0)

    try:
        employee_id = int(employee_id_str)
    except ValueError:
        logger.error(f"Invalid Employee ID format: {employee_id_str}")
        print(json.dumps({"success": False, "error": "Invalid Employee ID format."}))
        sys.exit(0)

    logger.debug(f"Processing attendance request for employee_id: {employee_id}, action: {action}")

    try:
        if method == 'GET':
            logger.info(f"Fetching today's attendance for employee_id: {employee_id}")
            attendance_status = get_today_attendance(employee_id)
            print(json.dumps({"success": True, "data": attendance_status}))

        elif method == 'POST':
            if action == 'punch_in':
                logger.info(f"Processing punch_in for employee_id: {employee_id}")
                success, result_data = punch_in(employee_id)
                if success:
                    logger.info(f"Punch_in successful for employee_id: {employee_id}, data: {result_data}")
                    print(json.dumps({"success": True, "message": "Punched in successfully.", "data": result_data}))
                else:
                    logger.warning(f"Punch_in failed for employee_id: {employee_id}, reason: {result_data}")
                    print(json.dumps({"success": False, "error": result_data}))
            elif action == 'punch_out':
                logger.info(f"Processing punch_out for employee_id: {employee_id}")
                success, result_data = punch_out(employee_id)
                if success:
                    logger.info(f"Punch_out successful for employee_id: {employee_id}, data: {result_data}")
                    print(json.dumps({"success": True, "message": "Punched out successfully.", "data": result_data}))
                else:
                    logger.warning(f"Punch_out failed for employee_id: {employee_id}, reason: {result_data}")
                    print(json.dumps({"success": False, "error": result_data}))
            else:
                logger.warning(f"Invalid action '{action}' for POST request.")
                print(json.dumps({"success": False, "error": "Invalid action for POST request."}))

        else:
            logger.warning(f"Method {method} not allowed for this endpoint.")
            print(json.dumps({"success": False, "error": f"Method {method} not allowed."}))

    except Exception as e:
        logger.error(f"Unhandled error in {script_name}: {e}", exc_info=True)
        print(json.dumps({"success": False, "error": "An internal server error occurred."}))

if __name__ == "__main__":
    logger.info(f"{script_name} script started (likely direct execution or misconfiguration).")
    main()
