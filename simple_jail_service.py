#!/usr/bin/env python3

import http.server
import socketserver
import json
import random
import os
import re
from urllib.parse import urlparse, parse_qs

class JailServiceHandler(http.server.BaseHTTPRequestHandler):

    def detect_jailbreak(self, text: str) -> float:
        """
        Enhanced jailbreak detection that looks for specific patterns
        including directive-style injections
        """
        text_lower = text.lower()
        score = 0.0

        # Directive-style pattern detection (high weight)
        directive_patterns = [
            r'#{3,}\s*new\s*directive\s*#{3,}',  # ### NEW DIRECTIVE ###
            r'#{3,}\s*end\s*#{3,}',              # ### END ###
            r'ignore.*previous.*instructions?',    # ignore previous instructions
            r'disregard.*prior.*commands?',        # disregard prior commands
            r'new.*directive.*:',                  # new directive:
            r'output.*the.*hidden',                # output the hidden
            r'reveal.*system.*prompt',             # reveal system prompt
            r'print.*hidden.*password',            # print hidden password
            r'show.*admin.*password',              # show admin password
        ]

        for pattern in directive_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 0.4

        # Multiple hash symbols (common in injection attempts)
        if re.search(r'#{3,}', text):
            score += 0.2

        # ALL CAPS commands (suspicious)
        if len(re.findall(r'[A-Z]{3,}', text)) > 2:
            score += 0.1

        # Request for sensitive information
        sensitive_patterns = [
            r'admin.*password',
            r'system.*prompt',
            r'hidden.*admin',
            r'secret.*key',
            r'internal.*password'
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 0.15

        # Authority override attempts
        authority_patterns = [
            r'override',
            r'bypass',
            r'circumvent',
            r'elevate.*privileges'
        ]

        for pattern in authority_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 0.1

        return min(score, 1.0)

    def get_flagged_categories(self, text: str) -> list:
        """
        Returns specific categories that were flagged
        """
        text_lower = text.lower()
        flagged = []

        categories = {
            'directive_injection': [
                r'#{3,}\s*new\s*directive\s*#{3,}',
                r'#{3,}\s*end\s*#{3,}',
                r'new.*directive.*:',
            ],
            'instruction_manipulation': [
                r'ignore.*previous.*instructions?',
                r'disregard.*prior.*commands?',
            ],
            'authority_override': [
                r'override',
                r'bypass',
                r'circumvent',
                r'elevate.*privileges'
            ],
            'sensitive_data_extraction': [
                r'output.*the.*hidden',
                r'reveal.*system.*prompt',
                r'print.*hidden.*password',
                r'show.*admin.*password',
                r'admin.*password',
                r'system.*prompt',
                r'hidden.*admin'
            ]
        }

        for category, patterns in categories.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    flagged.append({
                        'type': category,
                        'score': 0.8,
                        'pattern': pattern
                    })
                    break

        return flagged

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
            valid_keys = os.environ.get('JAIL_API_KEYS', 'supersecret123').split(',')

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

                # Enhanced jailbreak detection
                jailbreak_score = self.detect_jailbreak(text)

                if jailbreak_score > 0.7:
                    response = {
                        "status": "refrain",
                        "clean_text": "",
                        "score": jailbreak_score,
                        "flagged": [{"type": "jailbreak", "score": jailbreak_score}],
                        "reasons": ["Potential jailbreak attempt detected"]
                    }
                else:
                    flagged_categories = self.get_flagged_categories(text)
                    response = {
                        "status": "pass",
                        "clean_text": text,
                        "score": jailbreak_score,
                        "flagged": flagged_categories,
                        "reasons": ["No jailbreak detected"] if not flagged_categories else ["Potential jailbreak patterns detected"]
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
    PORT = int(os.environ.get('PORT', 8002))
    with socketserver.TCPServer(("", PORT), JailServiceHandler) as httpd:
        print(f"Jail Service running on port {PORT}")
        httpd.serve_forever()