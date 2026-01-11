#!/usr/bin/env python3
"""Simple test for MQL4 LSP completion."""
import json
import subprocess
import sys
import os
from pathlib import Path

REPO_ROOT = Path("/home/guillermo/source/serena-mql4/test/resources/repos/mql4/test_repo")
LSP_BINARY = Path("/home/guillermo/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server")
TEST_FILE = REPO_ROOT / "ExpertAdvisor.mq4"

def main():
    if not LSP_BINARY.exists():
        print(f"ERROR: LSP binary not found: {LSP_BINARY}")
        sys.exit(1)

    print(f"Using LSP: {LSP_BINARY}")
    print(f"Using test file: {TEST_FILE}")
    print(f"CWD: {REPO_ROOT}")

    proc = subprocess.Popen(
        [str(LSP_BINARY)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )

    try:
        # Initialize
        init_params = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": REPO_ROOT.as_uri(),
                "workspaceFolders": [{"uri": REPO_ROOT.as_uri(), "name": "test_repo"}],
                "capabilities": {},
            },
        }

        content = json.dumps(init_params)
        proc.stdin.write(f"Content-Length: {len(content)}\r\n\r\n{content}".encode())
        proc.stdin.flush()

        # Read response
        header = b""
        while True:
            line = proc.stdout.readline()
            header += line
            if line == b"\r\n":
                break

        content_length = 0
        for line in header.decode().split("\r\n"):
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
                break

        body = proc.stdout.read(content_length)
        response = json.loads(body.decode())
        print("\n=== Initialize Response ===")
        print(json.dumps(response, indent=2))

        # Send initialized notification
        proc.stdin.write(b"Content-Length: 22\r\n\r\n{\"jsonrpc\":\"2.0\",\"method\":\"initialized\",\"params\":{}}")
        proc.stdin.flush()

        # Open document
        file_uri = TEST_FILE.as_uri()
        file_content = TEST_FILE.read_text()
        did_open = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {"uri": file_uri, "languageId": "mql4", "version": 1, "text": file_content}
            },
        }
        content = json.dumps(did_open)
        proc.stdin.write(f"Content-Length: {len(content)}\r\n\r\n{content}".encode())
        proc.stdin.flush()

        # Wait a bit for server to process
        import time
        time.sleep(0.5)

        # Test completion at line 21
        print("\n=== Testing completion at line 21, col 20 ===")
        completion = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": 21, "character": 20},
            },
        }
        content = json.dumps(completion)
        proc.stdin.write(f"Content-Length: {len(content)}\r\n\r\n{content}".encode())
        proc.stdin.flush()

        # Read completion response
        header = b""
        while True:
            byte = proc.stdout.read(1)
            if not byte:
                break
            header += byte
            if header.endswith(b"\r\n\r\n"):
                break

        content_length = 0
        for line in header.decode().split("\r\n"):
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
                break

        if content_length > 0:
            body = proc.stdout.read(content_length)
            response = json.loads(body.decode())
            print("\n=== Completion Response ===")
            print(f"Type: {type(response)}")
            print(f"Value: {json.dumps(response, indent=2)}")
        else:
            print("No completion response received")

    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

if __name__ == "__main__":
    main()
