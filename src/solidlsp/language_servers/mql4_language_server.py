"""
Provides MQL4 specific instantiation of the LanguageServer class.
Uses the external MQL4 Language Server by davalillo (https://github.com/davalillo/mql4-language-server).
This LSP server provides full MQL4 language support including go-to-definition, references, completion, and hover.
"""

import logging
import os
import pathlib
import threading

from solidlsp import ls_types
from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings

from .common import RuntimeDependency, RuntimeDependencyCollection


class Mql4LanguageServer(SolidLanguageServer):
    """
    MQL4 Language Server wrapper using external LSP implementation.
    Provides MQL4 (MetaTrader 4) language support via LSP protocol.

    The external LSP server is developed in .NET 8 with ANTLR 4.13.1 parser
    and provides comprehensive MQL4 language features.
    """

    def __init__(
        self, config: LanguageServerConfig, logger: LanguageServerLogger, repository_root_path: str, solidlsp_settings: SolidLSPSettings
    ):
        """
        Creates a Mql4LanguageServer instance. This class is not meant to be instantiated directly.
        Use LanguageServer.create() instead.
        """
        mql4_ls_executable_path = self._setup_runtime_dependencies(logger, config, solidlsp_settings)
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=mql4_ls_executable_path, cwd=repository_root_path),
            "mql4",
            solidlsp_settings,
        )
        self.server_ready = threading.Event()
        self.service_ready_event = threading.Event()

    def _ensure_server_ready(self) -> None:
        """
        Ensures the MQL4 LSP server is ready before processing requests.
        Waits for server_ready event with a timeout.
        """
        if not self.server_ready.is_set():
            self.logger.log(
                "MQL4 LSP server not ready, waiting for initialization...",
                logging.WARNING,
            )
            import time
            start_time = time.time()
            timeout = 30  # Additional 30 seconds wait
            while not self.server_ready.is_set() and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if not self.server_ready.is_set():
                self.logger.log(
                    "MQL4 LSP server still not ready after extended wait, proceeding anyway",
                    logging.WARNING,
                )

    def request_definition(self, relative_file_path: str, line: int, column: int) -> list[ls_types.Location]:
        """
        Override request_definition to ensure server is ready before making the request.
        """
        self._ensure_server_ready()
        return super().request_definition(relative_file_path, line, column)

    def request_references(self, relative_file_path: str, line: int, column: int) -> list[ls_types.Location]:
        """
        Override request_references to ensure server is ready before making the request.
        """
        self._ensure_server_ready()
        return super().request_references(relative_file_path, line, column)

    @classmethod
    def get_language_enum_instance(cls) -> "Language":
        """
        Returns the Language enum instance for MQL4.
        """
        from solidlsp.ls_config import Language

        return Language.MQL4

    @classmethod
    def _setup_runtime_dependencies(
        cls, logger: LanguageServerLogger, config: LanguageServerConfig, solidlsp_settings: SolidLSPSettings
    ) -> str:
        """
        Setup runtime dependencies for Mql4LanguageServer and return the command to start the server.
        Downloads the appropriate binary from GitHub releases if not already installed.
        """
        import shutil
        import platform

        deps = RuntimeDependencyCollection(
            [
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description="MQL4 Language Server v1.3.0 for Linux (x64)",
                    url="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-linux-x64",
                    platform_id="linux-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description="MQL4 Language Server v1.3.0 for macOS (x64)",
                    url="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-x64",
                    platform_id="osx-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description="MQL4 Language Server v1.3.0 for macOS (Arm64)",
                    url="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-arm64",
                    platform_id="osx-arm64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description="MQL4 Language Server v1.3.0 for Windows (x64)",
                    url="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-win-x64.exe",
                    platform_id="win-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server.exe",
                ),
            ]
        )

        mql4_ls_dir = os.path.join(cls.ls_resources_dir(solidlsp_settings), "mql4-lsp")

        try:
            dep = deps.get_single_dep_for_current_platform()
        except RuntimeError:
            dep = None

        if dep is None:
            # No prebuilt binary available for this platform
            raise FileNotFoundError(
                f"MQL4 Language Server is not available for platform {platform.system()}.\n"
                + "Please visit https://github.com/davalillo/mql4-language-server/releases for manually downloaded binaries.\n"
                + "Supported platforms: Linux x64, macOS (x64 and Arm64), Windows x64"
            )

        # Check if binary exists, otherwise download it
        mql4_ls_executable_path = deps.binary_path(mql4_ls_dir)
        if not os.path.exists(mql4_ls_executable_path):
            logger.log(
                f"MQL4 LSP executable not found at {mql4_ls_executable_path}. Downloading from {dep.url}",
                logging.INFO,
            )
            _ = deps.install(logger, mql4_ls_dir)

        if not os.path.exists(mql4_ls_executable_path):
            raise FileNotFoundError(
                f"MQL4 LSP executable not found at {mql4_ls_executable_path}.\n"
                + f"Download may have failed. Please try again or visit: https://github.com/davalillo/mql4-language-server/releases"
            )

        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(mql4_ls_executable_path, 0o755)

        logger.log(f"MQL4 Language Server ready at {mql4_ls_executable_path}", logging.INFO)
        return mql4_ls_executable_path

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the MQL4 Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params = {
            "locale": "en",
            "capabilities": {
                "textDocument": {
                    "synchronization": {"didSave": True, "dynamicRegistration": True},
                    "completion": {"dynamicRegistration": True, "completionItem": {"snippetSupport": True}},
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "hover": {"dynamicRegistration": True},
                    "documentSymbol": {"dynamicRegistration": True},
                },
                "workspace": {"workspaceFolders": True, "didChangeConfiguration": {"dynamicRegistration": True}},
            },
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": root_uri,
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": "$name",
                }
            ],
        }

        return initialize_params

    def _start_server(self):
        """
        Starts the MQL4 Language Server, waits for the server to be ready and yields the LanguageServer instance.

        Usage:
        ```
        async with lsp.start_server():
            # LanguageServer has been initialized and ready to serve requests
            await lsp.request_definition(...)
            await lsp.request_references(...)
            # Shutdown the LanguageServer on exit from scope
        # LanguageServer has been shutdown
        """

        def register_capability_handler(params):
            assert "registrations" in params
            for registration in params["registrations"]:
                if registration["method"] == "workspace/executeCommand":
                    # Handle custom commands if needed
                    pass
            return

        def lang_status_handler(params):
            # Handle language server status notifications
            if params.get("type") == "ServiceReady" and params.get("message") == "ServiceReady":
                self.service_ready_event.set()

        def execute_client_command_handler(params):
            return []

        def do_nothing(params):
            return

        def check_experimental_status(params):
            # The server is ready when it reports quiescent status
            if params.get("quiescent") == True:
                self.server_ready.set()

        def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        # Register all necessary handlers
        self.server.on_request("client/registerCapability", register_capability_handler)
        self.server.on_notification("language/status", lang_status_handler)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request("workspace/executeClientCommand", execute_client_command_handler)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("language/actionableNotification", do_nothing)
        self.server.on_notification("experimental/serverStatus", check_experimental_status)

        self.logger.log("Starting MQL4 LSP server process", logging.INFO)
        self.server.start()

        # Send initialize request
        initialize_params = self._get_initialize_params(self.repository_root_path)
        self.logger.log(
            "Sending initialize request from LSP client to MQL4 LSP server and awaiting response",
            logging.INFO,
        )
        init_response = self.server.send.initialize(initialize_params)

        # Verify basic capabilities
        assert "capabilities" in init_response
        capabilities = init_response["capabilities"]

        # Check for textDocumentSync (can be in capabilities or capabilities.textDocument)
        has_sync = "textDocumentSync" in capabilities
        if not has_sync and "textDocument" in capabilities:
            has_sync = "synchronization" in capabilities["textDocument"]

        # Check for completion capability
        has_completion = "completionProvider" in capabilities or "completion" in capabilities.get("textDocument", {})

        self.logger.log(f"MQL4 LSP capabilities verified - Sync: {has_sync}, Completion: {has_completion}", logging.INFO)
        self.logger.log(f"Server capabilities: {capabilities}", logging.INFO)

        # Mark server as initialized
        self.server.notify.initialized({})

        # Signal that completions are available
        self.completions_available.set()

        # Wait for server to be fully ready (with timeout)
        import time
        start_time = time.time()
        timeout = 60  # 60 seconds timeout
        while not self.server_ready.is_set() and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if self.server_ready.is_set():
            self.logger.log("MQL4 LSP server is ready", logging.INFO)
        else:
            self.logger.log("MQL4 LSP server initialization timeout, proceeding anyway", logging.WARNING)
