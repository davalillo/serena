//+------------------------------------------------------------------+
//|                                           CustomIndicators.mqh |
//|                                  Copyright 2024, MQL4 Developer |
//|                            Common functions for custom indicators |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MQL4 Developer"
#property link      ""
#property version   "1.00"

#ifndef CUSTOM_INDICATORS_MQH
#define CUSTOM_INDICATORS_MQH

//--- Enumeration for indicator types
enum ENUM_INDICATOR_TYPE
{
    INDICATOR_SMA,
    INDICATOR_EMA,
    INDICATOR_RSI,
    INDICATOR_MACD,
    INDICATOR_BOLLINGER
};

//--- Structure for indicator parameters
struct IndicatorParams
{
    int period;
    int shift;
    double multiplier;
    ENUM_APPLIED_PRICE applied_price;
};

//+------------------------------------------------------------------+
//| Calculate Simple Moving Average                                  |
//+------------------------------------------------------------------+
double CalculateSMA(int period, int shift, ENUM_APPLIED_PRICE price = PRICE_CLOSE)
{
    double sum = 0.0;
    for(int i = 0; i < period; i++)
    {
        sum += iMA(Symbol(), Period(), 1, 0, MODE_SMA, price, shift + i);
    }
    return sum / period;
}

//+------------------------------------------------------------------+
//| Calculate Exponential Moving Average                             |
//+------------------------------------------------------------------+
double CalculateEMA(int period, int shift, ENUM_APPLIED_PRICE price = PRICE_CLOSE)
{
    double alpha = 2.0 / (period + 1.0);
    static double ema_prev = 0.0;
    static bool first_call = true;

    if(first_call)
    {
        // First EMA value is SMA
        ema_prev = CalculateSMA(period, shift, price);
        first_call = false;
    }
    else
    {
        // Calculate EMA using previous value
        double current_price = iMA(Symbol(), Period(), 1, 0, MODE_SMA, price, shift);
        ema_prev = alpha * current_price + (1.0 - alpha) * ema_prev;
    }

    return ema_prev;
}

//+------------------------------------------------------------------+
//| Calculate RSI (Relative Strength Index)                          |
//+------------------------------------------------------------------+
double CalculateRSI(int period, int shift, ENUM_APPLIED_PRICE price = PRICE_CLOSE)
{
    double gains = 0.0;
    double losses = 0.0;

    // Calculate average gains and losses
    for(int i = 1; i < period + 1; i++)
    {
        double change = iMA(Symbol(), Period(), 1, 0, MODE_SMA, price, shift + i - 1) -
                       iMA(Symbol(), Period(), 1, 0, MODE_SMA, price, shift + i);

        if(change > 0)
            gains += change;
        else
            losses += MathAbs(change);
    }

    double avgGain = gains / period;
    double avgLoss = losses / period;

    if(avgLoss == 0)
        return 100.0;

    double rs = avgGain / avgLoss;
    return 100.0 - (100.0 / (1.0 + rs));
}

//+------------------------------------------------------------------+
//| Calculate Bollinger Bands upper line                             |
//+------------------------------------------------------------------+
double CalculateBollingerUpper(int period, double deviation, int shift)
{
    double sma = CalculateSMA(period, shift);
    double sum = 0.0;

    // Calculate standard deviation
    for(int i = 0; i < period; i++)
    {
        double price = iMA(Symbol(), Period(), 1, 0, MODE_SMA, PRICE_CLOSE, shift + i);
        sum += MathPow(price - sma, 2);
    }

    double stdDev = MathSqrt(sum / period);
    return sma + (deviation * stdDev);
}

//+------------------------------------------------------------------+
//| Calculate Bollinger Bands lower line                             |
//+------------------------------------------------------------------+
double CalculateBollingerLower(int period, double deviation, int shift)
{
    double sma = CalculateSMA(period, shift);
    double sum = 0.0;

    // Calculate standard deviation
    for(int i = 0; i < period; i++)
    {
        double price = iMA(Symbol(), Period(), 1, 0, MODE_SMA, PRICE_CLOSE, shift + i);
        sum += MathPow(price - sma, 2);
    }

    double stdDev = MathSqrt(sum / period);
    return sma - (deviation * stdDev);
}

//+------------------------------------------------------------------+
//| Get custom indicator handle                                      |
//+------------------------------------------------------------------+
int GetCustomIndicatorHandle(ENUM_INDICATOR_TYPE indicatorType, IndicatorParams &params)
{
    switch(indicatorType)
    {
        case INDICATOR_SMA:
            return iMA(Symbol(), Period(), params.period, 0, MODE_SMA, params.applied_price);
        case INDICATOR_EMA:
            return iMA(Symbol(), Period(), params.period, 0, MODE_EMA, params.applied_price);
        case INDICATOR_RSI:
            return iRSI(Symbol(), Period(), params.period, params.applied_price);
        case INDICATOR_MACD:
            return iMACD(Symbol(), Period(), 12, 26, 9, params.applied_price);
        case INDICATOR_BOLLINGER:
            return iBands(Symbol(), Period(), params.period, 0, params.multiplier, params.applied_price);
        default:
            return INVALID_HANDLE;
    }
}

//+------------------------------------------------------------------+
//| Validate indicator parameters                                    |
//+------------------------------------------------------------------+
bool ValidateIndicatorParams(ENUM_INDICATOR_TYPE indicatorType, IndicatorParams &params)
{
    // Validate period
    if(params.period <= 0 || params.period > 1000)
    {
        Print("Invalid period: ", params.period);
        return false;
    }

    // Validate multiplier for Bollinger Bands
    if(indicatorType == INDICATOR_BOLLINGER && (params.multiplier <= 0 || params.multiplier > 10))
    {
        Print("Invalid multiplier for Bollinger Bands: ", params.multiplier);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Free indicator handle                                            |
//+------------------------------------------------------------------+
void FreeIndicatorHandle(int handle)
{
    if(handle != INVALID_HANDLE)
    {
        IndicatorRelease(handle);
    }
}

//+------------------------------------------------------------------+
//| Calculate support and resistance levels                          |
//+------------------------------------------------------------------+
double CalculateSupport(int period, int shift)
{
    double lowest = Low[iLowest(Symbol(), Period(), MODE_LOW, period, shift)];
    return lowest;
}

//+------------------------------------------------------------------+
//| Calculate support and resistance levels                          |
//+------------------------------------------------------------------+
double CalculateResistance(int period, int shift)
{
    double highest = High[iHighest(Symbol(), Period(), MODE_HIGH, period, shift)];
    return highest;
}

//+------------------------------------------------------------------+
//| Helper function to calculate price range                         |
//+------------------------------------------------------------------+
double CalculatePriceRange(int period, int shift)
{
    double support = CalculateSupport(period, shift);
    double resistance = CalculateResistance(period, shift);
    return resistance - support;
}

#endif // CUSTOM_INDICATORS_MQH
