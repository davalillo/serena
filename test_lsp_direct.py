#!/usr/bin/env python3
"""
Test script to debug MQL4 LSP completion response.
This script communicates directly with the MQL4 LSP server via JSON-RPC.
"""
import json
import subprocess
import sys
import os
import time
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent
LSP_BINARY = Path("/home/guillermo/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server")
TEST_FILE = Path("/home/guillermo/source/serena-mql4/test/resources/repos/mql4/test_repo/ExpertAdvisor.mq4")

def send_request(proc, request):
    """Send JSON-RPC request and get response."""
    content = json.dumps(request)
    headers = f"Content-Length: {len(content)}\r\n\r\n"
    proc.stdin.write(headers.encode())
    proc.stdin.write(content.encode())
    proc.stdin.flush()

    # Read response headers
    response = b""
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        response += line
        if line == b"\r\n":
            break

    # Read content
    content_length = 0
    for line in response.decode().split("\r\n"):
        if line.startswith("Content-Length:"):
            content_length = int(line.split(":")[1].strip())
            break

    if content_length > 0:
        body = proc.stdout.read(content_length)
        return json.loads(body.decode())
    return None

def main():
    # Check if LSP binary exists
    if not LSP_BINARY.exists():
        print(f"LSP binary not found at {LSP_BINARY}")
        print("Run tests first to download it, or manually download from:")
        print("https://github.com/davalillo/mql4-language-server-releases/releases")
        sys.exit(1)

    # Start LSP process
    print(f"Starting MQL4 LSP from {LSP_BINARY}")
    proc = subprocess.Popen(
        [str(LSP_BINARY)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(TEST_FILE.parent),
    )

    try:
        # Initialize
        initialize_params = {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "completion": {"dynamicRegistration": True, "completionItem": {"snippetSupport": True}},
                },
                "workspace": {"workspaceFolders": True},
            },
            "processId": os.getpid(),
            "rootUri": REPO_ROOT.as_uri(),
            "workspaceFolders": [{"uri": REPO_ROOT.as_uri(), "name": "serena-mql4"}],
        }

        print("\n=== Sending initialize ===")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": initialize_params,
        }
        response = send_request(proc, init_request)
        print(f"Initialize response: {json.dumps(response, indent=2)}")

        # Send initialized notification
        proc.stdin.write(b"Content-Length: 22\r\n\r\n{\"jsonrpc\":\"2.0\",\"method\":\"initialized\",\"params\":{}}")
        proc.stdin.flush()
        time.sleep(0.5)

        # Open document
        file_uri = TEST_FILE.as_uri()
        print(f"\n=== Opening document: {file_uri} ===")
        did_open = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": file_uri,
                    "languageId": "mql4",
                    "version": 1,
                    "text": TEST_FILE.read_text(),
                }
            },
        }
        send_request(proc, did_open)
        time.sleep(0.5)

        # Test completion at line 21 (inside OnInit function)
        print("\n=== Testing textDocument/completion at line 21, col 20 ===")
        completion_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": 21, "character": 20},
            },
        }
        response = send_request(proc, completion_request)
        print(f"Completion response type: {type(response)}")
        print(f"Completion response: {json.dumps(response, indent=2)}")

        # Test completion at empty line (line 60)
        print("\n=== Testing textDocument/completion at line 60, col 0 (empty line) ===")
        completion_request2 = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": 60, "character": 0},
            },
        }
        response2 = send_request(proc, completion_request2)
        print(f"Completion response type: {type(response2)}")
        print(f"Completion response: {json.dumps(response2, indent=2)}")

    finally:
        proc.stdin.close()
        proc.wait(timeout=5)

if __name__ == "__main__":
    main()
