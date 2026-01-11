"""
Provides MQL4 specific instantiation of the LanguageServer class.
Uses the external MQL4 Language Server by davalillo (https://github.com/davalillo/mql4-language-server-releases).
This LSP server provides full MQL4 language support including go-to-definition, references, completion, and hover.
"""

import logging
import os
import pathlib
import threading
from typing import TYPE_CHECKING, Any

from solidlsp import ls_types
from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings

from .common import RuntimeDependency, RuntimeDependencyCollection

if TYPE_CHECKING:
    from solidlsp.ls_config import Language


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
        from solidlsp.ls_config import Language  # type: ignore[import-untyped]

        return Language.MQL4

    @classmethod
    def _setup_runtime_dependencies(
        cls, logger: LanguageServerLogger, config: LanguageServerConfig, solidlsp_settings: SolidLSPSettings
    ) -> str:
        """
        Setup runtime dependencies for Mql4LanguageServer and return the command to start the server.
        Downloads the appropriate binary from GitHub releases if not already installed.
        Supports SHA256 checksum verification and fallback to system-installed binary.
        """
        import hashlib
        import shutil
        import urllib.error
        import urllib.request

        # Version and base URL configuration
        LSP_VERSION = "v1.7.0"
        BASE_URL = f"https://github.com/davalillo/mql4-language-server-releases/releases/download/{LSP_VERSION}"
        CHECKSUMS_URL = f"{BASE_URL}/CHECKSUMS.txt"

        logger.log(f"[MQL4 LSP] Starting setup for version {LSP_VERSION}", logging.INFO)

        # Platform-specific configuration
        deps = RuntimeDependencyCollection(
            [
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description=f"MQL4 Language Server {LSP_VERSION} for Linux (x64)",
                    url=f"{BASE_URL}/mql4-lsp-server-linux-x64",
                    platform_id="linux-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description=f"MQL4 Language Server {LSP_VERSION} for macOS (x64)",
                    url=f"{BASE_URL}/mql4-lsp-server-osx-x64",
                    platform_id="osx-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description=f"MQL4 Language Server {LSP_VERSION} for macOS (Arm64)",
                    url=f"{BASE_URL}/mql4-lsp-server-osx-arm64",
                    platform_id="osx-arm64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server",
                ),
                RuntimeDependency(
                    id="Mql4LanguageServer",
                    description=f"MQL4 Language Server {LSP_VERSION} for Windows (x64)",
                    url=f"{BASE_URL}/mql4-lsp-server-win-x64.exe",
                    platform_id="win-x64",
                    archive_type="binary",
                    binary_name="mql4-lsp-server.exe",
                ),
            ]
        )

        mql4_ls_dir = os.path.join(cls.ls_resources_dir(solidlsp_settings), "mql4-lsp")
        logger.log(f"[MQL4 LSP] Resource directory: {mql4_ls_dir}", logging.DEBUG)

        # Get dependency for current platform
        try:
            dep = deps.get_single_dep_for_current_platform()
            logger.log(f"[MQL4 LSP] Platform dependency found: {dep.description}", logging.INFO)
        except RuntimeError:
            dep = None
            logger.log("[MQL4 LSP] No prebuilt binary available for current platform", logging.WARNING)

        if dep is None:
            # Try system-installed binary as fallback
            logger.log("[MQL4 LSP] No platform-specific binary, checking system PATH...", logging.INFO)
            system_ls = shutil.which("mql4-lsp-server")
            if system_ls:
                logger.log(f"[MQL4 LSP] Found system-installed binary at: {system_ls}", logging.INFO)
                return system_ls
            raise FileNotFoundError(
                "MQL4 Language Server is not available for this platform.\n"
                + "Please visit https://github.com/davalillo/mql4-language-server-releases/releases\n"
                + "Supported platforms: Linux x64, macOS (x64 and Arm64), Windows x64"
            )

        # Determine executable path
        mql4_ls_executable_path = deps.binary_path(mql4_ls_dir)
        logger.log(f"[MQL4 LSP] Expected executable path: {mql4_ls_executable_path}", logging.DEBUG)

        # Step 1: Check if binary already exists locally
        if os.path.exists(mql4_ls_executable_path):
            logger.log(f"[MQL4 LSP] Binary found in cache: {mql4_ls_executable_path}", logging.INFO)
            cls._verify_and_set_executable(mql4_ls_executable_path, logger)
            return mql4_ls_executable_path

        logger.log("[MQL4 LSP] Binary not in cache, attempting download...", logging.INFO)

        # Step 2: Try to download checksums file first
        checksums: dict[str, str] = {}
        try:
            logger.log(f"[MQL4 LSP] Fetching checksums from: {CHECKSUMS_URL}", logging.INFO)
            with urllib.request.urlopen(CHECKSUMS_URL, timeout=10) as response:
                checksums_content = response.read().decode("utf-8")
                logger.log("[MQL4 LSP] Checksums file downloaded successfully", logging.DEBUG)

            # Parse checksums (format: "sha256hash  filename")
            for line in checksums_content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    file_hash, file_name = parts
                    checksums[file_name] = file_hash

            if dep.binary_name:
                expected_hash = checksums.get(dep.binary_name)
            else:
                expected_hash = None
            if expected_hash:
                logger.log(f"[MQL4 LSP] Expected SHA256 for {dep.binary_name}: {expected_hash[:16]}...", logging.INFO)
            else:
                logger.log(f"[MQL4 LSP] WARNING: No checksum found for {dep.binary_name}", logging.WARNING)
        except urllib.error.URLError as e:
            logger.log(f"[MQL4 LSP] Failed to fetch checksums: {e}. Continuing without verification...", logging.WARNING)
        except Exception as e:
            logger.log(f"[MQL4 LSP] Error parsing checksums file: {e}. Continuing without verification...", logging.WARNING)

        # Step 3: Download the binary
        os.makedirs(mql4_ls_dir, exist_ok=True)
        try:
            logger.log(f"[MQL4 LSP] Downloading from: {dep.url}", logging.INFO)
            deps.install(logger, mql4_ls_dir)
            logger.log("[MQL4 LSP] Download completed", logging.INFO)
        except Exception as e:
            logger.log(f"[MQL4 LSP] Download failed: {e}", logging.ERROR)

            # Fallback to system binary if download fails
            logger.log("[MQL4 LSP] Attempting fallback to system binary...", logging.WARNING)
            system_ls = shutil.which("mql4-lsp-server")
            if system_ls:
                logger.log(f"[MQL4 LSP] Using system binary at: {system_ls}", logging.INFO)
                return system_ls

            raise FileNotFoundError(
                "Failed to download MQL4 LSP and no system binary available.\n"
                + f"Download URL: {dep.url}\n"
                + "Please ensure you have internet connectivity or install the binary manually."
            )

        # Step 4: Verify binary exists after download
        if not os.path.exists(mql4_ls_executable_path):
            logger.log(f"[MQL4 LSP] ERROR: Binary not found after download at {mql4_ls_executable_path}", logging.ERROR)
            system_ls = shutil.which("mql4-lsp-server")
            if system_ls:
                logger.log(f"[MQL4 LSP] Falling back to system binary: {system_ls}", logging.WARNING)
                return system_ls
            raise FileNotFoundError(
                f"MQL4 LSP executable not found at {mql4_ls_executable_path}.\n"
                + "Download may have failed. Please try again or visit: https://github.com/davalillo/mql4-language-server-releases/releases"
            )

        # Step 5: Verify SHA256 checksum if available
        if dep.binary_name in checksums:
            expected_hash = checksums[dep.binary_name]
            logger.log("[MQL4 LSP] Verifying SHA256 checksum...", logging.INFO)
            try:
                with open(mql4_ls_executable_path, "rb") as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                logger.log(f"[MQL4 LSP] Actual SHA256:   {actual_hash[:16]}...", logging.DEBUG)
                if actual_hash == expected_hash:
                    logger.log("[MQL4 LSP] SHA256 verification PASSED", logging.INFO)
                else:
                    logger.log("[MQL4 LSP] SHA256 verification FAILED!", logging.ERROR)
                    logger.log(f"[MQL4 LSP] Expected: {expected_hash}", logging.ERROR)
                    logger.log(f"[MQL4 LSP] Actual:   {actual_hash}", logging.ERROR)
                    # Remove corrupted file
                    os.remove(mql4_ls_executable_path)
                    raise RuntimeError("SHA256 checksum verification failed. Binary may be corrupted.")
            except Exception as e:
                logger.log(f"[MQL4 LSP] Error verifying checksum: {e}", logging.ERROR)
                # Continue anyway - checksum verification is optional
        else:
            logger.log("[MQL4 LSP] No checksum available, skipping verification", logging.WARNING)

        # Step 6: Set executable permissions and return
        return cls._verify_and_set_executable(mql4_ls_executable_path, logger)

    @staticmethod
    def _verify_and_set_executable(executable_path: str, logger: LanguageServerLogger) -> str:
        """
        Verify the executable exists and has correct permissions, then return the path.
        """
        if not os.path.exists(executable_path):
            raise FileNotFoundError(f"Executable not found at {executable_path}")

        # Make executable on Unix-like systems
        if os.name != "nt":
            os.chmod(executable_path, 0o755)
            logger.log(f"[MQL4 LSP] Set executable permissions on {executable_path}", logging.DEBUG)

        logger.log(f"[MQL4 LSP] Language Server ready at {executable_path}", logging.INFO)
        return executable_path

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> dict[str, Any]:
        """
        Returns the initialize params for the MQL4 Language Server.
        """
        root_uri = pathlib.Path(repository_absolute_path).as_uri()
        initialize_params: dict[str, Any] = {
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

    def _start_server(self) -> None:
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
        from typing import cast

        def register_capability_handler(params: dict[str, Any]) -> None:
            assert "registrations" in params
            for registration in params["registrations"]:
                if registration["method"] == "workspace/executeCommand":
                    # Handle custom commands if needed
                    pass

        def lang_status_handler(params: dict[str, Any]) -> None:
            # Handle language server status notifications
            if params.get("type") == "ServiceReady" and params.get("message") == "ServiceReady":
                self.service_ready_event.set()

        def execute_client_command_handler(params: dict[str, Any]) -> list[Any]:
            return []

        def do_nothing(params: dict[str, Any]) -> None:
            return

        def check_experimental_status(params: dict[str, Any]) -> None:
            # The server is ready when it reports quiescent status
            if params.get("quiescent") == True:
                self.server_ready.set()

        def window_log_message(msg: dict[str, Any]) -> None:
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
        init_response = self.server.send.initialize(cast(InitializeParams, initialize_params))

        # Verify basic capabilities
        assert "capabilities" in init_response
        capabilities: dict[str, Any] = cast(dict[str, Any], init_response["capabilities"])

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
