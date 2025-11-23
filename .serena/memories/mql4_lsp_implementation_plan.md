# Plan Detallado: Añadir Soporte LSP para MQL4 en Serena

## Resumen Ejecutivo

Este documento detalla los pasos necesarios para añadir soporte completo del Language Server Protocol (LSP) para el lenguaje MQL4 en el proyecto Serena. El plan incluye la creación de un nuevo servidor de lenguaje, configuración de tests, integración con el sistema de build, y documentación.

## 1. Análisis Previo

### 1.1 Estado Actual del Proyecto
- **Lenguajes soportados**: 36+ lenguajes (Python, Java, Go, PHP, etc.)
- **Arquitectura**: Dual-layer con `SolidLanguageServer` como wrapper LSP unificado
- **Patrón de implementación**: Cada lenguaje tiene:
  - Implementación de servidor en `src/solidlsp/language_servers/`
  - Registro en `Language` enum en `ls_config.py`
  - Test suite en `test/solidlsp/<lenguaje>/`
  - Repositorio de prueba en `test/resources/repos/<lenguaje>/`

### 1.2 Consideraciones para MQL4
- **Tipo de lenguaje**: Lenguaje de scripting para MetaTrader 4 (trading financiero)
- **Características**: Similar a C/C++, con extensiones específicas para trading
- **Archivos típicos**: `.mq4`, `.mqh` (headers)
- **Servidor LSP**: **NO existe** un servidor LSP nativo para MQL4
- **Enfoque recomendado**: Utilizar un servidor genérico basado en tree-sitter o clangd con configuración personalizada

## 2. Pasos de Implementación

### Paso 1: Crear el Servidor de Lenguaje MQL4

#### 2.1 Archivo: `src/solidlsp/language_servers/mql4_language_server.py`

**Crear la clase `Mql4LanguageServer`** (basada en el patrón de `BashLanguageServer` o `ClangdLanguageServer` para lenguajes sin LSP nativo):

```python
"""
Provides MQL4 specific instantiation of the LanguageServer class.
"""

import logging
import os
import shutil
from pathlib import Path

from overrides import override

from solidlsp.ls import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig
from solidlsp.ls_logger import LanguageServerLogger
from solidlsp.lsp_protocol_handler.lsp_types import InitializeParams
from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
from solidlsp.settings import SolidLSPSettings


class Mql4LanguageServer(SolidLanguageServer):
    """
    Provides MQL4 specific instantiation of the LanguageServer class.
    Uses clangd with MQL4-specific configuration.
    """
    
    @override
    def is_ignored_dirname(self, dirname: str) -> bool:
        """Define MQL4-specific directories to ignore."""
        return super().is_ignored_dirname(dirname) or dirname in [
            "logs",           # Log files
            "MQL4/Logs",      # Standard MT4 log directory
            "temp",           # Temporary files
            "backup",         # Backup files
        ]

    def __init__(
        self,
        config: LanguageServerConfig,
        logger: LanguageServerLogger,
        repository_root_path: str,
        solidlsp_settings: SolidLSPSettings,
    ):
        # Setup clangd with MQL4 configuration
        clangd_cmd = self._setup_mql4_server(logger, solidlsp_settings)
        
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=clangd_cmd, cwd=repository_root_path),
            "mql4",
            solidlsp_settings,
        )

    def _setup_mql4_server(self, logger: LanguageServerLogger, solidlsp_settings: SolidLSPSettings) -> list[str]:
        """
        Setup clangd with MQL4-specific configuration.
        MQL4 doesn't have a native LSP, so we use clangd with a custom compile_commands.json.
        """
        # Check if clangd is installed
        clangd_path = shutil.which("clangd")
        if not clangd_path:
            raise RuntimeError(
                "clangd is not installed or not in PATH. "
                "MQL4 support requires clangd for C/C++-like syntax analysis. "
                "Please install clangd and try again."
            )
        
        # MQL4 configuration flags
        mql4_flags = [
            "-std=c++11",      # MQL4 is C++-like
            "-DNDEBUG",        # Disable assertions
            "-DMT4_COMPILE",   # MQL4-specific define
        ]
        
        return [clangd_path, "--stdio"] + mql4_flags

    @staticmethod
    def _get_initialize_params(repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for MQL4 language server.
        """
        root_uri = Path(repository_absolute_path).as_uri()
        initialize_params = {
            "processId": os.getpid(),
            "rootPath": repository_absolute_path,
            "rootUri": root_uri,
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "documentSymbol": {
                        "dynamicRegistration": True,
                        "hierarchicalDocumentSymbolSupport": True,
                    },
                    "completion": {"dynamicRegistration": True},
                    "hover": {"dynamicRegistration": True},
                },
                "workspace": {
                    "workspaceFolders": True,
                },
            },
        }
        return initialize_params

    def _start_server(self):
        """
        Start the clangd server with MQL4-specific handlers.
        """
        def do_nothing(params):
            return

        def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("$/progress", do_nothing)

        self.logger.log("Starting clangd server for MQL4", logging.INFO)
        self.server.start()
        
        initialize_params = self._get_initialize_params(self.repository_root_path)
        init_response = self.server.send.initialize(initialize_params)
        
        self.server.notify.initialized({})
        self.completions_available.set()
```

**Consideraciones importantes**:
- MQL4 no tiene un LSP nativo, por lo que usamos **clangd** con configuración personalizada
- Clangd puede analizar la sintaxis C/C++-like de MQL4
- Se necesitan flags específicos para el dialecto MQL4

### Paso 2: Registrar MQL4 en el Sistema

#### 2.1 Modificar: `src/solidlsp/ls_config.py`

**Añadir a la clase `Language` enum**:

```python
class Language(str, Enum):
    # ... existing languages ...
    MQL4 = "mql4"
    
    def get_source_fn_matcher(self) -> FilenameMatcher:
        match self:
            # ... existing cases ...
            case self.MQL4:
                return FilenameMatcher("*.mq4", "*.mqh")  # .mqh for MQL4 header files
```

**Añadir método `get_ls_class()`**:

```python
    def get_ls_class(self) -> type["SolidLanguageServer"]:
        match self:
            # ... existing cases ...
            case self.MQL4:
                from solidlsp.language_servers.mql4_language_server import Mql4LanguageServer
                return Mql4LanguageServer
```

### Paso 3: Crear Repositorio de Prueba

#### 3.1 Directorio: `test/resources/repos/mql4/test_repo/`

**Estructura de archivos**:
```
test/resources/repos/mql4/test_repo/
├── ExpertAdvisor.mq4         # EA principal
├── Include/
│   └── CustomIndicators.mqh  # Header con indicadores
├── Indicators/
│   └── MyIndicator.mq4       # Indicador personalizado
├── Scripts/
│   └── TradeManager.mq4      # Script de trading
└── .gitignore                # Ignorar archivos compilados
```

**Ejemplo: ExpertAdvisor.mq4**

```mql4
//+------------------------------------------------------------------+
//|                                                     Expert.mq4 |
//|                                  Copyright 2024, Serena Project |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Serena Project"
#property link      ""
#property version   "1.00"
#property strict

// Include custom indicators
#include <CustomIndicators.mqh>

// Input parameters
input double LotSize = 0.1;
input int StopLoss = 50;
input int TakeProfit = 100;

// Global variables
int maHandle;
double maBuffer[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize Moving Average indicator
    maHandle = iMA(Symbol(), PERIOD_H1, 20, 0, MODE_SMA, PRICE_CLOSE);
    
    if(maHandle == INVALID_HANDLE)
    {
        Print("Error creating MA indicator");
        return INIT_FAILED;
    }
    
    Print("Expert Advisor initialized successfully");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release indicator handle
    if(maHandle != INVALID_HANDLE)
        IndicatorRelease(maHandle);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if we have enough data
    if(Bars < 20)
        return;
    
    // Get MA value
    if(CopyBuffer(maHandle, 0, 0, 3, maBuffer) < 0)
        return;
    
    // Trading logic
    if(maBuffer[0] > maBuffer[1] && maBuffer[1] <= maBuffer[2])
    {
        // Buy signal
        OpenPosition(OP_BUY);
    }
    else if(maBuffer[0] < maBuffer[1] && maBuffer[1] >= maBuffer[2])
    {
        // Sell signal
        OpenPosition(OP_SELL);
    }
}

//+------------------------------------------------------------------+
//| Open position function                                           |
//+------------------------------------------------------------------+
void OpenPosition(int orderType)
{
    double price, sl, tp;
    int ticket;
    
    if(orderType == OP_BUY)
    {
        price = Ask;
        sl = (StopLoss > 0) ? price - StopLoss * Point : 0;
        tp = (TakeProfit > 0) ? price + TakeProfit * Point : 0;
    }
    else
    {
        price = Bid;
        sl = (StopLoss > 0) ? price + StopLoss * Point : 0;
        tp = (TakeProfit > 0) ? price - TakeProfit * Point : 0;
    }
    
    ticket = OrderSend(Symbol(), orderType, LotSize, price, 3, sl, tp, "Trade", 0, 0, clrNONE);
    
    if(ticket < 0)
    {
        Print("Error opening position: ", GetLastError());
    }
    else
    {
        Print("Position opened successfully, ticket: ", ticket);
    }
}
```

**Ejemplo: CustomIndicators.mqh**

```mql4
//+------------------------------------------------------------------+
//|                                             CustomIndicators.mqh |
//|                                  Copyright 2024, Serena Project |
//+------------------------------------------------------------------+

//--- Custom indicator buffers
double RSIBuffer[];

//+------------------------------------------------------------------+
//| Calculate RSI                                                    |
//+------------------------------------------------------------------+
double CalculateRSI(int period, int shift)
{
    double gain = 0, loss = 0;
    
    for(int i = 1; i <= period; i++)
    {
        double change = Close[shift + i - 1] - Close[shift + i];
        if(change > 0)
            gain += change;
        else
            loss += MathAbs(change);
    }
    
    if(loss == 0)
        return 100;
    
    double rs = gain / loss;
    return 100 - (100 / (1 + rs));
}
```

### Paso 4: Crear Test Suite

#### 4.1 Archivo: `test/solidlsp/mql4/test_mql4_basic.py`

```python
"""
Tests for MQL4 language server functionality.
"""

from pathlib import Path

import pytest

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import Language


@pytest.mark.mql4
class TestMql4LanguageServer:
    """Test suite for MQL4 language server."""
    
    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_ls_is_running(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test that the MQL4 language server starts and stops successfully."""
        assert language_server.is_running()
        assert Path(language_server.language_server.repository_root_path).resolve() == repo_path.resolve()

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_find_definition_within_file(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test finding definition of a function within the same file."""
        # In ExpertAdvisor.mq4:
        # Line 45: void OnTick() - function definition
        # Line 65: OpenPosition() - function call
        # Find definition of OpenPosition() from its call
        
        file_path = str(repo_path / "ExpertAdvisor.mq4")
        # OnTick() calls OpenPosition() - find its definition
        # Line 65 (0-indexed: line 64), looking for "OpenPosition"
        definition_locations = language_server.request_definition(file_path, 64, 10)  # cursor on 'O' in OpenPosition
        
        assert definition_locations, f"Expected non-empty definition_locations but got {definition_locations=}"
        assert len(definition_locations) == 1
        definition_location = definition_locations[0]
        assert definition_location["uri"].endswith("ExpertAdvisor.mq4")
        # OpenPosition is defined on line 70 (0-indexed: line 69)
        assert definition_location["range"]["start"]["line"] == 69
        assert definition_location["range"]["start"]["character"] == 0

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_find_definition_across_files(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test finding definition of a function across files."""
        # In ExpertAdvisor.mq4 line 12: #include <CustomIndicators.mqh>
        # Uses CalculateRSI function from the header file
        file_path = str(repo_path / "ExpertAdvisor.mq4")
        # We need to call CalculateRSI from the header (this is conceptual - the LSP should find it)
        definition_locations = language_server.request_definition(
            str(repo_path / "Include" / "CustomIndicators.mqh"), 15, 10
        )
        
        assert definition_locations, f"Expected non-empty definition_locations but got {definition_locations=}"
        # Verify that the function is found in the header file
        assert any("CustomIndicators.mqh" in loc["uri"] for loc in definition_locations)

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_find_references_within_file(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test finding references within the same file."""
        file_path = str(repo_path / "ExpertAdvisor.mq4")
        # Find references to OnInit function (defined on line 26)
        references = language_server.request_references(file_path, 26, 5)  # cursor on 'O' in OnInit
        
        assert references, f"Expected non-empty references but got {references=}"
        # OnInit should be referenced at least once (in the definition itself or in MA handle)
        assert len(references) >= 1

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_find_global_variables(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test finding global variables."""
        file_path = str(repo_path / "ExpertAdvisor.mq4")
        # Look for global variable 'maHandle' (defined on line 21)
        symbols = language_server.request_document_overview(file_path)
        
        assert symbols, "Expected to find symbols in the file"
        
        # Find maHandle in the symbols
        ma_handle_symbol = None
        for symbol in symbols:
            if symbol["name"] == "maHandle":
                ma_handle_symbol = symbol
                break
        
        assert ma_handle_symbol is not None, "Expected to find 'maHandle' variable"

    @pytest.mark.parametrize("language_server", [Language.MQL4], indirect=True)
    @pytest.mark.parametrize("repo_path", [Language.MQL4], indirect=True)
    def test_document_symbols_structure(self, language_server: SolidLanguageServer, repo_path: Path) -> None:
        """Test that document symbols show proper hierarchical structure."""
        file_path = str(repo_path / "ExpertAdvisor.mq4")
        
        symbols = language_server.request_document_overview(file_path)
        
        assert symbols, "Expected to find symbols in the file"
        
        # Should find: OnInit, OnDeinit, OnTick, OpenPosition functions
        function_names = [s["name"] for s in symbols if s["kind"] == 12]  # Function kind
        
        assert "OnInit" in function_names, "Expected to find OnInit function"
        assert "OnTick" in function_names, "Expected to find OnTick function"
        assert "OpenPosition" in function_names, "Expected to find OpenPosition function"
```

### Paso 5: Configuración de Pytest

#### 5.1 Modificar: `pyproject.toml`

**Añadir marker para MQL4** en la sección `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
markers = [
  # ... existing markers ...
  "mql4: language server running for MQL4 (MetaTrader 4)",
]
```

**Añadir la línea a la configuración de test por defecto** en `[tool.poe.tasks]`:

```toml
[tool.poe.tasks]
test = "pytest test -vv -m \"${PYTEST_MARKERS:-not java and not rust and not erlang and not mql4}\""
```

### Paso 6: Documentación

#### 6.1 Actualizar archivos de documentación:

**README.md**:
- Añadir MQL4 a la lista de lenguajes soportados
- Indicar que usa clangd como backend

**CHANGELOG.md**:
- Documentar la nueva funcionalidad
- Explicar que MQL4 requiere instalación manual de clangd

## 3. Dependencias y Requisitos

### 3.1 Dependencias del Sistema
- **clangd**: Debe instalarse manualmente por el usuario
  - Ubuntu/Debian: `sudo apt-get install clangd`
  - macOS: `brew install llvm`
  - Windows: Instalar LLVM con clangd

### 3.2 Dependencias de Python
- No se requieren nuevas dependencias de Python
- MQL4 usa el mismo stack LSP que C/C++

## 4. Consideraciones Especiales

### 4.1 Limitaciones del Enfoque
1. **Sin LSP nativo**: MQL4 no tiene un servidor LSP dedicado, por lo que dependemos de clangd
2. **Configuración limitada**: Algunas características específicas de MQL4 podrían no ser reconocidas
3. **Análisis sintáctico**: Clangd entiende la sintaxis C++ pero no las funciones específicas de MQL4

### 4.2 Soluciones Propuestas
1. **Configuración personalizada**: Usar `compile_commands.json` con flags específicos para MQL4
2. **Headers personalizados**: Proporcionar headers con declaraciones de funciones MQL4
3. **Directivas de preprocesador**: Usar defines para simular el entorno MQL4

### 4.3 Archivos de Configuración Adicionales

**compile_commands.json** (opcional, para análisis avanzado):

```json
[
  {
    "directory": "/path/to/mql4/project",
    "command": "clang++ -std=c++11 -DNDEBUG -DMT4_COMPILE -I/path/to/mql4/include -c file.mq4",
    "file": "file.mq4"
  }
]
```

## 5. Estructura de Archivos Final

```
/home/guillermo/source/serena-mql4/
├── src/solidlsp/
│   ├── language_servers/
│   │   └── mql4_language_server.py          [NUEVO]
│   └── ls_config.py                         [MODIFICAR]
│
├── test/
│   ├── solidlsp/
│   │   └── mql4/
│   │       └── test_mql4_basic.py           [NUEVO]
│   └── resources/
│       └── repos/
│           └── mql4/
│               └── test_repo/               [NUEVO]
│                   ├── ExpertAdvisor.mq4
│                   ├── Include/
│                   │   └── CustomIndicators.mqh
│                   ├── Indicators/
│                   │   └── MyIndicator.mq4
│                   ├── Scripts/
│                   │   └── TradeManager.mq4
│                   └── .gitignore
│
└── pyproject.toml                           [MODIFICAR]
```

## 6. Testing y Validación

### 6.1 Comandos de Test

```bash
# Ejecutar tests específicos de MQL4
uv run poe test -m mql4

# Ejecutar todos los tests (incluye MQL4)
uv run poe test -m "mql4 or python or go"

# Validar formato
uv run poe format

# Verificar tipos
uv run poe type-check
```

### 6.2 Criterios de Aceptación
- [ ] El servidor MQL4 se inicia correctamente
- [ ] Puede encontrar definiciones dentro de un archivo
- [ ] Puede encontrar definiciones entre archivos
- [ ] Puede encontrar referencias a símbolos
- [ ] Los símbolos globales son detectados
- [ ] La estructura jerárquica de símbolos es correcta
- [ ] Los tests pasan en CI/CD

## 7. Lista de Verificación

### 7.1 Implementación Core
- [ ] Crear `mql4_language_server.py`
- [ ] Registrar MQL4 en `ls_config.py`
- [ ] Implementar método `_get_initialize_params()`
- [ ] Configurar directorios ignorados

### 7.2 Testing
- [ ] Crear repositorio de prueba
- [ ] Implementar tests básicos
- [ ] Añadir marker en `pyproject.toml`
- [ ] Validar que todos los tests pasen

### 7.3 Documentación
- [ ] Actualizar README.md
- [ ] Actualizar CHANGELOG.md
- [ ] Añadir comentarios en el código
- [ ] Crear guía de instalación para clangd

### 7.4 CI/CD
- [ ] Verificar que los tests se ejecuten en CI
- [ ] Validar que no se rompan tests existentes
- [ ] Comprobar el reporte de cobertura

## 8. Próximos Pasos Recomendados

1. **Implementación inicial**: Crear la implementación básica siguiendo los pasos 1-2
2. **Testing**: Crear el repositorio de test y escribir tests (pasos 3-4)
3. **Integración**: Añadir a pyproject.toml y validar (paso 5)
4. **Documentación**: Escribir documentación completa (paso 6)
5. **Refinamiento**: Ajustar basado en resultados de testing
6. **Optimización**: Mejorar soporte para características específicas de MQL4

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| clangd no está disponible | Alto | Documentar instalación en README, mostrar error claro |
| Análisis limitado de MQL4 | Medio | Usar configuración personalizada, proporcionar headers |
| Rendimiento con proyectos grandes | Bajo | Implementar ignore paths para directorios específicos |
| Compatibilidad con CI | Bajo | Hacer tests condicionales, permitir skip en algunos OS |

## 10. Conclusión

Este plan proporciona una hoja de ruta completa para añadir soporte MQL4 a Serena. El enfoque utiliza clangd como backend, lo cual es una solución práctica dado que no existe un LSP nativo para MQL4. La implementación seguirá los patrones establecidos del proyecto y mantendrá la consistencia con otros lenguajes soportados.

**Tiempo estimado de implementación**: 2-3 días
**Complejidad**: Media
**Beneficio**: Alto (MQL4 es ampliamente usado en trading financiero)

---

*Documento creado como parte del análisis del proyecto Serena para añadir soporte MQL4*