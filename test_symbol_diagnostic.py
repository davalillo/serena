#!/usr/bin/env python3
"""Test workspace/symbol and diagnostic methods."""
import sys
sys.path.insert(0, '/home/guillermo/source/serena-mql4/src')

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import Language, LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.settings import SolidLSPSettings
from serena.constants import SERENA_MANAGED_DIR_IN_HOME, SERENA_MANAGED_DIR_NAME
from serena.util.file_system import GitignoreParser
from pathlib import Path

REPO_PATH = Path("/home/guillermo/source/serena-mql4/test/resources/repos/mql4/test_repo")

gitignore_parser = GitignoreParser(str(REPO_PATH))
ignored_paths = []
for spec in gitignore_parser.get_ignore_specs():
    ignored_paths.extend(spec.patterns)

config = LanguageServerConfig(code_language=Language.MQL4, ignored_paths=ignored_paths)
logger = LanguageServerLogger(log_level=40)
settings = SolidLSPSettings(solidlsp_dir=SERENA_MANAGED_DIR_IN_HOME, project_data_relative_path=SERENA_MANAGED_DIR_NAME)

ls = SolidLanguageServer.create(config, logger, str(REPO_PATH), solidlsp_settings=settings)

print("Starting MQL4 LSP server...")
ls.start()

try:
    print("\n=== Testing workspace/symbol ===")
    try:
        result = ls.request_workspace_symbol('OnInit')
        print(f'Type: {type(result)}')
        print(f'Value: {result}')
    except Exception as e:
        print(f'Error: {e}')

    print("\n=== Testing textDocument/diagnostic ===")
    try:
        result = ls.request_text_document_diagnostics('ExpertAdvisor.mq4')
        print(f'Type: {type(result)}')
        print(f'Value: {result}')
    except Exception as e:
        print(f'Error: {e}')

finally:
    ls.stop()
    print("\nDone.")
