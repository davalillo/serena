//+------------------------------------------------------------------+
//|                                              ExpertAdvisor.mq4 |
//|                                  Copyright 2024, MQL4 Developer |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MQL4 Developer"
#property link      ""
#property version   "1.00"
#property strict

// Include custom indicators
#include <Include/CustomIndicators.mqh>

//--- Input parameters
input int      MagicNumber = 12345;
input double   LotSize = 0.1;
input int      StopLoss = 50;
input int      TakeProfit = 100;
input int      FastEMA = 10;
input int      SlowEMA = 20;

//--- Global variables
int handleFastEMA;
int handleSlowEMA;
double fastEMA[];
double slowEMA[];
datetime lastBarTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- Initialize indicators
    handleFastEMA = iMA(Symbol(), Period(), FastEMA, 0, MODE_EMA, PRICE_CLOSE);
    handleSlowEMA = iMA(Symbol(), Period(), SlowEMA, 0, MODE_EMA, PRICE_CLOSE);

    if(handleFastEMA == INVALID_HANDLE || handleSlowEMA == INVALID_HANDLE)
    {
        Print("Error creating indicators");
        return INIT_FAILED;
    }

    //--- Set array properties
    ArraySetAsSeries(fastEMA, true);
    ArraySetAsSeries(slowEMA, true);

    Print("Expert Advisor initialized successfully");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    //--- Release indicator handles
    if(handleFastEMA != INVALID_HANDLE)
        IndicatorRelease(handleFastEMA);
    if(handleSlowEMA != INVALID_HANDLE)
        IndicatorRelease(handleSlowEMA);

    Print("Expert Advisor deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    //--- Check for new bar
    datetime currentBarTime = Time[0];
    if(currentBarTime == lastBarTime)
        return;

    lastBarTime = currentBarTime;

    //--- Copy indicator values
    if(CopyBuffer(handleFastEMA, 0, 0, 3, fastEMA) < 0 ||
       CopyBuffer(handleSlowEMA, 0, 0, 3, slowEMA) < 0)
    {
        Print("Error copying indicator values");
        return;
    }

    //--- Check for trade conditions
    CheckForTradeSignals();
}

//+------------------------------------------------------------------+
//| Check for trade signals                                          |
//+------------------------------------------------------------------+
void CheckForTradeSignals()
{
    //--- Get current prices
    double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
    double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);

    //--- Check for buy signal (Fast EMA crosses above Slow EMA)
    if(fastEMA[1] > slowEMA[1] && fastEMA[2] <= slowEMA[2])
    {
        if(!HasOpenPosition(POSITION_TYPE_BUY))
        {
            OpenPosition(POSITION_TYPE_BUY, ask);
        }
    }

    //--- Check for sell signal (Fast EMA crosses below Slow EMA)
    if(fastEMA[1] < slowEMA[1] && fastEMA[2] >= slowEMA[2])
    {
        if(!HasOpenPosition(POSITION_TYPE_SELL))
        {
            OpenPosition(POSITION_TYPE_SELL, bid);
        }
    }

    //--- Manage open positions
    ManageOpenPositions();
}

//+------------------------------------------------------------------+
//| Open a new position                                              |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_POSITION_TYPE positionType, double price)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};

    //--- Calculate stop loss and take profit
    double sl;
    if(positionType == POSITION_TYPE_BUY)
        sl = price - StopLoss * Point;
    else
        sl = price + StopLoss * Point;

    double tp;
    if(positionType == POSITION_TYPE_BUY)
        tp = price + TakeProfit * Point;
    else
        tp = price - TakeProfit * Point;

    //--- Prepare trade request
    request.action = TRADE_ACTION_DEAL;
    request.symbol = Symbol();
    request.volume = LotSize;
    if(positionType == POSITION_TYPE_BUY)
        request.type = ORDER_TYPE_BUY;
    else
        request.type = ORDER_TYPE_SELL;
    request.price = price;
    request.sl = sl;
    request.tp = tp;
    request.magic = MagicNumber;
    request.comment = "EA Trade";

    //--- Send order
    if(OrderSend(request, result))
    {
        Print("Order opened successfully: ", result.order);
    }
    else
    {
        Print("Error opening order: ", result.retcode);
    }
}

//+------------------------------------------------------------------+
//| Check if position already exists                                 |
//+------------------------------------------------------------------+
bool HasOpenPosition(ENUM_POSITION_TYPE positionType)
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol() &&
               PositionGetInteger(POSITION_MAGIC) == MagicNumber &&
               PositionGetInteger(POSITION_TYPE) == positionType)
            {
                return true;
            }
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Manage open positions                                            |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol() &&
               PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            {
                //--- Check if stop loss or take profit should be updated
                // Implementation for trailing stop or breakeven logic
                UpdatePositionExit(i);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update position exit levels                                      |
//+------------------------------------------------------------------+
void UpdatePositionExit(int positionIndex)
{
    // Implementation for updating stop loss based on market conditions
    // This is a placeholder for more advanced position management
}
