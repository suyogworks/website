#!/usr/bin/env python3
"""
Simple HTTP server for Matrica Networks website
Serves static files and handles CGI scripts
"""

import http.server
import socketserver
import os
import sys
from http.server import CGIHTTPRequestHandler, HTTPServer

class MatricaHTTPRequestHandler(CGIHTTPRequestHandler):
    """Custom HTTP request handler with CORS support"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.end_headers()
    
    def do_DELETE(self):
        """Handle DELETE requests by treating them as CGI requests"""
        if self.is_cgi():
            self.run_cgi()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_PUT(self):
        """Handle PUT requests by treating them as CGI requests"""
        if self.is_cgi():
            self.run_cgi()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")

class MatricaHTTPServer(HTTPServer):
    """Custom HTTP server with proper server_name attribute"""
    
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.server_name = server_address[0]
        self.server_port = server_address[1]

def run_server(port=12000, host='0.0.0.0'):
    """Run the HTTP server"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Set CGI directories
    handler = MatricaHTTPRequestHandler
    handler.cgi_directories = ['/cgi-bin']
    
    # Create server
    with MatricaHTTPServer((host, port), handler) as httpd:
        print(f"🚀 Matrica Networks server starting...")
        print(f"📍 Server address: http://{host}:{port}")
        print(f"📁 Serving from: {os.getcwd()}")
        print(f"🔧 CGI enabled for: {handler.cgi_directories}")
        print(f"🌐 Access URLs:")
        print(f"   • Main site: http://localhost:{port}")
        print(f"   • Admin panel: http://localhost:{port}/admin.html")
        print(f"   • Dashboard: http://localhost:{port}/dashboard.html")
        print(f"🔐 Admin credentials: psychy / Scambanenabler")
        print(f"📊 Server ready! Press Ctrl+C to stop.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
    run_server(port)