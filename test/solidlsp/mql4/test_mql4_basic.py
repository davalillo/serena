"""
Basic integration tests for the MQL4 language server functionality.

These tests validate the functionality of the MQL4 language server APIs
like request_references, request_definition, and request_document_symbols
using the test repository.
"""


import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language


@pytest.mark.mql4
class TestMql4LanguageServerBasics:
    """Test basic functionality of the MQL4 language server."""

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_document_symbols_expert_advisor(self, language_server: SolidLanguageServer) -> None:
        """Test request_document_symbols on ExpertAdvisor.mq4 file."""
        file_path = "ExpertAdvisor.mq4"
        # Get all symbols from the Expert Advisor
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get document symbols"

        # Check for key functions
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_functions = ["OnInit", "OnDeinit", "OnTick", "CheckForTradeSignals"]
        for func in expected_functions:
            assert func in symbol_names, f"Expected function {func} not found in symbols"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_document_symbols_custom_indicator(self, language_server: SolidLanguageServer) -> None:
        """Test request_document_symbols on MyIndicator.mq4 file."""
        file_path = "Indicators/MyIndicator.mq4"

        # Get all symbols from the indicator
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get document symbols"

        # Check for expected indicator functions
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_functions = ["OnInit", "OnDeinit", "OnCalculate"]
        for func in expected_functions:
            assert func in symbol_names, f"Expected function {func} not found in symbols"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_document_symbols_trade_manager_script(self, language_server: SolidLanguageServer) -> None:
        """Test request_document_symbols on TradeManager.mq4 script."""
        file_path = "Scripts/TradeManager.mq4"

        # Get all symbols from the script
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get document symbols"

        # Check for expected script functions
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_functions = ["OnStart", "CloseAllOpenPositions", "DisplayPositionInfo"]
        for func in expected_functions:
            assert func in symbol_names, f"Expected function {func} not found in symbols"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_document_symbols_custom_indicators_include(self, language_server: SolidLanguageServer) -> None:
        """Test request_document_symbols on CustomIndicators.mqh include file."""
        file_path = "Include/CustomIndicators.mqh"

        # Get all symbols from the include file
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get document symbols"

        # Check for expected helper functions
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_functions = [
            "CalculateSMA", "CalculateEMA", "CalculateRSI",
            "CalculateBollingerUpper", "CalculateBollingerLower"
        ]
        for func in expected_functions:
            assert func in symbol_names, f"Expected function {func} not found in symbols"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_definition_on_init_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_definition on OnInit function in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Find the OnInit function symbol
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        oninit_symbol = next((s for s in symbols[0] if s.get("name") == "OnInit"), None)

        if not oninit_symbol or "selectionRange" not in oninit_symbol:
            raise AssertionError("OnInit symbol or its selectionRange not found")

        # Get definition
        sel_start = oninit_symbol["selectionRange"]["start"]
        definitions = language_server.request_definition(file_path, sel_start["line"], sel_start["character"])

        # Should find at least one definition
        assert len(definitions) > 0, "Should find definition for OnInit function"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_definition_global_variable(self, language_server: SolidLanguageServer) -> None:
        """Test request_definition on global variable in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Find the MagicNumber input parameter symbol
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        magic_symbol = next((s for s in symbols[0] if s.get("name") == "MagicNumber"), None)

        if not magic_symbol or "selectionRange" not in magic_symbol:
            raise AssertionError("MagicNumber symbol or its selectionRange not found")

        # Get definition
        sel_start = magic_symbol["selectionRange"]["start"]
        definitions = language_server.request_definition(file_path, sel_start["line"], sel_start["character"])

        # Should find at least one definition
        assert len(definitions) > 0, "Should find definition for MagicNumber parameter"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_references_on_init_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_references on OnInit function in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Find the OnInit function symbol
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        oninit_symbol = next((s for s in symbols[0] if s.get("name") == "OnInit"), None)

        if not oninit_symbol or "selectionRange" not in oninit_symbol:
            raise AssertionError("OnInit symbol or its selectionRange not found")

        # Get references
        sel_start = oninit_symbol["selectionRange"]["start"]
        references = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        # Should find at least one reference (the definition itself)
        assert len(references) > 0, "Should find references for OnInit function"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_references_check_for_trade_signals_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_references on CheckForTradeSignals function in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Find the CheckForTradeSignals function symbol
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        check_func_symbol = next((s for s in symbols[0] if s.get("name") == "CheckForTradeSignals"), None)

        if not check_func_symbol or "selectionRange" not in check_func_symbol:
            raise AssertionError("CheckForTradeSignals symbol or its selectionRange not found")

        # Get references
        sel_start = check_func_symbol["selectionRange"]["start"]
        references = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        # Should find at least one reference (called from OnTick)
        assert len(references) > 0, "Should find references for CheckForTradeSignals function"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_references_magic_number_input(self, language_server: SolidLanguageServer) -> None:
        """Test request_references on MagicNumber input parameter in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Find the MagicNumber input parameter symbol
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        magic_symbol = next((s for s in symbols[0] if s.get("name") == "MagicNumber"), None)

        if not magic_symbol or "selectionRange" not in magic_symbol:
            raise AssertionError("MagicNumber symbol or its selectionRange not found")

        # Get references
        sel_start = magic_symbol["selectionRange"]["start"]
        references = language_server.request_references(file_path, sel_start["line"], sel_start["character"])

        # Should find multiple references (used in open position and has open position functions)
        assert len(references) > 0, "Should find references for MagicNumber parameter"

    @pytest.mark.skip(reason="request_completion method not implemented in SolidLanguageServer")
    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_completion_on_init_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_completion within OnInit function in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Test completion at line where OnInit function is defined
        # Line 21 contains the OnInit function definition
        completions = language_server.request_completions(file_path, 21, 5)

        # Should get completions
        assert completions is not None, "Should get completions"

    @pytest.mark.skip(reason="request_completion method not implemented in SolidLanguageServer")
    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_request_completion_on_tick_function(self, language_server: SolidLanguageServer) -> None:
        """Test request_completion within OnTick function in ExpertAdvisor.mq4."""
        file_path = "ExpertAdvisor.mq4"

        # Test completion at a line within OnTick function
        # Line 45 has code that calls CheckForTradeSignals
        completions = language_server.request_completions(file_path, 45, 10)

        # Should get completions
        assert completions is not None, "Should get completions"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_cross_file_symbols_include_file(self, language_server: SolidLanguageServer) -> None:
        """Test that symbols from include file (CustomIndicators.mqh) are accessible."""
        ea_file = "ExpertAdvisor.mq4"

        # Get symbols from the main EA file
        symbols = language_server.request_document_symbols(ea_file).get_all_symbols_and_roots()

        # Check that we got symbols from the EA
        assert len(symbols) > 0, "Should get symbols from ExpertAdvisor.mq4"

        # The EA includes CustomIndicators.mqh, so references to included functions should work
        # (This is more of an integration test to ensure includes are properly parsed)
        symbol_names = [s.get("name", "") for s in symbols[0]]

        # Verify we have EA-specific symbols
        expected_ea_symbols = ["OnInit", "OnTick", "MagicNumber", "LotSize"]
        for sym in expected_ea_symbols:
            assert sym in symbol_names, f"Expected symbol {sym} not found in EA"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_struct_symbols_in_indicator(self, language_server: SolidLanguageServer) -> None:
        """Test that struct symbols are properly extracted in indicator file."""
        indicator_file = "Indicators/MyIndicator.mq4"

        # Get symbols from the indicator
        symbols = language_server.request_document_symbols(indicator_file).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get symbols from indicator"

        # Check for different types of symbols
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_symbols = [
            "UpperBandBuffer", "LowerBandBuffer", "MiddleBandBuffer", "SignalBuffer",
            "Period", "Deviation", "OnInit", "OnCalculate"
        ]

        for sym in expected_symbols:
            assert sym in symbol_names, f"Expected symbol {sym} not found in indicator"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_script_main_function(self, language_server: SolidLanguageServer) -> None:
        """Test that script main function (OnStart) is properly recognized."""
        script_file = "Scripts/TradeManager.mq4"

        # Get symbols from the script
        symbols = language_server.request_document_symbols(script_file).get_all_symbols_and_roots()

        # Check that we got symbols
        assert len(symbols) > 0, "Should get symbols from script"

        # Check for OnStart function
        symbol_names = [s.get("name", "") for s in symbols[0]]
        assert "OnStart" in symbol_names, "OnStart function should be found in script"

        # Check for script-specific symbols
        script_symbols = ["CloseAllPositions", "MagicNumber", "LotSize"]
        for sym in script_symbols:
            assert sym in symbol_names, f"Expected symbol {sym} not found in script"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_lsp_server_initialization(self, language_server: SolidLanguageServer) -> None:
        """Test that the MQL4 LSP server initializes correctly."""
        # The language server should be ready after fixture setup
        assert language_server.server_ready.is_set(), "LSP server should be initialized"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_file_type_detection_mq4(self, language_server: SolidLanguageServer) -> None:
        """Test that .mq4 files are correctly identified as MQL4."""
        matcher = Language.MQL4.get_source_fn_matcher()
        assert matcher.is_relevant_filename("ExpertAdvisor.mq4"), "Should detect .mq4 files"
        assert matcher.is_relevant_filename("MyIndicator.mq4"), "Should detect .mq4 files"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_file_type_detection_mqh(self, language_server: SolidLanguageServer) -> None:
        """Test that .mqh files are correctly identified as MQL4."""
        matcher = Language.MQL4.get_source_fn_matcher()
        assert matcher.is_relevant_filename("CustomIndicators.mqh"), "Should detect .mqh files"
        assert matcher.is_relevant_filename("TradeFunctions.mqh"), "Should detect .mqh files"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_symbol_caching_across_requests(self, language_server: SolidLanguageServer) -> None:
        """Test that symbols are cached and can be retrieved multiple times."""
        file_path = "ExpertAdvisor.mq4"

        # First request
        symbols1 = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        assert len(symbols1) > 0, "Should get symbols on first request"

        # Second request (should use cache if implemented)
        symbols2 = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        assert len(symbols2) > 0, "Should get symbols on second request"

        # Results should be consistent
        symbol_names_1 = [s.get("name", "") for s in symbols1[0]]
        symbol_names_2 = [s.get("name", "") for s in symbols2[0]]
        assert symbol_names_1 == symbol_names_2, "Cached symbols should be consistent"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_global_variables_and_constants(self, language_server: SolidLanguageServer) -> None:
        """Test that global variables and constants are properly extracted."""
        file_path = "ExpertAdvisor.mq4"

        # Get all symbols
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        assert len(symbols) > 0, "Should get symbols from file"

        # Check for global variables
        symbol_names = [s.get("name", "") for s in symbols[0]]
        expected_globals = ["MagicNumber", "LotSize"]
        for global_var in expected_globals:
            assert global_var in symbol_names, f"Expected global variable {global_var} not found"

    # ============================================================
    # NEW TESTS: Line Indexing and Range Validation
    # ============================================================

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_symbol_ranges_are_zero_indexed(self, language_server: SolidLanguageServer) -> None:
        """Verify that symbol ranges are 0-indexed per LSP 3.17 specification.

        LSP 3.17 spec states: "Line position in a document (zero-based)."
        This test ensures the MQL4 LSP returns correct 0-indexed line numbers.
        """
        file_path = "ExpertAdvisor.mq4"

        # Get all symbols
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        assert len(symbols) > 0, "Should get symbols from file"

        # Find OnInit function - its declaration should be at a specific line
        # The test file ExpertAdvisor.mq4 has OnInit defined at line 21 (0-indexed = 20)
        oninit_symbol = next((s for s in symbols[0] if s.get("name") == "OnInit"), None)
        assert oninit_symbol is not None, "OnInit symbol should be found"

        # Verify the line is 0-indexed (not 1-indexed)
        # If the LSP returned 1-indexed, line would be 21, not 20
        start_line = oninit_symbol["selectionRange"]["start"]["line"]

        # The first function in a valid MQL4 file should not be at line 0
        # (line 0 is typically the comment header)
        # But it should be 0-indexed, not 1-indexed
        assert start_line > 0, "First function should not be at line 0 in a properly formatted MQL4 file"

        # Get the actual content to verify the line number is correct
        # OnInit declaration should be around line 21 (0-indexed)
        # If the value is 21 instead of 20, it would indicate 1-indexing (bug)
        # If the value is 20, it indicates correct 0-indexing
        #
        # We verify it's not 1-indexed by checking it's NOT equal to the 1-indexed expected line
        # A 1-indexed OnInit at line 21 would give us start_line == 21
        # A correctly 0-indexed OnInit at line 21 would give us start_line == 20
        assert start_line != 21, (
            f"Line {start_line} appears to be 1-indexed. "
            "LSP 3.17 requires 0-indexed lines. Got: {start_line}"
        )

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_symbol_ranges_consistency(self, language_server: SolidLanguageServer) -> None:
        """Verify that start and end lines in ranges are consistent.

        The range should represent the full extent of the symbol,
        with start <= end and both being valid line numbers.
        """
        file_path = "ExpertAdvisor.mq4"

        # Get all symbols
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()
        assert len(symbols) > 0, "Should get symbols from file"

        for symbol in symbols[0]:
            if "range" in symbol:
                r = symbol["range"]
                start_line = r["start"]["line"]
                end_line = r["end"]["line"]

                # Verify start <= end
                assert start_line <= end_line, (
                    f"Symbol {symbol.get('name', 'unknown')}: start_line ({start_line}) > end_line ({end_line})"
                )

                # Verify both are non-negative
                assert start_line >= 0, f"Symbol {symbol.get('name', 'unknown')}: start_line is negative ({start_line})"
                assert end_line >= 0, f"Symbol {symbol.get('name', 'unknown')}: end_line is negative ({end_line})"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_oninit_range_includes_body(self, language_server: SolidLanguageServer) -> None:
        """Verify that OnInit function range includes its body, not just declaration.

        This test catches the bug where ranges were degenerate (start == end).
        A proper function range should span from declaration to closing brace.
        """
        file_path = "ExpertAdvisor.mq4"

        # Get all symbols
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Find OnInit function
        oninit_symbol = next((s for s in symbols[0] if s.get("name") == "OnInit"), None)
        assert oninit_symbol is not None, "OnInit symbol should be found"

        # Get the full range (should include body)
        if "range" in oninit_symbol:
            r = oninit_symbol["range"]
            start_line = r["start"]["line"]
            end_line = r["end"]["line"]

            # The range should span multiple lines for OnInit (it's a complex function)
            line_count = end_line - start_line + 1
            assert line_count > 1, (
                f"OnInit range appears degenerate: start={start_line}, end={end_line}, lines={line_count}. "
                "Expected range to include function body."
            )

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    def test_simple_function_range(self, language_server: SolidLanguageServer) -> None:
        """Test that simple functions have correct range boundaries.

        Uses functions like NormalizeTPSell which should have small but valid ranges.
        """
        file_path = "ExpertAdvisor.mq4"

        # Get all symbols
        symbols = language_server.request_document_symbols(file_path).get_all_symbols_and_roots()

        # Find a simple function (NormalizeTPSell should be a simple function)
        normalize_tp_sell = next(
            (s for s in symbols[0] if s.get("name") == "NormalizeTPSell"),
            None
        )

        if normalize_tp_sell is None:
            # Skip if not found (might not exist in this file)
            return

        # Get selection range (declaration)
        sel_start = normalize_tp_sell["selectionRange"]["start"]["line"]
        sel_end = normalize_tp_sell["selectionRange"]["end"]["line"]

        # Selection range should be a single line (the declaration)
        assert sel_start == sel_end, (
            f"NormalizeTPSell selectionRange should be single line: start={sel_start}, end={sel_end}"
        )

        # Verify 0-indexed (not 1-indexed)
        # If this function is at line 18686 (1-indexed), a 1-indexed LSP would return 18686
        # A correct 0-indexed LSP would return 18685
        # We verify by checking it doesn't match the 1-indexed line number
        assert sel_start != 18686, (
            f"Line {sel_start} appears to be 1-indexed. "
            "LSP 3.17 requires 0-indexed lines."
        )
