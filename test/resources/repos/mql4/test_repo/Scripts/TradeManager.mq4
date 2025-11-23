//+------------------------------------------------------------------+
//|                                              TradeManager.mq4  |
//|                                  Copyright 2024, MQL4 Developer |
//|                            Script for managing trading positions |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MQL4 Developer"
#property link      ""
#property version   "1.00"
#property strict

//--- Input parameters
input int      MagicNumber = 12345;
input double   LotSize = 0.1;
input int      MaxPositions = 5;
input bool     CloseAllPositions = false;
input bool     TrailingStopEnabled = true;
input int      TrailingStop = 30;
input int      TrailingStep = 5;

//--- Global variables
string scriptName = "TradeManager";

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== ", scriptName, " started ===");

    if(CloseAllPositions)
    {
        CloseAllOpenPositions();
    }
    else
    {
        // Display position information
        DisplayPositionInfo();

        // Manage trailing stops if enabled
        if(TrailingStopEnabled)
        {
            ManageTrailingStops();
        }

        // Close positions based on certain conditions
        CheckForCloseConditions();
    }

    Print("=== ", scriptName, " completed ===");
}

//+------------------------------------------------------------------+
//| Close all open positions                                         |
//+------------------------------------------------------------------+
void CloseAllOpenPositions()
{
    Print("Closing all positions...");

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol())
            {
                ClosePosition(i);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close a specific position                                        |
//+------------------------------------------------------------------+
void ClosePosition(int positionIndex)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};

    if(!PositionSelectByIndex(positionIndex))
    {
        Print("Error: Cannot select position at index ", positionIndex);
        return;
    }

    ENUM_POSITION_TYPE positionType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentTP = PositionGetDouble(POSITION_TP);

    //--- Prepare close request
    request.action = TRADE_ACTION_DEAL;
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.volume = PositionGetDouble(POSITION_VOLUME);
    if(positionType == POSITION_TYPE_BUY)
        request.type = ORDER_TYPE_SELL;
    else
        request.type = ORDER_TYPE_BUY;
    request.position = PositionGetInteger(POSITION_TICKET);
    request.magic = PositionGetInteger(POSITION_MAGIC);
    request.comment = "TradeManager Close";

    //--- Determine price
    if(positionType == POSITION_TYPE_BUY)
        request.price = SymbolInfoDouble(Symbol(), SYMBOL_BID);
    else
        request.price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);

    //--- Send close request
    if(OrderSend(request, result))
    {
        Print("Position closed successfully: Ticket=", result.order, " Profit=", PositionGetDouble(POSITION_PROFIT));
    }
    else
    {
        Print("Error closing position: Retcode=", result.retcode);
    }
}

//+------------------------------------------------------------------+
//| Display position information                                     |
//+------------------------------------------------------------------+
void DisplayPositionInfo()
{
    int buyPositions = 0;
    int sellPositions = 0;
    double totalProfit = 0.0;
    double totalVolume = 0.0;

    Print("\n=== Position Information ===");
    Print("Symbol: ", Symbol());
    Print("Current Price - Ask: ", SymbolInfoDouble(Symbol(), SYMBOL_ASK), " Bid: ", SymbolInfoDouble(Symbol(), SYMBOL_BID));
    Print("Spread: ", SymbolInfoInteger(Symbol(), SYMBOL_SPREAD));
    Print("");

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol())
            {
                ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
                double profit = PositionGetDouble(POSITION_PROFIT);
                double volume = PositionGetDouble(POSITION_VOLUME);
                int ticket = (int)PositionGetInteger(POSITION_TICKET);
                double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                double currentSL = PositionGetDouble(POSITION_SL);
                double currentTP = PositionGetDouble(POSITION_TP);

                if(posType == POSITION_TYPE_BUY)
                    buyPositions++;
                else
                    sellPositions++;

                totalProfit += profit;
                totalVolume += volume;

                Print("Ticket: ", ticket);
                Print("  Type: ", EnumToString(posType));
                Print("  Volume: ", volume);
                Print("  Open Price: ", openPrice);
                Print("  Current Profit: ", profit);
                Print("  Stop Loss: ", currentSL);
                Print("  Take Profit: ", currentTP);
                Print("  Swap: ", PositionGetDouble(POSITION_SWAP));
                Print("");
            }
        }
    }

    Print("=== Summary ===");
    Print("Buy Positions: ", buyPositions);
    Print("Sell Positions: ", sellPositions);
    Print("Total Volume: ", totalVolume);
    Print("Total Profit: ", totalProfit);
    Print("=========================\n");
}

//+------------------------------------------------------------------+
//| Manage trailing stops                                            |
//+------------------------------------------------------------------+
void ManageTrailingStops()
{
    Print("Managing trailing stops...");

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol())
            {
                ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
                double currentSL = PositionGetDouble(POSITION_SL);
                double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                int magic = (int)PositionGetInteger(POSITION_MAGIC);

                // Only manage positions with our magic number
                if(magic != MagicNumber)
                    continue;

                // Calculate new stop loss based on trailing stop
                double newSL = CalculateTrailingStop(posType, openPrice, currentSL);

                if(newSL > 0)
                {
                    ModifyPositionStopLoss(i, newSL);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate trailing stop level                                    |
//+------------------------------------------------------------------+
double CalculateTrailingStop(ENUM_POSITION_TYPE positionType, double openPrice, double currentSL)
{
    double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);

    if(positionType == POSITION_TYPE_BUY)
    {
        double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
        double newSL = bid - TrailingStop * point;

        // Only update if new SL is higher than current SL (or if no SL set)
        if(currentSL == 0 || newSL > currentSL + TrailingStep * point)
        {
            return newSL;
        }
    }
    else // SELL position
    {
        double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
        double newSL = ask + TrailingStop * point;

        // Only update if new SL is lower than current SL (or if no SL set)
        if(currentSL == 0 || newSL < currentSL - TrailingStep * point)
        {
            return newSL;
        }
    }

    return 0; // No change needed
}

//+------------------------------------------------------------------+
//| Modify position stop loss                                        |
//+------------------------------------------------------------------+
void ModifyPositionStopLoss(int positionIndex, double newSL)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};

    if(!PositionSelectByIndex(positionIndex))
    {
        Print("Error: Cannot select position at index ", positionIndex);
        return;
    }

    request.action = TRADE_ACTION_SLTP;
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.position = PositionGetInteger(POSITION_TICKET);
    request.sl = newSL;
    request.tp = PositionGetDouble(POSITION_TP);

    if(OrderSend(request, result))
    {
        Print("Stop loss modified for ticket ", result.order, " to ", newSL);
    }
    else
    {
        Print("Error modifying stop loss: Retcode=", result.retcode);
    }
}

//+------------------------------------------------------------------+
//| Check for close conditions                                       |
//+------------------------------------------------------------------+
void CheckForCloseConditions()
{
    // Implementation for custom close conditions
    // For example: close all positions if daily loss exceeds X%

    double totalEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double totalBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double dailyPnL = totalEquity - totalBalance;

    // Close all positions if daily loss exceeds 5% of balance
    double maxDailyLoss = totalBalance * 0.05;

    if(dailyPnL < -maxDailyLoss)
    {
        Print("Daily loss (", dailyPnL, ") exceeds maximum (", -maxDailyLoss, ")");
        Print("Closing all positions...");
        CloseAllOpenPositions();
    }
}

//+------------------------------------------------------------------+
//| Get total number of open positions                               |
//+------------------------------------------------------------------+
int GetOpenPositionsCount()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) == Symbol())
            {
                count++;
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Calculate position risk                                          |
//+------------------------------------------------------------------+
double CalculatePositionRisk(int positionIndex)
{
    if(!PositionSelectByIndex(positionIndex))
        return 0.0;

    double volume = PositionGetDouble(POSITION_VOLUME);
    double stopLoss = PositionGetDouble(POSITION_SL);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double tickValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);

    if(stopLoss == 0)
        return 0.0;

    double riskAmount = MathAbs(openPrice - stopLoss) * volume * tickValue;
    double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);

    return (riskAmount / accountBalance) * 100.0;
}
