#!/usr/bin/env python3
"""
Database initialization script for Matrica Networks website
Creates SQLite database with required tables
"""

import sqlite3
import os

def init_database():
    """Initialize the SQLite database with required tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'matrica.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            company TEXT,
            subject TEXT,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create team table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            bio TEXT,
            photo_url TEXT
        )
    ''')
    
    # Create careers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            experience_required INTEGER DEFAULT 0,
            location TEXT NOT NULL
        )
    ''')
    
    # Create resources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            file_path TEXT
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            logo_url TEXT
        )
    ''')

    # Create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            designation TEXT,
            profile_picture_url TEXT,
            email TEXT UNIQUE,
            phone TEXT
            -- is_admin BOOLEAN DEFAULT FALSE -- Decided against for now, current admin is separate
        )
    ''')

    # Create company_handbook table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_handbook (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- Assuming only one handbook, but PK is good practice
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE, -- Path to the uploaded PDF
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Placeholder for future tables related to Employee Management System

    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assigned_to_employee_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            status TEXT NOT NULL DEFAULT 'Pending', -- Pending, In Progress, Completed
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to_employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')

    # Create leave_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Approved, Rejected
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')

    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            punch_in_time DATETIME,
            punch_out_time DATETIME,
            date DATE NOT NULL, -- To ensure one record per day per employee
            UNIQUE (employee_id, date),
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')

    # Create employee_documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            document_type TEXT NOT NULL, -- 'aadhaar', 'pan', 'certificate', etc.
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')

    # Create education_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS education_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            institution_name TEXT NOT NULL,
            degree TEXT NOT NULL,
            year_of_completion INTEGER, -- Year as integer
            details TEXT, -- Optional, for percentage/GPA or other notes
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')

    # Insert sample data (if any for new tables, or adjust existing)
    insert_sample_data(cursor)
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {db_path}")

def insert_sample_data(cursor):
    """Insert sample data for demonstration"""
    
    # Sample team members
    team_data = [
        ("John Smith", "CEO & Founder", "Cybersecurity expert with 15+ years experience", ""),
        ("Sarah Johnson", "CTO", "Former NSA analyst specializing in threat intelligence", ""),
        ("Mike Chen", "Lead Security Engineer", "Penetration testing and red team operations specialist", "")
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO team (name, title, bio, photo_url) 
        VALUES (?, ?, ?, ?)
    ''', team_data)
    
    # Sample careers
    careers_data = [
        ("Senior Cybersecurity Analyst", "Join our threat intelligence team to analyze and respond to advanced persistent threats.", 5, "Remote"),
        ("Penetration Tester", "Conduct security assessments and vulnerability testing for enterprise clients.", 3, "Hybrid"),
        ("SOC Engineer", "Monitor security events and respond to incidents in our 24/7 Security Operations Center.", 2, "Office")
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO careers (title, description, experience_required, location) 
        VALUES (?, ?, ?, ?)
    ''', careers_data)
    
    # Sample resources
    resources_data = [
        ("Understanding MITRE ATT&CK Framework", "Blog", "Comprehensive guide to implementing MITRE ATT&CK in your security operations."),
        ("2024 Threat Landscape Report", "Case Study", "Analysis of emerging threats and attack vectors observed in the past year."),
        ("Zero Trust Architecture Implementation", "Technical Aspect", "Technical whitepaper on implementing zero trust security models.")
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO resources (title, type, content) 
        VALUES (?, ?, ?)
    ''', resources_data)
    
    # Sample products
    products_data = [
        ("ThreatScope Pro", "Advanced threat intelligence platform with real-time monitoring and analysis.", ""),
        ("SecureShield Enterprise", "Comprehensive endpoint protection and response solution.", ""),
        ("CyberWatch 24/7", "Managed security operations center services with expert monitoring.", "")
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, description, logo_url) 
        VALUES (?, ?, ?)
    ''', products_data)

if __name__ == "__main__":
    init_database()