#!/usr/bin/env python3
import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='dist', **kwargs)
    
    def do_GET(self):
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Remove leading slash and decode
        if path.startswith('/'):
            path = path[1:]
        
        # If it's a file request (has extension) or specific asset paths
        if ('.' in path and not path.endswith('/')) or path.startswith('assets/'):
            # Serve the actual file
            super().do_GET()
        else:
            # For all other routes, serve index.html (SPA routing)
            self.path = '/'
            super().do_GET()

PORT = 3001
Handler = SPAHandler

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    print(f'React SPA server running on port {PORT}')
    print(f'Visit: http://localhost:{PORT}')
    httpd.serve_forever()
