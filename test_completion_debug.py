#!/usr/bin/env python3
"""Debug MQL4 LSP completion response."""
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

# Create the language server
gitignore_parser = GitignoreParser(str(REPO_PATH))
ignored_paths = []
for spec in gitignore_parser.get_ignore_specs():
    ignored_paths.extend(spec.patterns)

config = LanguageServerConfig(code_language=Language.MQL4, ignored_paths=ignored_paths)
logger = LanguageServerLogger(log_level=40)  # ERROR level
settings = SolidLSPSettings(solidlsp_dir=SERENA_MANAGED_DIR_IN_HOME, project_data_relative_path=SERENA_MANAGED_DIR_NAME)

ls = SolidLanguageServer.create(config, logger, str(REPO_PATH), solidlsp_settings=settings)

print("Starting MQL4 LSP server...")
ls.start()

try:
    print("\n=== Testing completion at line 21, col 20 ===")
    completions = ls.request_completions("ExpertAdvisor.mq4", 21, 20)
    print(f"Type: {type(completions)}")
    print(f"Is dict: {isinstance(completions, dict)}")
    print(f"Is list: {isinstance(completions, list)}")
    print(f"Value: {completions}")
    print(f"repr: {repr(completions)}")

    print("\n=== Testing completion at line 60, col 0 (empty line) ===")
    completions2 = ls.request_completions("ExpertAdvisor.mq4", 60, 0)
    print(f"Type: {type(completions2)}")
    print(f"Value: {completions2}")

finally:
    print("\nStopping server...")
    ls.stop()
    print("Done.")
