//+------------------------------------------------------------------+
//|                                                  MyIndicator.mq4 |
//|                                  Copyright 2024, MQL4 Developer |
//|                                    Custom Indicator for MQL4    |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MQL4 Developer"
#property link      ""
#property version   "1.00"
#property strict
#property indicator_separate_window
#property indicator_buffers 4
#property indicator_plots   4

#property indicator_label1  "Upper Band"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrRed
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1

#property indicator_label2  "Lower Band"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrBlue
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1

#property indicator_label3  "Middle Band"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrYellow
#property indicator_style3  STYLE_DOT
#property indicator_width3  1

#property indicator_label4  "Signal"
#property indicator_type4   DRAW_ARROW
#property indicator_color4  clrLime
#property indicator_style4  STYLE_SOLID
#property indicator_width4  2

//--- Input parameters
input int      Period = 20;          // Period for calculation
input double   Deviation = 2.0;      // Standard deviation multiplier
input int      Shift = 0;            // Shift

//--- Indicator buffers
double UpperBandBuffer[];
double LowerBandBuffer[];
double MiddleBandBuffer[];
double SignalBuffer[];

//--- Global variables
int handleSMA;
datetime lastBarTime = 0;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- Validate input parameters
    if(Period <= 0 || Period > 1000)
    {
        Print("Error: Invalid period parameter");
        return INIT_PARAMETERS_INCORRECT;
    }

    if(Deviation <= 0 || Deviation > 10)
    {
        Print("Error: Invalid deviation parameter");
        return INIT_PARAMETERS_INCORRECT;
    }

    //--- Set indicator buffers
    SetIndexBuffer(0, UpperBandBuffer);
    SetIndexBuffer(1, LowerBandBuffer);
    SetIndexBuffer(2, MiddleBandBuffer);
    SetIndexBuffer(3, SignalBuffer);

    //--- Set buffer properties
    SetIndexLabel(0, "Upper Band");
    SetIndexLabel(1, "Lower Band");
    SetIndexLabel(2, "Middle Band");
    SetIndexLabel(3, "Signal");

    //--- Set drawing begin
    SetIndexDrawBegin(0, Period);
    SetIndexDrawBegin(1, Period);
    SetIndexDrawBegin(2, Period);
    SetIndexDrawBegin(3, Period);

    //--- Set as series
    ArraySetAsSeries(UpperBandBuffer, true);
    ArraySetAsSeries(LowerBandBuffer, true);
    ArraySetAsSeries(MiddleBandBuffer, true);
    ArraySetAsSeries(SignalBuffer, true);

    //--- Initialize indicator handle for SMA
    handleSMA = iMA(Symbol(), Period(), Period, 0, MODE_SMA, PRICE_CLOSE);

    if(handleSMA == INVALID_HANDLE)
    {
        Print("Error creating SMA indicator");
        return INIT_FAILED;
    }

    //--- Set indicator name
    IndicatorSetString(INDICATOR_SHORTNAME, "MyIndicator(" + IntegerToString(Period) + "," + DoubleToString(Deviation, 1) + ")");

    Print("MyIndicator initialized successfully");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    //--- Release indicator handle
    if(handleSMA != INVALID_HANDLE)
        IndicatorRelease(handleSMA);

    Print("MyIndicator deinitialized");
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
    //--- Check for minimum bars
    if(rates_total < Period)
        return 0;

    //--- Determine from where to start calculation
    int start = prev_calculated;
    if(start == 0)
    {
        start = Period;
        // Initialize previous values
        for(int i = 0; i < Period; i++)
        {
            UpperBandBuffer[i] = EMPTY_VALUE;
            LowerBandBuffer[i] = EMPTY_VALUE;
            MiddleBandBuffer[i] = EMPTY_VALUE;
            SignalBuffer[i] = EMPTY_VALUE;
        }
    }

    //--- Calculate for each bar
    for(int i = start; i < rates_total; i++)
    {
        //--- Calculate SMA (middle band)
        double sma_value = CalculateSMA(i);
        MiddleBandBuffer[i] = sma_value;

        //--- Calculate Bollinger Bands
        CalculateBollingerBands(i, sma_value, UpperBandBuffer, LowerBandBuffer);

        //--- Generate signals
        GenerateSignals(i, close[i], UpperBandBuffer[i], LowerBandBuffer[i]);
    }

    return rates_total;
}

//+------------------------------------------------------------------+
//| Calculate SMA value                                              |
//+------------------------------------------------------------------+
double CalculateSMA(int shift)
{
    double sum = 0.0;

    // Calculate sum of closing prices
    for(int i = 0; i < Period; i++)
    {
        sum += iClose(Symbol(), Period(), shift + i);
    }

    return sum / Period;
}

//+------------------------------------------------------------------+
//| Calculate Bollinger Bands                                        |
//+------------------------------------------------------------------+
void CalculateBollingerBands(int shift, double middle_band, double &upper[], double &lower[])
{
    double sum_squared_deviation = 0.0;

    // Calculate sum of squared deviations
    for(int i = 0; i < Period; i++)
    {
        double price = iClose(Symbol(), Period(), shift + i);
        double deviation = price - middle_band;
        sum_squared_deviation += deviation * deviation;
    }

    // Calculate standard deviation
    double std_deviation = MathSqrt(sum_squared_deviation / Period);

    // Calculate upper and lower bands
    upper[shift] = middle_band + (Deviation * std_deviation);
    lower[shift] = middle_band - (Deviation * std_deviation);
}

//+------------------------------------------------------------------+
//| Generate trading signals                                         |
//+------------------------------------------------------------------+
void GenerateSignals(int shift, double close_price, double upper_band, double lower_band)
{
    // Initialize signal
    SignalBuffer[shift] = EMPTY_VALUE;

    // Buy signal: price touches lower band
    if(shift > 0)
    {
        double prev_close = iClose(Symbol(), Period(), shift + 1);
        double prev_lower = lower[shift + 1];

        if(prev_close > prev_lower && close_price <= lower_band)
        {
            SignalBuffer[shift] = lower_band - 10 * Point;
        }

        // Sell signal: price touches upper band
        double prev_upper = upper[shift + 1];
        if(prev_close < prev_upper && close_price >= upper_band)
        {
            SignalBuffer[shift] = upper_band + 10 * Point;
        }
    }
}

//+------------------------------------------------------------------+
//| Get indicator value for external use                             |
//+------------------------------------------------------------------+
double GetIndicatorValue(int buffer_index, int shift)
{
    switch(buffer_index)
    {
        case 0: return UpperBandBuffer[shift];
        case 1: return LowerBandBuffer[shift];
        case 2: return MiddleBandBuffer[shift];
        case 3: return SignalBuffer[shift];
        default: return EMPTY_VALUE;
    }
}

//+------------------------------------------------------------------+
//| Validate indicator state                                         |
//+------------------------------------------------------------------+
bool IsIndicatorValid()
{
    if(handleSMA == INVALID_HANDLE)
    {
        Print("Error: SMA handle is invalid");
        return false;
    }

    if(Period <= 0)
    {
        Print("Error: Period is invalid");
        return false;
    }

    return true;
}
