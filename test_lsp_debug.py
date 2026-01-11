#!/usr/bin/env python3
"""Test MQL4 LSP completion with proper message parsing."""
import json
import subprocess
import sys
import os
import select
from pathlib import Path

REPO_ROOT = Path("/home/guillermo/source/serena-mql4/test/resources/repos/mql4/test_repo")
LSP_BINARY = Path("/home/guillermo/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server")
TEST_FILE = REPO_ROOT / "ExpertAdvisor.mq4"

def read_message(proc):
    """Read a JSON-RPC message from stdout."""
    header = b""
    content_length = 0

    # Read headers
    while True:
        line = proc.stdout.readline()
        if not line:
            return None
        header += line
        if line == b"\r\n":
            break

    # Parse Content-Length
    for line in header.decode().split("\r\n"):
        if line.startswith("Content-Length:"):
            content_length = int(line.split(":")[1].strip())
            break

    if content_length == 0:
        return None

    # Read body
    body = proc.stdout.read(content_length)
    return json.loads(body.decode())

def main():
    if not LSP_BINARY.exists():
        print(f"ERROR: LSP binary not found: {LSP_BINARY}")
        sys.exit(1)

    print(f"Using LSP: {LSP_BINARY}")
    print(f"Test file: {TEST_FILE}")

    proc = subprocess.Popen(
        [str(LSP_BINARY)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        bufsize=0,
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

        # Read initialize response
        msg = read_message(proc)
        print("\n=== Initialize Response ===")
        print(json.dumps(msg, indent=2))

        # Drain any notifications
        while select.select([proc.stdout], [], [], 0.1)[0]:
            remaining = read_message(proc)
            if remaining:
                print(f"Notification: {remaining.get('method', 'unknown')}")
            else:
                break

        # Send initialized notification
        proc.stdin.write(b"Content-Length: 22\r\n\r\n{\"jsonrpc\":\"2.0\",\"method\":\"initialized\",\"params\":{}}")
        proc.stdin.flush()

        # Drain notifications
        import time
        time.sleep(0.3)
        while select.select([proc.stdout], [], [], 0.1)[0]:
            remaining = read_message(proc)
            if remaining:
                print(f"Notification: {remaining.get('method', 'unknown')}")
            else:
                break

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

        # Drain notifications
        time.sleep(0.3)
        while select.select([proc.stdout], [], [], 0.1)[0]:
            remaining = read_message(proc)
            if remaining:
                print(f"Notification: {remaining.get('method', 'unknown')}")
            else:
                break

        # Test completion at line 21, col 20
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
        msg = read_message(proc)
        print("\n=== Completion Response ===")
        print(f"Type: {type(msg)}")
        print(json.dumps(msg, indent=2))

    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

if __name__ == "__main__":
    main()
