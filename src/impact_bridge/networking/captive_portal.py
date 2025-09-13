"""Captive portal for redirecting to bridge.local in AP mode."""

import logging
from flask import Flask, request, redirect, jsonify, render_template_string
from typing import Optional

logger = logging.getLogger(__name__)


class CaptivePortal:
    """Captive portal that redirects clients to bridge.local in AP mode."""
    
    def __init__(self, bridge_url: str = "http://bridge.local"):
        """Initialize CaptivePortal.
        
        Args:
            bridge_url: URL to redirect clients to
        """
        self.bridge_url = bridge_url
        self.app = Flask(__name__)
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Setup captive portal routes."""
        
        @self.app.route('/')
        def index():
            """Main captive portal page."""
            return self._redirect_to_bridge()
        
        @self.app.route('/generate_204')
        @self.app.route('/connecttest.txt')  
        @self.app.route('/hotspot-detect.html')
        @self.app.route('/ncsi.txt')
        def captive_portal_detection():
            """Handle various captive portal detection requests."""
            return self._redirect_to_bridge()
        
        @self.app.route('/status')
        def status():
            """Status endpoint for the captive portal."""
            return jsonify({
                "status": "active",
                "bridge_url": self.bridge_url,
                "message": "Captive portal is active"
            })
        
        @self.app.route('/<path:path>')
        def catch_all(path):
            """Catch all other requests and redirect."""
            return self._redirect_to_bridge()
    
    def _redirect_to_bridge(self):
        """Redirect to bridge.local with splash page."""
        # Check if this is an AJAX request or API call
        if request.headers.get('Accept', '').startswith('application/json'):
            return jsonify({
                "redirect": self.bridge_url,
                "message": "Please connect to LeadVille Bridge"
            }), 302
        
        # For browser requests, show a redirect page
        redirect_page = '''
<!DOCTYPE html>
<html>
<head>
    <title>LeadVille Bridge</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            margin-bottom: 20px;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .button:hover {
            background-color: #0056b3;
        }
        .loader {
            display: none;
            margin: 20px auto;
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    <script>
        function connectToBridge() {
            document.getElementById('loader').style.display = 'block';
            setTimeout(function() {
                window.location.href = '{{ bridge_url }}';
            }, 1000);
        }
        
        // Auto-redirect after 3 seconds
        setTimeout(function() {
            connectToBridge();
        }, 3000);
    </script>
</head>
<body>
    <div class="container">
        <h1>🎯 LeadVille Bridge</h1>
        <p>Welcome to LeadVille Impact Bridge System</p>
        <p>You will be redirected to the bridge interface automatically in 3 seconds.</p>
        <div class="loader" id="loader"></div>
        <p>
            <a href="{{ bridge_url }}" class="button" onclick="connectToBridge()">
                Connect Now
            </a>
        </p>
        <p style="font-size: 12px; color: #999;">
            If automatic redirection fails, click "Connect Now" or navigate to {{ bridge_url }}
        </p>
    </div>
</body>
</html>
        '''
        
        return render_template_string(redirect_page, bridge_url=self.bridge_url)
    
    def run(self, host: str = '0.0.0.0', port: int = 80, debug: bool = False) -> None:
        """Run the captive portal server.
        
        Args:
            host: Host to bind to
            port: Port to bind to (usually 80 for captive portal)
            debug: Enable debug mode
        """
        logger.info(f"Starting captive portal on {host}:{port}")
        logger.info(f"Redirecting to: {self.bridge_url}")
        
        self.app.run(host=host, port=port, debug=debug)
        
    def get_app(self) -> Flask:
        """Get the Flask app instance for integration with other servers."""
        return self.app