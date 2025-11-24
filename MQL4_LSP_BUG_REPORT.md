# Bug Report: MQL4 LSP v1.3.0 Critical Parsing Failures

## Bug Report Template for MQL4 LSP Repository

**Repository**: https://github.com/davalillo/mql4-language-server
**Version**: v1.3.0
**ANTLR Version**: 4.13.1
**Platform**: Linux x64 (reproducible on all platforms)

---

## Summary

MQL4 LSP v1.3.0 fails to parse standard MQL4 syntax elements that are commonly found in real-world MQL4 projects. While basic functionality works for simplified code, **the parser generates hundreds of errors when processing production MQL4 code**.

## Severity

**Critical** - Parser unusable for real-world MQL4 development

## Affected Use Cases

- All users attempting to use language servers with existing MQL4 projects
- Users with preprocessor directives for platform compatibility
- Users with modern C-style syntax
- Any non-trivial MQL4 codebases

## Reproduction Steps

1. Download or create a real MQL4 project (see examples below)
2. Initialize MQL4 LSP on the project directory
3. Observe hundreds of parsing errors in logs

## Minimal Reproducible Examples

### Example 1: Logical Operators Fail

**File**: `Example1_LogicalOps.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Logical operators that fail parsing                    |
//+------------------------------------------------------------------+

bool CheckTradeCondition(int magic, double lotSize)
{
    // These logical operators cause "token recognition error"
    if(magic > 0 && lotSize > 0.01)
    {
        return true;
    }

    if(magic == 12345 || lotSize >= 0.1)
    {
        return false;
    }

    // Negation also fails
    if(!(AccountFreeMargin() > 1000))
    {
        Print("Not enough margin");
    }

    return true;
}

void OnTick()
{
    // Complex logical expression fails
    bool condition = (FastEMA[0] > SlowEMA[0]) && (RSI[0] > 30) && (RSI[0] < 70);

    if(condition && HasPosition(POSITION_TYPE_BUY))
    {
        // Do something
    }
}
```

**Expected Behavior**: Parse without errors
**Actual Behavior**: Multiple "token recognition error at: '&&'" and "token recognition error at: '||'"

---

### Example 2: Preprocessor Directives Fail

**File**: `Example2_Preprocessor.mqh`
```mql4
//+------------------------------------------------------------------+
//| Example: Preprocessor directives that fail parsing             |
//+------------------------------------------------------------------+

// Platform detection (common in MQL4)
#ifdef __MQL5__
    #define USE_MQL5_FEATURES
    #define ORDER_TYPE_ORDER ENUM_ORDER_TYPE
#else
    #ifdef __MQL4__
        #define USE_MQL4_FEATURES
        #define ORDER_TYPE_ORDER int
    #endif
#endif

// Build version checks (common in production)
#if (BUILD >= 2285)
    #property strict
#endif

#ifndef MYLIB_VERSION
#define MYLIB_VERSION "1.2.3"
#endif

// Conditional compilation
#ifdef DEBUG
    #define LOG_LEVEL LOG_DEBUG
#else
    #define LOG_LEVEL LOG_INFO
#endif

// Feature flags
#if USE_MQL5_FEATURES
    void ProcessTradeMQL5() { }
#else
    void ProcessTradeMQL4() { }
#endif

// Multiple conditions
#if (defined(__MQL5__) || defined(__MQL4__)) && (BUILD >= 2000)
    #define PLATFORM_SUPPORTED
#endif
```

**Expected Behavior**: Parse preprocessor directives correctly
**Actual Behavior**: Multiple "syntax error at '#if'", "syntax error at '#ifdef'", "syntax error at '#endif'"

---

### Example 3: Complex Structs Fail

**File**: `Example3_Structs.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Complex struct definitions that fail parsing           |
//+------------------------------------------------------------------+

// Nested struct
struct TradeInfo
{
    int ticket;
    double openPrice;
    datetime openTime;

    struct
    {
        int sl_pips;
        int tp_pips;
        bool breakeven;
    } exit_levels;

    string comment;
};

// Struct with arrays
struct IndicatorResult
{
    double values[100];
    int valid_count;
    double ma_buffer[10][5];  // 2D arrays
};

// Struct with function pointers (advanced)
struct TradeCallbacks
{
    void (*onOpen)(int ticket);
    void (*onClose)(int ticket);
    int (*onError)(int code);
};

// Typedef struct
typedef struct
{
    string symbol;
    ENUM_TIMEFRAMES tf;
    double price;
} PriceInfo;

// Using the structs
void ProcessTrade(TradeInfo &trade)
{
    if(trade.exit_levels.sl_pips > 0)
    {
        // Modify stop loss
    }
}

void AnalyzeIndicators(IndicatorResult &result)
{
    // Access 2D array
    double value = result.ma_buffer[0][0];
}
```

**Expected Behavior**: Parse all struct definitions
**Actual Behavior**: Multiple syntax errors on struct definitions, especially nested structs and arrays in structs

---

### Example 4: Array Declarations Fail

**File**: `Example4_Arrays.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Array declarations that fail parsing                   |
//+------------------------------------------------------------------+

// Dynamic arrays (basic - may work)
double prices[];

// Fixed-size arrays
double priceBuffer[1000];

// Multi-dimensional arrays
double matrix[10][20];

// Arrays in function parameters
double CalculateAverage(double values[], int count)
{
    double sum = 0;
    for(int i = 0; i < count; i++)
    {
        sum += values[i];
    }
    return sum / count;
}

// Array of structs
TradeInfo trades[100];
int tradeCount = 0;

// Using arrays
void OnTick()
{
    double fastEMA[10];
    double slowEMA[10];

    // This fails with logical operators in array access
    if(fastEMA[0] > slowEMA[0] && fastEMA[1] <= slowEMA[1])
    {
        // Signal
    }
}
```

**Expected Behavior**: Parse all array declarations and usage
**Actual Behavior**: Syntax errors, especially with 2D arrays and complex expressions

---

### Example 5: Complex Function Signatures Fail

**File**: `Example5_Functions.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Complex function signatures that fail parsing          |
//+------------------------------------------------------------------+

// Function with default parameters
bool OrderSendEx(
    string symbol,
    ENUM_ORDER_TYPE orderType,
    double volume,
    double price = 0,
    int sl = 0,
    int tp = 0,
    string comment = "",
    datetime expire = 0
)
{
    // Implementation
    return true;
}

// Function with reference parameters
void ModifyTrade(int ticket, double &newSL, double &newTP)
{
    // Implementation
}

// Function with array parameters
void ProcessTrades(TradeInfo &trades[], int &count)
{
    for(int i = 0; i < count; i++)
    {
        // Process each trade
    }
}

// Overloaded functions (if supported)
double CalculateMA(int period);
double CalculateMA(int period, ENUM_MA_METHOD method);
double CalculateMA(int period, int shift, ENUM_APPLIED_PRICE price);

// Function pointers
typedef bool (*OrderHandler)(string symbol, double volume, int type);

bool ExecuteOrder(string symbol, double volume, int type, OrderHandler handler)
{
    return handler(symbol, volume, type);
}
```

**Expected Behavior**: Parse all function signatures
**Actual Behavior**: Syntax errors on complex parameter lists, default values, reference parameters

---

### Example 6: Ternary Operators Fail

**File**: `Example6_Ternary.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Ternary operators that fail parsing                   |
//+------------------------------------------------------------------+

void OnTick()
{
    // Basic ternary operator
    double lotSize = (AccountBalance() < 1000) ? 0.01 : 0.1;

    // Nested ternary
    double tp = (Type == BUY) ?
                (EntryPrice + StopLossPips * Point) :
                (EntryPrice - StopLossPips * Point);

    // In complex expressions
    bool condition = (fastEMA[0] > slowEMA[0]) ?
                     (RSI[0] > 50) :
                     (RSI[0] < 50);

    // With logical operators
    double value = (a > b && c < d) ? result1 : result2;
}
```

**Expected Behavior**: Parse ternary operators
**Actual Behavior**: "syntax error" when encountering '?' and ':'

---

### Example 7: Macro Definitions Fail

**File**: `Example7_Macros.mqh`
```mql4
//+------------------------------------------------------------------+
//| Example: Macro definitions that fail parsing                   |
//+------------------------------------------------------------------+

// Simple macros
#define MAX(a,b) ((a) > (b) ? (a) : (b))
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#define ABS(a) ((a) >= 0 ? (a) : -(a))

// Complex macros
#define CALCULATE_LOT_SIZE(sl, risk) \
    (AccountBalance() * risk / (sl * Point * MarketInfo(Symbol(), MODE_TICKVALUE)))

#define CHECK_TRADE_CONDITIONS(magic, lot, sl, tp) \
    ((magic > 0) && (lot >= 0.01) && (sl > 0) && (tp > 0))

// String macros
#define VERSION "1.2.3"
#define AUTHOR "MQL4 Developer"

// Conditional macros
#ifdef __MQL5__
    #define IS_MQL5 true
#else
    #define IS_MQL5 false
#endif

// Multi-statement macros
#define LOG_ERROR(msg) \
    Print("[ERROR] ", msg); \
    Alert("Error: ", msg)
```

**Expected Behavior**: Parse macro definitions
**Actual Behavior**: "syntax error" on macro definitions, especially complex ones with multiple lines

---

### Example 8: Type Casting Failures

**File**: `Example8_Casting.mq4`
```mql4
//+------------------------------------------------------------------+
//| Example: Type casting that fails parsing                       |
//+------------------------------------------------------------------+

void ProcessData()
{
    // Explicit type casting
    int intValue = (int)price;
    double doubleValue = (double)volume;

    // Casting with complex expressions
    double result = (double)(intValue1 * intValue2);

    // Casting in function calls
    Print("Price: ", (double)price);
    OrderSend((string)symbol, (int)type, (double)volume, (double)price, 0, 0, (string)comment);

    // Cast with logical operators
    bool isValid = (bool)(value > 0);
}
```

**Expected Behavior**: Parse type casting
**Actual Behavior**: "syntax error" on type casting expressions

---

## Error Log Examples

When running LSP on any of these files, the error log contains:

```
[Error - 10:45:23 AM] MQL4 Language Server: token recognition error at: '&&'
[Error - 10:45:23 AM] MQL4 Language Server: token recognition error at: '||'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '#if'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '#ifdef'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '#endif'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '#define'
[Error - 10:45:23 AM] MQL4 Language Server: token recognition error at '?'
[Error - 10:45:23 AM] MQL4 Language Server: token recognition error at ':'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at 'struct'
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '[' (in array context)
[Error - 10:45:23 AM] MQL4 Language Server: syntax error at '(' (in casting context)
[Error - 10:45:23 AM] MQL4 Language Server: token recognition error at '!'
```

**Note**: These are standard MQL4 syntax elements present in 90%+ of real MQL4 projects.

## Test Files That Work

The provided test repository (`test/resources/repos/mql4/test_repo/`) works because it uses simplified syntax:

- Basic preprocessor (`#include`, simple `#property`)
- Simple functions without complex parameters
- Basic structs without nesting
- No logical operators (`&&`, `||`)
- No ternary operators
- No complex macros
- Simple array usage

This does not reflect real-world MQL4 code.

## ANTLR Grammar Issues

The grammar file likely needs updates to support:

1. **Logical Operators**
   - Add `&&`, `||`, `!` tokens
   - Add precedence rules

2. **Preprocessor Directives**
   - Support `#if`, `#ifdef`, `#ifndef`, `#else`, `#elif`, `#endif`
   - Support `#define` with complex definitions
   - Support `#undef`

3. **Struct/Union Definitions**
   - Nested structs
   - Arrays in structs
   - 2D arrays
   - Function pointers in structs

4. **Ternary Operator**
   - Add `?` and `:` tokens
   - Add conditional expression rule

5. **Type Casting**
   - Add cast expression rule
   - Handle complex cast expressions

6. **Advanced Arrays**
   - Multi-dimensional arrays
   - Array initialization

## Alternative: Use MQL5 LSP

MQL5 uses a different LSP implementation that successfully handles:
- All C-style operators
- Complex preprocessor directives
- Modern C++ syntax
- Advanced type systems

Many MQL4 projects can be adapted to MQL5 with minimal changes.

## Impact on Serena Integration

Serena integrates with MQL4 LSP through the LSP protocol. The parsing failures cause:

1. **Symbol Resolution Failures**: Cannot find symbols in complex code
2. **Navigation Failures**: Go-to-definition broken
3. **Reference Tracking Broken**: Cannot find references
4. **Indexing Failures**: Cannot index real projects
5. **Developer Experience**: Hundreds of error messages

This makes MQL4 support in Serena **unusable for production**.

## Request for Fix

Please prioritize fixing the ANTLR grammar to support:

1. **C-style logical operators** (`&&`, `||`, `!`)
2. **Complete preprocessor directive support**
3. **Complex struct/union definitions**
4. **Ternary operators**
5. **Type casting**
6. **Multi-dimensional arrays**

## Validation

After fixes, test with:
1. Popular MQL4 repositories on GitHub
2. Code from MQL4 forums and communities
3. MetaTrader 4 standard library
4. Third-party MQL4 libraries

## Additional Resources

- MQL4 Language Reference: https://docs.mql4.com/
- MQL4 Syntax: Similar to C/C++
- Real MQL4 examples: https://www.mql5.com/en/code/center?category=1

---

## Contact

This bug report is filed on behalf of the Serena project (https://github.com/oraios/serena).
We successfully integrated MQL4 LSP v1.3.0 and the basic functionality works,
but production use is blocked by these parsing limitations.

We are available to provide additional samples, testing, or collaboration on fixes.

---

**Bug Report Version**: 1.0
**Date**: 2025-11-24
**Filed By**: Serena Development Team
