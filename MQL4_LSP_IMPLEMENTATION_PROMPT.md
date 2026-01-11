# Prompt para Implementar Métodos LSP Faltantes en MQL4 Language Server

## Contexto del Proyecto

Eres un desarrollador experto implementando un Language Server Protocol (LSP) para MQL4 (MetaTrader 4). El servidor está desarrollado en **.NET 8 con ANTLR 4.13.1** para el parsing.

El servidor LSP ya implementa:
- `textDocument/documentSymbol` - ✅ Funcional
- `textDocument/definition` - ✅ Funcional
- `textDocument/references` - ✅ Funcional
- `textDocument/hover` - ✅ Funcional

**Faltan implementar los siguientes métodos LSP** que son requeridos por Serena (herramienta de código para agentes IA):

---

## Especificaciones LSP (LSP 3.17) - Basado en Documentación Oficial

### 1. `workspace/symbol` - Búsqueda de Símbolos en Workspace

**Referencia**: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol

#### Request Parameters
```typescript
interface WorkspaceSymbolParams extends WorkDoneProgressParams, PartialResultParams {
    /**
     * A query string to filter symbols by. Clients may send an empty
     * string here to request all symbols.
     *
     * The query-parameter should be interpreted in a *relaxed way* -
     * match case-insensitive and simply check that the characters of
     * query appear in their order in a candidate symbol.
     */
    query: string;
}
```

#### Response
```typescript
// Opción 1: SymbolInformation (legacy)
interface SymbolInformation {
    name: string;
    kind: SymbolKind;
    location: Location;
    containerName?: string;
}

// Opción 2: WorkspaceSymbol (modern, LSP 3.17+)
interface WorkspaceSymbol {
    name: string;
    kind: SymbolKind;
    location: Location | { uri: DocumentUri };  // Puede ser sin range
    tags?: SymbolTag[];
    containerName?: string;
}
```

#### SymbolKind Valores (1-27)
```typescript
enum SymbolKind {
    File = 1, Module = 2, Namespace = 3, Package = 4,
    Class = 5, Method = 6, Property = 7, Field = 8,
    Constructor = 9, Enum = 10, Interface = 11, Function = 12,
    Variable = 13, Constant = 14, String = 15, Number = 16,
    Boolean = 17, Array = 18, Object = 19, Key = 20,
    Null = 21, EnumMember = 22, Struct = 23, Event = 24,
    Operator = 25, TypeParameter = 26, Unknown = 27
}
```

#### Expected Response Format (lo que espera Serena)
```typescript
// Serena espera este formato exacto en request_workspace_symbol:
response = [
    {
        "name": "OnInit",
        "kind": 12,  // Function
        "location": {
            "uri": "file:///path/to/ExpertAdvisor.mq4",
            "range": {
                "start": { "line": 20, "character": 4 },
                "end": { "line": 20, "character": 10 }
            }
        }
    },
    // ... más símbolos
]
```

#### Requisitos para MQL4
- Indexar todos los archivos `.mq4` y `.mqh` en el workspace
- Buscar: funciones (`OnInit`, `OnTick`, `OnDeinit`, `OnStart`, `OnCalculate`), variables globales, inputs, arrays de buffers
- Búsqueda case-insensitive
- Retornar máximo 50-100 resultados para performance

---

### 2. `textDocument/rename` - Renombrar Símbolos

**Referencia**: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_rename

#### Request Parameters
```typescript
interface RenameParams extends TextDocumentPositionParams, WorkDoneProgressParams {
    /**
     * The new name of the symbol.
     */
    newName: string;
}

interface TextDocumentPositionParams {
    textDocument: TextDocumentIdentifier;
    position: Position;
}

interface Position {
    line: number;        // 0-indexed
    character: number;   // 0-indexed
}
```

#### Response
```typescript
interface WorkspaceEdit {
    /**
     * Holds changes to existing resources.
     * Maps document URIs to array of TextEdits.
     */
    changes?: { [uri: DocumentUri]: TextEdit[]; };

    /**
     * Preferred for versioned edits. Can include file operations.
     */
    documentChanges?: (
        TextDocumentEdit[] |
        (TextDocumentEdit | CreateFile | RenameFile | DeleteFile)[]
    );
}

interface TextDocumentEdit {
    textDocument: {
        uri: DocumentUri;
        version: number | null;  // null para archivos sin versionar
    };
    edits: (TextEdit | AnnotatedTextEdit)[];
}

interface TextEdit {
    range: Range;
    newText: string;
}

interface Range {
    start: Position;
    end: Position;
}
```

#### Expected Response Format (lo que espera Serena)
```typescript
// Serena usa request_rename_symbol_edit() que espera:
{
    "changes": {
        "file:///path/to/ExpertAdvisor.mq4": [
            {
                "range": {
                    "start": { "line": 14, "character": 15 },
                    "end": { "line": 14, "character": 26 }
                },
                "newText": "MagicNumberRenamed"
            }
        ],
        "file:///path/to/Include/CustomIndicators.mqh": [
            {
                "range": { ... },
                "newText": "MagicNumberRenamed"
            }
        ]
    }
}
```

#### Requisitos para MQL4
- Encontrar todas las referencias al símbolo (definición + usos)
- Incluir: definición, llamadas en funciones, referencias en otros archivos
- Validar que el nuevo nombre sea válido (no palabras reservadas)
- Retornar error si el símbolo no puede renombrarse

---

### 3. `textDocument/diagnostic` - Diagnósticos del Documento

**Referencia**: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_diagnostic

#### Request Parameters
```typescript
interface DocumentDiagnosticParams extends WorkDoneProgressParams, PartialResultParams {
    textDocument: TextDocumentIdentifier;
    identifier?: string;           // Opcional, para registro
    previousResultId?: string;     // Para diagnósticos incrementales
}
```

#### Response
```typescript
// LSP 3.17+ usa este formato:
type DocumentDiagnosticReport = 
    | RelatedFullDocumentDiagnosticReport
    | RelatedUnchangedDocumentDiagnosticReport;

interface FullDocumentDiagnosticReport {
    kind: 'full';  // Valor exacto: 'full'
    resultId?: string;  // ID para siguientes requests incrementales
    items: Diagnostic[];
}

interface UnchangedDocumentDiagnosticReport {
    kind: 'unchanged';  // Valor exacto: 'unchanged'
    resultId: string;   // Requerido si kind es 'unchanged'
}

interface Diagnostic {
    range: Range;
    severity?: DiagnosticSeverity;
    code?: number | string;
    source?: string;
    message: string;
    tags?: DiagnosticTag[];
    relatedInformation?: DiagnosticRelatedInformation[];
    data?: any;
}

enum DiagnosticSeverity {
    Error = 1,
    Warning = 2,
    Information = 3,
    Hint = 4
}
```

#### Expected Response Format (lo que espera Serena)
```typescript
// Serena usa request_text_document_diagnostics() que espera:
{
    "items": [
        {
            "range": {
                "start": { "line": 45, "character": 10 },
                "end": { "line": 45, "character": 25 }
            },
            "severity": 1,
            "message": "Undeclared identifier 'UnkownFunction'",
            "code": "E001",
            "source": "mql4"
        }
    ]
}
```

#### Requisitos para MQL4
- Errores de sintaxis del parser ANTLR
- Errores semánticos (tipos incompatibles, funciones no definidas)
- Warnings (variables no usadas, conversiones implícitas)
- Validación de funciones MQL4 específicas (`OnInit` debe retornar int, etc.)

---

### 4. `textDocument/completion` - Autocompletado

**Referencia**: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion

#### Request Parameters
```typescript
interface CompletionParams extends TextDocumentPositionParams,
    WorkDoneProgressParams, PartialResultParams {
    context?: CompletionContext;
}

interface CompletionContext {
    triggerKind: CompletionTriggerKind;
    triggerCharacter?: string;
}

enum CompletionTriggerKind {
    Invoked = 1,
    TriggerCharacter = 2,
    TriggerForIncompleteCompletions = 3
}
```

#### Response
```typescript
// Puede ser array o CompletionList
type CompletionResult = CompletionItem[] | CompletionList | null;

interface CompletionList {
    isIncomplete: boolean;  // true = seguir pidiendo mientras escribe
    items: CompletionItem[];
}

interface CompletionItem {
    label: string;           // Texto mostrado (REQUIRED)
    kind?: CompletionItemKind;
    detail?: string;         // Info adicional (tipo, firma)
    documentation?: string | MarkupContent;
    insertText?: string;
    textEdit?: {
        newText: string;
        range: Range;
    } | {
        newText: string;
    };
    sortText?: string;       // Para ordering
    filterText?: string;     // Para filtering
    preselect?: boolean;
    deprecated?: boolean;
}

enum CompletionItemKind {
    Text = 1, Method = 3, Function = 6, Variable = 13,
    Class = 5, Constant = 14, Keyword = 14, Snippet = 15
}
```

#### Expected Response Format (lo que espera Serena)
```typescript
// Serena usa request_completions() que espera dict con 'items':
{
    "isIncomplete": false,
    "items": [
        {
            "label": "NormalizeDouble",
            "kind": 6,  // Function
            "detail": "double NormalizeDouble(double value, int digits)",
            "insertText": "NormalizeDouble(",
            "textEdit": {
                "newText": "NormalizeDouble(",
                "range": { ... }
            }
        }
    ]
}

// Si es array, Serena lo convierte:
// response = response || { "items": response, "isIncomplete": false }
```

#### Requisitos para MQL4
- Keywords MQL4 (`if`, `for`, `return`, `void`, `int`, `double`, etc.)
- Funciones built-in (`OrderSend`, `NormalizeDouble`, `MathSum`, etc.)
- Funciones definidas por el usuario en el archivo actual
- Variables locales y globales
- Inputs y externals
- Trigger characters: `.` (miembros), `(` (funciones)

---

## Implementación Recomendada

### Estructura del Proyecto (.NET)

```
mql4-language-server/
├── src/
│   ├── Mql4Lsp.Server/
│   │   ├── Lsp/
│   │   │   ├── WorkspaceSymbolHandler.cs
│   │   │   ├── RenameHandler.cs
│   │   │   ├── DiagnosticHandler.cs
│   │   │   └── CompletionHandler.cs
│   │   ├── Mql4LanguageServer.cs
│   │   └── Program.cs
│   └── Mql4Lsp.Core/
│       ├── Parsing/
│       │   └── Mql4Parser.cs (ANTLR)
│       ├── Symbols/
│       │   ├── Mql4Symbol.cs
│       │   ├── SymbolIndex.cs
│       │   └── WorkspaceIndexer.cs
│       └── Diagnostics/
│           └── Mql4DiagnosticProvider.cs
```

### Patrón de Implementación

Cada handler debe implementar la interfaz LSP correspondiente:

```csharp
// Ejemplo: WorkspaceSymbolHandler.cs
public class WorkspaceSymbolHandler : IRequestHandler<WorkspaceSymbolParams, WorkspaceSymbol[]>
{
    private readonly SymbolIndex _symbolIndex;
    
    public WorkspaceSymbolHandler(SymbolIndex symbolIndex)
    {
        _symbolIndex = symbolIndex;
    }
    
    public async Task<WorkspaceSymbol[]> Handle(WorkspaceSymbolParams request, CancellationToken cancellationToken)
    {
        var query = request.Query ?? "";
        var symbols = _symbolIndex.Search(query);
        
        return symbols
            .Take(100)  // Limitar resultados
            .Select(s => new WorkspaceSymbol
            {
                Name = s.Name,
                Kind = MapSymbolKind(s.Kind),
                Location = new Location
                {
                    Uri = new Uri(s.FilePath),
                    Range = new Range
                    {
                        Start = new Position(s.StartLine, s.StartColumn),
                        End = new Position(s.EndLine, s.EndColumn)
                    }
                }
            })
            .ToArray();
    }
    
    private static SymbolKind MapSymbolKind(Mql4SymbolKind kind) => kind switch
    {
        Mql4SymbolKind.Function => SymbolKind.Function,
        Mql4SymbolKind.Variable => SymbolKind.Variable,
        Mql4SymbolKind.Input => SymbolKind.Constant,
        // ... etc
    };
}
```

### Registro en el Servidor

```csharp
// En Mql4LanguageServer.cs o Program.cs
public void ConfigureServices(IServiceCollection services)
{
    // ... servicios existentes
    
    services.AddSingleton<SymbolIndex>();
    services.AddSingleton<WorkspaceIndexer>();
    
    // Registrar handlers LSP
    services.AddLspHandler<WorkspaceSymbolParams, WorkspaceSymbolHandler>();
    services.AddLspHandler<RenameParams, WorkspaceEdit, RenameHandler>();
    services.AddLspHandler<CompletionParams, CompletionList, CompletionHandler>();
    services.AddLspHandler<DocumentDiagnosticParams, FullDocumentDiagnosticReport, DiagnosticHandler>();
}
```

---

## Notas de Implementación

1. **Índice del Workspace**: Mantener un índice en memoria de todos los símbolos para `workspace/symbol`. Actualizar cuando se modifiquen archivos.

2. **Líneas 0-indexed**: LSP usa líneas 0-indexed (no 1-indexed como muchos editores). ASEGURARSE de restar 1 al convertir desde el parser.

3. **Caracteres UTF-16**: Las posiciones de carácter en LSP son en código units UTF-16, no caracteres Unicode. ANTLR puede usar offsets de bytes - convertir apropiadamente.

4. **Símbolos MQL4 Específicos**:
   - **Expert Advisors**: `OnInit()`, `OnDeinit()`, `OnTick()`
   - **Indicadores**: `OnInit()`, `OnDeinit()`, `OnCalculate()`
   - **Scripts**: `OnStart()`
   - **Buffers**: Arrays especiales para indicadores (`HighBuffer[]`, etc.)
   - **Inputs**: Parámetros configurables (`input int Period = 14;`)

5. **Testing**: Verificar con los tests en `serena-mql4/test/solidlsp/mql4/test_mql4_comprehensive.py`:
   - `TestMql4LanguageServerWorkspaceSymbol` (5 tests)
   - `TestMql4LanguageServerRenameSymbol` (3 tests)
   - `TestMql4LanguageServerDiagnostics` (3 tests)
   - `TestMql4LanguageServerCompletions` (2 tests)

---

## Recursos Adicionales

- **Especificación LSP 3.17**: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
- **Reposoitorio de Serena**: https://github.com/davalillo/serena-mql4 (para ver cómo usa estos métodos)
- **Tests de referencia**: `test/solidlsp/mql4/test_mql4_comprehensive.py`
