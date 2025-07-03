# Matrica Networks Website & Employee Portal

## 1. Project Overview

This project is a company website for "Matrica Networks Pvt Ltd," a cybersecurity intelligence platform. It includes public-facing pages (Home, About, Services, Products, Resources, Careers, Contact) and an admin portal for managing website content.

Additionally, it features an Employee Management System (EMS) with:
-   **Admin capabilities**: Managing employees (CRUD), company handbook, assigning tasks, handling leave requests, viewing employee activity.
-   **Employee capabilities**: Secure login, profile management (personal info, documents, education), viewing handbook, attendance (punch-in/out), viewing tasks, and requesting leave.

The backend is implemented using Python CGI scripts, and data is stored in an SQLite database.

## 2. Technology Stack

-   **Frontend**: HTML5, CSS3, JavaScript (ES6+)
-   **Backend**: Python 3.x (primarily CGI scripts)
-   **Database**: SQLite 3
-   **Password Hashing**: bcrypt
-   **Web Server (Local Development)**: Python's built-in `http.server`
-   **Web Server (Production - Conceptual)**: Nginx (or similar) with CGI/FastCGI support.
-   **SSL (Production - Conceptual)**: Let's Encrypt (Certbot)

## 3. Directory Structure

```
.
├── website/
│   ├── index.html                 # Main landing page
│   ├── about.html
│   ├── services.html
│   ├── products.html
│   ├── resources.html
│   ├── careers.html
│   ├── contact.html
│   ├── admin.html                 # Admin login page
│   ├── dashboard.html             # Admin dashboard
│   ├── employee_login.html        # Employee login page
│   ├── employee_dashboard.html    # Employee portal/dashboard
│   │
│   ├── assets/
│   │   ├── css/
│   │   │   └── main.css           # Main stylesheet
│   │   ├── js/
│   │   │   ├── main.js            # JS for public pages
│   │   │   ├── dashboard.js       # JS for admin dashboard
│   │   │   └── background.js      # Animated background JS
│   │   └── images/                # Static images, logos, favicon
│   │
│   ├── cgi-bin/                   # Python backend CGI scripts
│   │   ├── auth_api.py            # Admin authentication
│   │   ├── products_api.py        # Admin products CRUD
│   │   ├── resources_api.py       # Admin resources CRUD
│   │   ├── careers_api.py         # Admin careers CRUD & public GET
│   │   ├── contacts_api.py        # Admin view contacts & public form submission
│   │   ├── team_api.py            # Admin team CRUD (if applicable)
│   │   ├── employee_auth_api.py   # Employee authentication
│   │   ├── employee_admin_api.py  # Admin managing employees
│   │   ├── employee_profile_api.py # Employee self-profile updates
│   │   ├── employee_documents_api.py # Employee document uploads
│   │   ├── education_api.py       # Employee education history
│   │   ├── handbook_api.py        # Company handbook management (admin & employee view)
│   │   ├── attendance_api.py      # Employee punch-in/out
│   │   ├── tasks_api.py           # Employee view tasks (admin assign later)
│   │   ├── leave_api.py           # Employee leave requests (admin approve later)
│   │   └── submit_contact.py      # (Potentially redundant, review usage)
│   │
│   ├── database/
│   │   ├── matrica.db             # SQLite database file
│   │   └── init_db.py           # Python script to initialize/reset DB
│   │
│   └── uploads/                   # Directory for file uploads (needs write permissions)
│       ├── profile_pictures/      # Admin uploaded employee profile pics
│       ├── employee_profiles/     # Employee self-uploaded profile pics
│       ├── company_handbook/      # Uploaded company handbook PDF
│       └── employee_documents/    # Employee uploaded documents (Aadhaar, PAN, etc.)
│           └── {employee_id}/     # Subdirectory per employee for their docs
│
└── README.md                      # This file
```

## 4. Database Setup

The application uses an SQLite database (`website/database/matrica.db`). To initialize or reset the database with the required schema and sample data:

1.  Ensure you are in the root directory of the project.
2.  Run the initialization script:
    ```bash
    python website/database/init_db.py
    ```
    This will create `matrica.db` in the `website/database/` directory if it doesn't exist, or update the schema if tables are missing.

## 5. Local Development Setup

### Prerequisites

-   Python 3.7+ installed and added to your PATH.
-   `pip` (Python package installer).

### Dependencies

The primary Python dependency is `bcrypt` for password hashing. Install it using pip:

```bash
pip install bcrypt
```
You might want to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install bcrypt
# To deactivate: deactivate
```

### Running the Local Server

Python's built-in HTTP server can run CGI scripts.

1.  Navigate to the `website` directory:
    ```bash
    cd website
    ```
2.  Start the server with CGI enabled:
    *   On Python 3.7 and later:
        ```bash
        python -m http.server --cgi 8000
        ```
    *   If you encounter issues, ensure your `cgi-bin` directory is correctly named and scripts within are executable.

3.  Access the application by opening your web browser and navigating to:
    `http://localhost:8000`

    *   Admin login: `http://localhost:8000/admin.html` (Default admin credentials might need to be set or known from `auth_api.py` if it has hardcoded values, or added to `init_db.py` if an admin table exists).
    *   Employee login: `http://localhost:8000/employee_login.html` (Employees are created by Admin).

**Note on Permissions (Local):**
Ensure your CGI scripts in `website/cgi-bin/` have execute permissions. On Linux/macOS:
```bash
chmod +x website/cgi-bin/*.py
```
The `website/uploads/` directory and its subdirectories also need to be writable by the user running the Python server if file uploads are being tested.

## 6. Production Deployment (Conceptual Guide)

Deploying Python CGI applications to production requires a more robust setup. This guide provides conceptual steps using Nginx as a reverse proxy and Certbot for SSL.

**Assumptions:**
-   Server with root/sudo access (e.g., Linux VPS).
-   Nginx installed.
-   Domain name (e.g., `your_domain.com`) pointing to server's IP.

### 6.1. Prepare Application Files & Server Environment

-   Copy the `website` directory to your server (e.g., `/var/www/matrica_networks`).
-   Install Python 3, `pip`, and `bcrypt`:
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-venv
    # Consider a dedicated virtual environment for the app on the server
    # python3 -m venv /var/www/matrica_networks/venv
    # source /var/www/matrica_networks/venv/bin/activate
    pip3 install bcrypt
    ```
-   **Permissions**:
    -   CGI scripts must be executable:
        ```bash
        sudo chmod +x /var/www/matrica_networks/cgi-bin/*.py
        ```
    -   `uploads` directory and subdirectories need to be writable by the Nginx/CGI process user (often `www-data`):
        ```bash
        sudo chown -R www-data:www-data /var/www/matrica_networks/uploads
        sudo chmod -R 775 /var/www/matrica_networks/uploads # Adjust permissions as needed, 775 allows group write
        ```
    -   Database file and its directory:
        ```bash
        sudo chown www-data:www-data /var/www/matrica_networks/database/matrica.db
        sudo chown www-data:www-data /var/www/matrica_networks/database/
        sudo chmod 664 /var/www/matrica_networks/database/matrica.db # Read/Write for owner & group
        ```
    -   Initialize the database on the server:
        ```bash
        # If using a venv: source /var/www/matrica_networks/venv/bin/activate
        python3 /var/www/matrica_networks/database/init_db.py
        ```

### 6.2. Configure Nginx with CGI/FastCGI

Nginx will serve static files and pass CGI requests to a handler. `fcgiwrap` is a common choice.

1.  **Install `fcgiwrap`**:
    ```bash
    sudo apt install fcgiwrap
    ```
    `fcgiwrap` is often started as a systemd service or socket. Check its status: `sudo systemctl status fcgiwrap.socket` or `fcgiwrap.service`. Ensure it's running. The socket path is typically `/var/run/fcgiwrap.socket`.

2.  **Nginx Server Block**:
    Create `/etc/nginx/sites-available/matrica_networks`:
    ```nginx
    server {
        listen 80;
        server_name your_domain.com www.your_domain.com;

        root /var/www/matrica_networks;
        index index.html;

        access_log /var/log/nginx/matrica_access.log;
        error_log /var/log/nginx/matrica_error.log;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location ~ ^/(assets|uploads)/ {
            try_files $uri =404;
            expires 7d;
        }

        location /cgi-bin/ {
            gzip off;
            fastcgi_pass unix:/var/run/fcgiwrap.socket; # Verify this socket path

            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            # Other fastcgi_params like QUERY_STRING, REQUEST_METHOD etc. are usually in fastcgi_params

            # If using a virtual environment for Python scripts:
            # fastcgi_param PATH_INFO $fastcgi_path_info;
            # fastcgi_param VIRTUAL_ENV /var/www/matrica_networks/venv; # Path to venv
        }

        location ~ /\.ht {
            deny all;
        }
        location = /database/matrica.db { # Protect database file
            deny all;
        }
    }
    ```

3.  **Enable Site & Reload Nginx**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/matrica_networks /etc/nginx/sites-enabled/
    sudo nginx -t      # Test configuration
    sudo systemctl reload nginx
    ```

### 6.3. Setup SSL/HTTPS with Let's Encrypt (Certbot)

1.  **Install Certbot Nginx Plugin**:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    ```
2.  **Obtain and Install Certificate**:
    ```bash
    sudo certbot --nginx -d your_domain.com -d www.your_domain.com
    ```
    Follow prompts (provide email, agree to ToS). Choose whether to redirect HTTP to HTTPS (recommended).

3.  **Verify Auto-Renewal**:
    Certbot sets up automatic renewal. Test it:
    ```bash
    sudo certbot renew --dry-run
    ```

## 7. Application Structure Overview

-   **Public Pages (`*.html`)**: Static HTML files for general website content.
-   **Admin Portal (`admin.html`, `dashboard.html`)**: For content and employee management. Uses `dashboard.js`.
-   **Employee Portal (`employee_login.html`, `employee_dashboard.html`)**: For employee self-service. Uses JavaScript embedded in `employee_dashboard.html`.
-   **Static Assets (`assets/`)**: CSS, public JavaScript, images.
-   **CGI Scripts (`cgi-bin/`)**: Python scripts acting as backend API endpoints. They handle requests, interact with SQLite, and return JSON.
    -   Authentication: `auth_api.py` (admin), `employee_auth_api.py` (employee).
    -   Admin specific: `products_api.py`, `resources_api.py`, `careers_api.py`, `contacts_api.py`, `team_api.py`, `employee_admin_api.py`, `handbook_api.py` (for admin upload/delete).
    -   Employee specific: `employee_profile_api.py`, `employee_documents_api.py`, `education_api.py`, `attendance_api.py`, `tasks_api.py`, `leave_api.py`.
    -   Shared: `handbook_api.py` (for employee view).
-   **Database (`database/`)**: SQLite DB file (`matrica.db`) and initialization script (`init_db.py`).
-   **Uploads (`uploads/`)**: Stores user-uploaded files. Requires write permissions for the web server process.

## 8. Logging

-   **CGI Script Errors & Python `stderr`**: Python CGI scripts, by default, send their `stdout` as the HTTP response and `stderr` to the web server's error log. The application's Python scripts have been configured to also print unhandled exceptions to `stderr`, which will typically end up in the web server's error log (e.g., `/var/log/nginx/error_log` or `/var/log/nginx/matrica_error.log` as configured for Nginx, or to the console if using `python -m http.server --cgi`).

-   **Application Log File**:
    -   The application implements more detailed logging using Python's `logging` module.
    -   **Location**: Log messages are written to `website/logs/app.log`.
    -   **Format**: `YYYY-MM-DD HH:MM:SS - LEVEL - [script_name.py] - Message`
    -   **Content**: Includes informational messages about requests, actions taken, warnings for non-critical issues, and detailed error messages with stack traces for exceptions.
    -   **Viewing Logs**: You can view the application log using standard command-line tools:
        ```bash
        # View the entire log
        cat website/logs/app.log

        # Tail the log in real-time
        tail -f website/logs/app.log

        # Filter for errors
        grep "ERROR" website/logs/app.log
        ```
    -   **Permissions**: Ensure the `website/logs/` directory is writable by the user/process running the CGI scripts (e.g., `www-data` in a typical Nginx setup). The `logger_config.py` attempts to create this directory if it doesn't exist, but write permissions are crucial.
        ```bash
        # Example permission setting on the server:
        sudo chown -R www-data:www-data /var/www/matrica_networks/logs
        sudo chmod -R u+rwX,g+rwX,o+rX /var/www/matrica_networks/logs
        ```
    -   **Log Rotation (Production)**: For production environments, it is crucial to set up log rotation for `website/logs/app.log` (and server logs) to prevent them from consuming excessive disk space. This is typically done using system utilities like `logrotate`. Configuration for `logrotate` is outside the scope of this application's code but is a standard server administration task.

-   **Nginx Logs**: As mentioned in the deployment section, Nginx access and error logs (e.g., `/var/log/nginx/matrica_access.log`, `/var/log/nginx/matrica_error.log`) are vital for diagnosing request handling issues at the web server level.
```
