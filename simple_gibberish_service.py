#!/usr/bin/env python3

import http.server
import socketserver
import json
import random
import os
from urllib.parse import urlparse, parse_qs

class GibberishServiceHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"ok": True}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/validate':
            # Check API key
            api_key = self.headers.get('x-api-key', '')
            valid_keys = os.environ.get('GIBBERISH_API_KEYS', 'supersecret123').split(',')

            if api_key not in valid_keys:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": "Invalid API key"}
                self.wfile.write(json.dumps(response).encode())
                return

            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                text = data.get('text', '')

                # Simple gibberish detection
                gibberish_score = random.uniform(0.1, 0.9)

                if gibberish_score > 0.8:
                    response = {
                        "status": "refrain",
                        "clean_text": "",
                        "score": gibberish_score,
                        "flagged": [{"type": "gibberish", "score": gibberish_score}],
                        "reasons": ["Gibberish detected"]
                    }
                else:
                    response = {
                        "status": "pass",
                        "clean_text": text,
                        "score": gibberish_score,
                        "flagged": [],
                        "reasons": ["No gibberish detected"]
                    }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": str(e)}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8007))
    with socketserver.TCPServer(("", PORT), GibberishServiceHandler) as httpd:
        print(f"Gibberish Service running on port {PORT}")
        httpd.serve_forever()