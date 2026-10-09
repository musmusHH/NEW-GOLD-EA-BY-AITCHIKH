//+------------------------------------------------------------------+
//|                                                 gold_x9_FIXED.mq4 |
//|                                  Copyright 2026, Mr. CapFree     |
//|                                             https://example.com  |
//+------------------------------------------------------------------+
//|  MQL4 port of "gold x9 v6.3" - Base Strategy #9                  |
//|  Source video: "My Most Profitable Gold Trading Bot | Full Build |
//|  From Scratch, Step by Step" - Mr. CapFree (youtu.be/5HkZD7BGuYo)|
//|                                                                  |
//|  FULL FOCUS / DESIGN 4                                           |
//|  Four runtime palettes, full-width broker-data candles,          |
//|  open-first trade dock, closed-result EMA/DD and trade tracker.   |
//|  Trading logic and risk controls unchanged by the UI redesign.   |
//+------------------------------------------------------------------+
#property copyright   "Mr. CapFree"
#property link        "https://example.com"
#property version     "6.740"   // Broker-data chart panel + carryover performance
#property description "gold X9 Full Focus design 4 + four themes + broker-data chart"
#property strict
#include <Canvas\Canvas.mqh>

// Graphite Full Focus is drawn at runtime; no external bitmap skins required.

// Enum for Lot Sizing Methods
enum enumLotSizing
  {
   MANUAL_LOTS       = 0, // Manual/Fixed Lots
   TIERED_LOTS       = 1, // Tiered Lot Sizing
   RISK_SCALE_FACTOR = 2  // Risk Scale Factor
  };

// Design 4 palette selector (four complete runtime-rendered themes).
enum enumHudTheme
  {
   HUD_GRAPHITE=0,
   HUD_LIGHT=1,
   HUD_MIDNIGHT=2,
   HUD_EMERALD=3
  };

//--- INPUT PARAMETERS ---
//--- Trade Setup ---
input int      inputMagicNumber = 123457;                   // EA Magic Number (LAB build; original uses 123456)
input string   tradeComment     = "gold X9 LAB by Mr. CapFree"; // Trade Comment (LAB identity in history)

//--- Money Management ---
input enumLotSizing lotSizingMethod    = MANUAL_LOTS;       // Lot Sizing Method
input double        tieredLotRiskMeter = 1.0;               // Tiered Lot Risk Meter (1-100)
input double        fixedLotSize       = 0.01;              // Fixed Lot Size
input double        riskScaleFactor    = 1.0;               // Risk Scale Factor Percentage

//--- Prop Firm Entry Adjustments ---
input double   entryAdjustment     = 0.0;                   // Entry Point Adjustment
input double   stopLossAdjustment  = 0.0;                   // Stop Loss Adjustment
input double   tpAdjustment        = 0.0;                   // Take Profit Adjustment
input double   trailAdjustment     = 0.0;                   // Trailing Stop Adjustment
input double   salvageAdjustment   = 0.0;                   // Salvage Adjustment
input double   breakEvenAdjustment = 0.0;                   // Break-Even Adjustment

//--- Strategy Parameters (Base Strategy #9) ---
input ENUM_TIMEFRAMES fractalTimeFrame       = PERIOD_CURRENT; // Timeframe for Highs/Lows
input int             rescanMinutes          = 15;             // Rescan Frequency (Minutes)
input int             fractalRight           = 5;              // Bars Below to Right
input int             fractalLeft            = 5;              // Bars Below to Left
input int             fractalMaxSearch       = 200;            // Max Bars Search Back
input int             maxPendingOrders       = 10;              // Max Pending Orders
input int             pendingExpiryHours     = 15;             // Pending Order Expiration (Hours)
input ENUM_TIMEFRAMES exitTimeFrame          = PERIOD_M1;      // Trade Management Frequency
input int             maxOpenPositions       = 10;             // Max Open Positions
input double          minFractalClearancePct = 0.02;           // Min Distance from Fractal (% Price)
input int             duplicatePointDistance = 5;              // Min Points for Duplicate Order
input double          buyEntryOffsetPct      = -0.08;          // Buy Entry Offset (% Price)
input double          sellEntryOffsetPct     = -0.08;          // Sell Entry Offset (% Price)
input double          stopLossPct            = 2.0;            // Stop Loss (% Price)
input double          takeProfitPct          = 0.7;            // Take Profit (% Price)
input double          trailTriggerPct        = 0.2;            // Trailing Stop Trigger (% Price)
input double          trailDistancePct       = 0.2;            // Trailing Distance (% Price)
input double          maxTrailPct            = 1.0;            // Max Trailing Distance (% Price)
input double          salvageTriggerPct      = 1.0;            // Salvage Trigger (% Price)
input double          salvagePct             = 0.15;           // Salvage TP Offset (% Price)
input double          breakEvenTriggerPct    = 0.1;            // Break-Even Trigger (% Price)
input double          breakEvenLockPct       = 0.025;          // Break-Even Lock Profit (% Price)
input double          strategyRiskWeight     = 0.055;          // Strategy Risk Weighting

//--- Chart Style & CARBON GRID HUD ---
input enumHudTheme hudTheme = HUD_GRAPHITE;             // Initial Full Focus theme; THEME button cycles all four
input bool   applyChartStyle       = true;             // Apply Dark Theme + Candlesticks On Start
input color  chartBgColor          = C'255,255,255';        // Chart Background
input color  bullBodyColor         = C'255,255,255';    // Bull Candle Body
input color  bullWickColor         = C'176,137,30';    // Bull Candle Wick
input color  bearBodyColor         = C'219,181,65';     // Bear Candle Body
input color  bearWickColor         = C'176,137,30';     // Bear Candle Wick
input int    chartTradeRows       = 4;                // Trade table rows (1-40; limited by available chart height)
input double chartRightSpacePct   = 20.0;             // Blank space after latest candle (8-45 percent)
input int    chartStartBars       = 64;               // Custom chart starting candles (16-240)
input int    chartStartOffset     = 0;                // Starting bar offset (0 = live)
input bool   chartStartFitOrders  = false;            // false = BARS (default), true = ALL levels
input bool   hideOriginalChart    = true;             // Hide native candles/axes while custom chart is active
input bool   showLiveChartPanel   = true;             // Real broker candles + order overlay in middle panel
input bool   showDashboardPanel    = true;             // Show The Full Focus Dashboard
input bool   showSpreadTag         = true;             // Show LIVE Panel (spread/PL/pips/lots/countdown)
input color  panelBackground       = C'241,245,247';      // Panel Background
input color  panelBorder           = C'2,28,50';     // Panel Border
input color  panelTitleColor       = C'8,101,195';    // Panel Title Color
input color  panelTextColor        = C'5,5,5';   // Panel Text Color
input color  panelGoodColor        = C'34,214,127';    // Panel Positive / Active Color
input color  panelBadColor         = C'255,77,90';     // Panel Negative Color
input color  panelDimColor         = C'75,85,94';   // Panel Label / Dim Color
input color  panelAmberColor       = C'224,125,0';    // Panel Amber / Warning Color
input string panelFontName         = "Consolas";       // Panel Font
input int    panelFontSize         = 9;                // Panel Font Size

enum enumMatchMode
  {
   MATCH_MAGIC_OR_COMMENT = 0, // Match Magic Number OR Trade Comment substring
   MATCH_MAGIC_ONLY       = 1, // Match Magic Number strictly
   MATCH_COMMENT_ONLY     = 2, // Match Trade Comment substring strictly
   MATCH_ALL_SYMBOL       = 3  // Match all historical trades on symbol
  };

// Reporting identity: retained independently of removed result boxes.
input bool   tagOnlyMyMagic        = true;             // Filter live/closed reporting (true = use filterMatchMode)
input enumMatchMode filterMatchMode = MATCH_MAGIC_OR_COMMENT; // C2: History Filter Mode (0=Magic OR Comment, 1=Magic, 2=Comment, 3=All Symbol)
input bool   showEquityCurve       = true;             // Closed-result EMA curve in the equity dock
input int    eqCurveEmaPeriod      = 3;                // Closed-result EMA smoothing (1=raw, max 100)
input bool   showEquityDDLine      = false;            // Optional CLOSED-result drawdown line (separate % scale)
input color  equityDDLineColor     = C'235,82,82';      // Drawdown line color
input int    eqCurveSamples        = 64;               // C2: Equity Samples Kept For The Curve
//=========================================================================

//--- Drawdown Guard ---
input double maxAllowedDrawdownPct = 30.0;             // Max Allowed DAILY DD (% Equity, resets each day)
input bool   enableDDHalt          = true;             // Pause New Entries While DD >= Max

//--- LAB Enhancements (M1-M4) ---
input bool   enableAgedLossCut     = true;             // M1: Cut Aged Losing Positions
input double agedLossHours         = 4.0;              // M1: Age Threshold (hours)
input double agedLossMinLossPct    = 0.05;             // M1: Min Floating Loss (% price)
input bool   enableDeadWindow      = true;             // M2: Block Entries In Dead Window
input int    deadWindowFromHour    = 0;                // M2: From Server Hour (0-23)
input int    deadWindowToHour      = 5;                // M2: To Server Hour (exclusive)
input bool   enableEquityCurveHalt = true;             // M3: Equity-Curve Breaker
input double equityCurveHaltPct    = 10.0;             // M3: Halt At DD From Peak (%)
input int    equityHaltMode        = 0;                // M3: 0=hard halt+Mon probation, 1=half-lot while underwater
input bool   enableMidTargetTrail  = true;             // M4: Two-Stage Trail Below/Above Mid Target
input double midTargetPct          = 0.35;             // M4: Mid Target (% price)
input double trailDistanceWidePct  = 0.30;             // M4: Wide Trail Distance Below Mid (% price)
input double trailDistanceAfterMidPct = 0.15;          // M4: Tight Trail Distance Above Mid (% price)
input bool   enablePartialPay      = false;            // M4b: Partial-Close Half At Mid Target

//--- GLOBAL VARIABLES ---
double          Cut;
double          Spread;
ENUM_TIMEFRAMES activeFractalTimeFrame;
int             activeRescanTimeFrame;
int             activeFractalRight;
int             activeFractalLeft;
int             activeMaxSearch;
int             activeMaxPending;
int             activeMaxPositions;
double          activeDuplicateDistance;
int             activeExpiryHours;
int             activeMagicNumber;
ENUM_TIMEFRAMES activeExitTimeFrame;
double          activeFreezeLevel;
string          activeComment;
string          activeTradeSymbol;
double          activeSymbolPoint;
int             activeSymbolDigits;
double          activePipFactor;
double          activeStopLevel;
double          tieredLotsEffective;

int           daySwitchBufferMinutes = 30;
double        fractalMinDistance;
double        buyEntryOffset;
double        sellEntryOffset;
double        activeBreakEvenLockPct;
bool          virtualExpiration = true;
double        stopLossDistance;
double        tpDistance;
double        trailDistance;
double        minProfitDistance;
double        maxStopLossDistance;
double        maxLotCap = 100.0;
double        weightedRiskDivider = 1.0;

double        lastSwingHigh = 0.0;
double        lastSwingLow  = 0.0;
double        virtualStopLoss = 0.0;

double        virtualStopLossStore[20][2];
double        orderPriceMap[100][2];
int           virtualStopLossStoreSize = 20;

double        strategyLots = 0.01;
int           lastTradeTicket = 0;
datetime      pendingExpirySeconds = 0;
datetime      pendingExpiry = 0;

int           lastHour;
int           perStrategyRescanBars = 0;
int           perStrategyPendingRescanBars = 0;

datetime      lastFractalScanTime   = 0;
datetime      lastExitManageTime    = 0;
double        activeTickSize        = 0.0;
double        activeTickValue       = 0.0;

//=== DASHBOARD PANEL / CHART STYLE state ===
int           statTrades[10];
double        statClosed[10];
double        statPerTrade[10];
int           statOpenTrades[10];
double        statOpenPL[10];
double        g_totalClosedPL    = 0.0;
double        g_openPL           = 0.0;
int           g_dayKey           = 0;
double        g_dayStartEquity   = 0.0;
double        g_dayPeakEquity    = 0.0;
double        g_currentDD        = 0.0;
bool          g_ddHalted         = false;
uint          g_lastPanelMs      = 0;

//=== LAB MODULE state (M1-M4) ===
double        g_peakEquityLab    = 0.0;
bool          g_equityHalted     = false;
bool          g_probationWeek    = false;
double        g_lotMultiplier    = 1.0;
int           g_lastWeekKey      = -1;
int           g_lastDeadWinLogH   = -1;
int           g_lastHaltSkipLogH  = -1;
string        g_partialKeys[200];

// Only retained to clean up result cards created by earlier versions.
#define TAG_PREFIX "GX9T_"

//=== C2: equity-curve sample ring ===
#define EQ_MAX 512
double        g_eqVal[EQ_MAX];
double        g_eqEMA[EQ_MAX],g_eqDD[EQ_MAX];
double        g_eqRunningPeak=0.0,g_eqRunningEMA=0.0;
datetime      g_eqT[EQ_MAX];
int           g_eqN        = 0;

//=== HUD v2: panel geometry + object registry ===
int           g_activeTheme = 0;
#define HUD_PREFIX "GX9H_"
#define HUD_MAXO   480
#define HUD_NP     6
string        g_hName[HUD_MAXO];
int           g_hPanel[HUD_MAXO];
int           g_hDx[HUD_MAXO];
int           g_hDy[HUD_MAXO];
int           g_hRA[HUD_MAXO];
int           g_hSize[HUD_MAXO];
int           g_hRect[HUD_MAXO];
int           g_hW[HUD_MAXO];
int           g_hH[HUD_MAXO];
color         g_hBg[HUD_MAXO];
int           g_hN = 0;
int           g_px[HUD_NP], g_py[HUD_NP], g_pw[HUD_NP], g_ph[HUD_NP];
int           g_chartW = 0, g_chartH = 0;
bool          g_focusReady=false;
int           g_focusRows=4,g_focusDockH=124,g_focusTableW=800;
uint          g_lastChartChgMs = 0;

//=== HUD v2: extended trade statistics ===
int           g_winCount  = 0;
int           g_lossCount = 0;
double        g_grossWin  = 0.0;
double        g_grossLoss = 0.0;
double        g_bestNet   = 0.0;
double        g_worstNet  = 0.0;
double        g_totalCommClosed = 0.0;
double        g_avgHoldSec = 0.0;
int           g_streak    = 0;
int           g_salvage   = 0;
int           g_cuts      = 0;
datetime      g_tD[8];
int           g_tSide[8];
double        g_tLot[8];
double        g_tGain[8];
double        g_tComm[8];
double        g_tProf[8];
double        g_tNet[8];
int           g_tN = 0;

int           selTicket   = -1;
int           selType     = -1;
double        selPrice    = 0.0;
int           selMagic    = 0;
string        selSymbol   = "";

bool IsMatchingOrderIdentity();

// Function prototypes
void   activateStrategyContext();
double findSwingPoints(ENUM_TIMEFRAMES tf, bool findHigh);
void   runStrategyTick(bool isBuy);
bool   placeEntry(bool isBuy);
double calculateStrategyLots(double entryPrice, double slPrice);
void   manageOpenPositions();
void   expireStalePendingOrders();
int    countOwnPositions();

//=== C2 prototypes ===
bool   IsMatchingOrder();
void   TagDeleteAll();

//=== HUD v2 prototypes ===
void   FocusGeometry(int width,int height);
void   HudCycleTheme();
void   EqCanvasDestroy();
void   PanelDraw(bool force);
double PanelRightGap();
double PanelBarSpacing(int count);
void   HudCreate();
void   HudLayout();
void   HudMoveAll();
void   HudTick(bool force);
void   RefreshStats();
void   EqPush(double v, datetime t);
void   EqDraw();

//=== Broker-data chart panel (display only; never sends/modifies orders) ===
#define PC_TABLE_BOTTOM_GAP 8 // Reclaim the former footer space for candles.
#define PC_NAME "GX9PC_chart"
#define PC_BUTTON "GX9PC_btn_"
CCanvas g_pc;
bool g_pcReady=false, g_pcSaved=false;
long g_pcOldLevels=0, g_pcOldForeground=0;
long g_pcOldMouseMove=0,g_pcOldMouseScroll=1;
bool g_pcMoveMode=false,g_pcDragging=false,g_pcManualY=false;
int g_pcDragX=0,g_pcDragY=0,g_pcRenderedBars=0;
double g_pcPanX=0.0,g_pcViewCenter=0.0,g_pcViewSpan=1.0;
double g_pcAutoLow=0.0,g_pcAutoHigh=1.0,g_pcLastVisiblePrice=0.0;
uint g_pcLastDragMs=0;
int g_pcX=0, g_pcY=0, g_pcW=0, g_pcH=0;
int g_pcBars=64, g_pcOffset=0, g_pcTradePage=0;
bool g_pcFitOrders=false;
datetime g_pcLatest=0;
double g_pcLow=0, g_pcHigh=1;
int g_pcTop=10, g_pcBottom=0, g_pcRight=0;
uint g_pcLastMs=0, g_pcQuoteSeenMs=0, g_pcLastTableClickMs=0;
datetime g_pcQuoteTime=0;
struct PanelLevel
  {
   int kind; // BUY, SELL, pending buy/sell, TP, SL
   double price;
   string text;
   color ink;
  };

bool PanelEnabled()
  {
   return showDashboardPanel && showLiveChartPanel && (!IsTesting() || IsVisualMode());
  }

// Preserve native appearance for panel fallback/removal.
ENUM_CHART_PROPERTY_INTEGER g_pcProps[15]={CHART_COLOR_BACKGROUND,CHART_COLOR_FOREGROUND,
   CHART_COLOR_CHART_UP,CHART_COLOR_CHART_DOWN,CHART_COLOR_CANDLE_BULL,CHART_COLOR_CANDLE_BEAR,
   CHART_COLOR_CHART_LINE,CHART_COLOR_BID,CHART_COLOR_ASK,CHART_COLOR_STOP_LEVEL,
   CHART_COLOR_VOLUME,CHART_COLOR_GRID,CHART_SHOW_PRICE_SCALE,CHART_SHOW_DATE_SCALE,CHART_SHOW_OHLC};
long g_pcPropValues[15];
bool g_pcAppearanceSaved=false;

// Hide non-dashboard objects without deleting the user's drawings.
string g_pcHiddenObjects[];
long g_pcHiddenMasks[];
uint g_pcLastObjectScan=0;

void PanelHideNativeObjects()
  {
   uint now=GetTickCount();
   if(g_pcLastObjectScan!=0 && now-g_pcLastObjectScan<500) return;
   g_pcLastObjectScan=now;
   // Discard records for objects their owner has deleted.
   for(int k=ArraySize(g_pcHiddenObjects)-1;k>=0;k--)
     {
      if(ObjectFind(0,g_pcHiddenObjects[k])>=0) continue;
      int last=ArraySize(g_pcHiddenObjects)-1;
      g_pcHiddenObjects[k]=g_pcHiddenObjects[last];
      g_pcHiddenMasks[k]=g_pcHiddenMasks[last];
      ArrayResize(g_pcHiddenObjects,last); ArrayResize(g_pcHiddenMasks,last);
     }
   for(int i=ObjectsTotal(0,0,-1)-1;i>=0;i--)
     {
      string name=ObjectName(0,i,0,-1);
      if(name==PC_NAME || StringFind(name,PC_BUTTON)==0 || StringFind(name,HUD_PREFIX)==0) continue;
      int found=-1;
      for(int j=0;j<ArraySize(g_pcHiddenObjects);j++)
         if(g_pcHiddenObjects[j]==name) { found=j; break; }
      if(found<0)
        {
         int n=ArraySize(g_pcHiddenObjects);
         if(ArrayResize(g_pcHiddenMasks,n+1)!=n+1) continue;
         if(ArrayResize(g_pcHiddenObjects,n+1)!=n+1) { ArrayResize(g_pcHiddenMasks,n); continue; }
         g_pcHiddenObjects[n]=name;
         g_pcHiddenMasks[n]=ObjectGetInteger(0,name,OBJPROP_TIMEFRAMES);
        }
      ObjectSetInteger(0,name,OBJPROP_TIMEFRAMES,OBJ_NO_PERIODS);
     }
  }

void PanelRestoreNativeObjects()
  {
   for(int i=0;i<ArraySize(g_pcHiddenObjects);i++)
      if(ObjectFind(0,g_pcHiddenObjects[i])>=0)
         ObjectSetInteger(0,g_pcHiddenObjects[i],OBJPROP_TIMEFRAMES,g_pcHiddenMasks[i]);
   ArrayResize(g_pcHiddenObjects,0); ArrayResize(g_pcHiddenMasks,0);
   g_pcLastObjectScan=0;
  }

void PanelHideNative()
  {
   if(!g_pcReady || !hideOriginalChart) return;
   PanelHideNativeObjects();
   ChartSetInteger(0,CHART_SHOW_TRADE_LEVELS,false);
   if(!g_pcAppearanceSaved)
     {
      for(int i=0;i<15;i++) g_pcPropValues[i]=ChartGetInteger(0,g_pcProps[i]);
      g_pcAppearanceSaved=true;
     }
   for(int c=0;c<12;c++) ChartSetInteger(0,g_pcProps[c],UiPanel());
   for(int v=12;v<15;v++) ChartSetInteger(0,g_pcProps[v],false);
  }

void PanelRestore()
  {
   PanelRestoreNativeObjects();
   if(g_pcAppearanceSaved)
     {
      for(int i=0;i<15;i++) ChartSetInteger(0,g_pcProps[i],g_pcPropValues[i]);
      g_pcAppearanceSaved=false;
     }
   if(!g_pcSaved) return;
   ChartSetInteger(0,CHART_SHOW_TRADE_LEVELS,g_pcOldLevels);
   ChartSetInteger(0,CHART_FOREGROUND,g_pcOldForeground);
   ChartSetInteger(0,CHART_EVENT_MOUSE_MOVE,g_pcOldMouseMove);
   ChartSetInteger(0,CHART_MOUSE_SCROLL,g_pcOldMouseScroll);
   g_pcSaved=false;
  }

void PanelDestroy()
  {
   g_pcDragging=false;
   if(g_pcReady) g_pc.Destroy();
   g_pcReady=false;
   ObjectsDeleteAll(0,PC_BUTTON);
   PanelRestore();
  }

int PanelPriceY(double price)
  {
   if(g_pcHigh<=g_pcLow) return g_pcBottom;
   double fraction=(g_pcHigh-price)/(g_pcHigh-g_pcLow);
   return (int)MathRound(g_pcTop+MathMax(0.0,MathMin(1.0,fraction))*(g_pcBottom-g_pcTop));
  }

int PanelBarX(int index,int count)
  {
   return 12+(int)MathRound((count-1-index+0.5)*PanelBarSpacing(count)+g_pcPanX*(g_pcRight-20));
  }

void PanelText(int x,int y,string text,color ink)
  {
   g_pc.TextOut(x,y,text,ColorToARGB(ink));
  }

void PanelDash(int y,color ink)
  {
   for(int x=10;x<g_pcRight;x+=9)
      g_pc.Line(x,y,(int)MathMin(x+4,g_pcRight),y,ColorToARGB(ink,150));
  }

void PanelButton(string key,string caption,int x,int y,int width)
  {
   string name=PC_BUTTON+key;
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,name,OBJPROP_XSIZE,width);
   ObjectSetInteger(0,name,OBJPROP_YSIZE,22);
   ObjectSetInteger(0,name,OBJPROP_BGCOLOR,UiBand());
   ObjectSetInteger(0,name,OBJPROP_COLOR,UiInk());
   ObjectSetInteger(0,name,OBJPROP_BORDER_COLOR,UiBorder());
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,8);
   ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,name,OBJPROP_ZORDER,50);
   ObjectSetInteger(0,name,OBJPROP_STATE,false);
   ObjectSetString(0,name,OBJPROP_TEXT,caption);
  }

// Camera controls only: no broker order/stop/target operations.
double PanelRightGap()
  {
   return MathMax(8.0,MathMin(45.0,chartRightSpacePct))/100.0;
  }

double PanelBarSpacing(int count)
  {
   if(count<=0) return 1.0;
   return (g_pcRight-20)*(1.0-PanelRightGap())/(double)count;
  }

void PanelToolbar()
  {
   bool compact=(g_chartW<1180);
   int x=g_px[2]+(compact?140:300),y=g_py[2]+(compact?38:7);
   string keys[10],captions[10],tips[10];
   int widths[10];ArrayInitialize(widths,24);
   keys[0]="in";captions[0]="+";tips[0]="Larger candles: fewer visible bars";
   keys[1]="out";captions[1]="-";tips[1]="Smaller candles: more visible bars";
   keys[2]="older";captions[2]="<";tips[2]="Older candle history";
   keys[3]="newer";captions[3]=">";tips[3]="Newer candle history";
   keys[4]="live";captions[4]="LIVE";widths[4]=40;tips[4]="Latest bars, automatic price scale and default right space";
   keys[5]="range";captions[5]=g_pcFitOrders?"ALL":"BARS";widths[5]=42;tips[5]="Reset auto scale: all order levels / candles only";
   keys[6]="move";captions[6]="MOVE";widths[6]=48;tips[6]="Toggle free pan: drag inside the candle plot horizontally or vertically";
   keys[7]="center";captions[7]="CENTER";widths[7]=58;tips[7]="Center the newest visible candle in the plot";
   keys[8]="vplus";captions[8]="Y+";widths[8]=28;tips[8]="Expand candles vertically (smaller price range)";
   keys[9]="vminus";captions[9]="Y-";widths[9]=28;tips[9]="Compress candles vertically (larger price range)";
   for(int i=0;i<10;i++)
     {
      PanelButton(keys[i],captions[i],x,y,widths[i]);
      ObjectSetString(0,PC_BUTTON+keys[i],OBJPROP_TOOLTIP,tips[i]);
      if(keys[i]=="move" && g_pcMoveMode)
        {
         ObjectSetInteger(0,PC_BUTTON+keys[i],OBJPROP_BGCOLOR,UiAccent());
         ObjectSetInteger(0,PC_BUTTON+keys[i],OBJPROP_COLOR,UiPanel());
        }
      x+=widths[i]+3;
     }
  }

void PanelVerticalZoom(double factor)
  {
   if(g_pcRenderedBars<2 || g_pcHigh<=g_pcLow) return;
   double automatic=MathMax(activeSymbolPoint*10,g_pcAutoHigh-g_pcAutoLow);
   g_pcViewCenter=(g_pcHigh+g_pcLow)*0.5;
   g_pcViewSpan=MathMax(automatic*0.15,MathMin(automatic*8.0,(g_pcHigh-g_pcLow)*factor));
   g_pcManualY=true;
  }

void PanelCenterView()
  {
   if(g_pcRenderedBars<2 || g_pcRight<=20) return;
   g_pcPanX=0.0;
   double midpoint=12+(g_pcRight-20)*0.5;
   g_pcPanX=(midpoint-PanelBarX(0,g_pcRenderedBars))/(g_pcRight-20);
   g_pcViewCenter=g_pcLastVisiblePrice;
   g_pcViewSpan=MathMax(activeSymbolPoint*10,g_pcHigh-g_pcLow);
   g_pcManualY=true;
  }

bool PanelMouseMove(int x,int y,int buttons)
  {
   if(!g_pcReady || !g_pcMoveMode) { g_pcDragging=false; return false; }
   bool down=((buttons & 1)!=0);
   if(!down)
     {
      bool wasDragging=g_pcDragging;g_pcDragging=false;
      if(wasDragging) PanelDraw(true);
      return wasDragging;
     }
   int left=g_pcX+12,right=g_pcX+g_pcRight-10;
   int top=g_pcY+g_pcTop,bottom=g_pcY+g_pcBottom;
   if(!g_pcDragging)
     {
      if(x<left || x>right || y<top || y>bottom || g_pcRenderedBars<2) return false;
      g_pcDragging=true;g_pcDragX=x;g_pcDragY=y;
      g_pcViewCenter=(g_pcLow+g_pcHigh)*0.5;
      g_pcViewSpan=g_pcHigh-g_pcLow;g_pcManualY=true;
      return true;
     }
   int nx=(int)MathMax(left,MathMin(right,x)),ny=(int)MathMax(top,MathMin(bottom,y));
   g_pcPanX+=(double)(nx-g_pcDragX)/MathMax(1,g_pcRight-20);
   // Retain a small gutter even at the rightmost pan position.
   g_pcPanX=MathMax(PanelRightGap()-0.95,MathMin(PanelRightGap()-0.03,g_pcPanX));
   g_pcViewCenter+=(double)(ny-g_pcDragY)*g_pcViewSpan/MathMax(1,bottom-top);
   if(nx!=g_pcDragX || ny!=g_pcDragY) g_pcLastDragMs=GetTickCount();
   g_pcDragX=nx;g_pcDragY=ny;
   if(GetTickCount()-g_pcLastMs>=30) PanelDraw(true);
   return true;
  }

void PanelAddLevel(PanelLevel &levels[],double price,string text,color ink,int kind)
  {
   if(price<=0) return;
   int n=ArraySize(levels);
   if(ArrayResize(levels,n+1)!=n+1) return;
   levels[n].kind=kind;
   levels[n].price=price;
   levels[n].text=text;
   levels[n].ink=ink;
  }

// Stable type colors, independent of floating P/L. Darker accents on Light.
color PanelLevelColor(int kind)
  {
   if(kind==0) return UiGood();
   if(kind==1) return UiBad();
   if(kind==2) return UiAmber();
   if(kind==3) return g_activeTheme==1?C'126,55,162':C'207,151,239';
   if(kind==4) return g_activeTheme==1?C'0,105,175':C'102,192,255';
   return g_activeTheme==1?C'173,73,15':C'255,155,87';
  }

string PanelLevelCaption(int kind)
  {
   if(kind==0) return "BUY";
   if(kind==1) return "SELL";
   if(kind==2) return "PENDING BUY";
   if(kind==3) return "PENDING SELL";
   if(kind==4) return "TP";
   return "SL";
  }

// Bounded 16px text slots in the right plot gutter, never on the price axis.
// Nearby levels of the same type share a label; full details stay in the tooltip.
void PanelLevelLabels(PanelLevel &levels[])
  {
   int kinds[128],counts[128],anchors[128];
   ArrayInitialize(kinds,-1);ArrayInitialize(counts,0);ArrayInitialize(anchors,0);
   int slots=(int)MathMax(0,MathMin(128,(g_pcBottom-g_pcTop-20)/16));
   int hidden=0;
   for(int i=0;i<ArraySize(levels);i++)
     {
      if(levels[i].price<g_pcLow || levels[i].price>g_pcHigh) continue;
      int target=PanelPriceY(levels[i].price),match=-1,best=-1,distance=100000;
      for(int j=0;j<slots;j++)
        {
         if(counts[j]>0 && kinds[j]==levels[i].kind && MathAbs(anchors[j]-target)<=8)
           { match=j;break; }
         int delta=(int)MathAbs(g_pcTop+8+j*16-target);
         if(counts[j]==0 && delta<distance) { best=j;distance=delta; }
        }
      if(match>=0) { counts[match]++;continue; }
      if(best<0) { hidden++;continue; }
      kinds[best]=levels[i].kind;counts[best]=1;anchors[best]=target;
     }
   for(int row=0;row<slots;row++)
     {
      if(counts[row]==0) continue;
      string label=PanelLevelCaption(kinds[row]);
      if(counts[row]>1) label+=" x"+IntegerToString(counts[row]);
      int y=g_pcTop+2+row*16,x=g_pcRight-12-g_pc.TextWidth(label);
      color ink=PanelLevelColor(kinds[row]);
      // Text only: no diagonal connectors. Horizontal order lines retain exact prices.
      g_pc.FillRectangle(x-2,y-1,g_pcRight-10,y+12,ColorToARGB(UiPanel()));
      PanelText(x,y,label,ink);
     }
   if(hidden>0)
     {
      string more="+"+IntegerToString(hidden)+" levels";
      int x=g_pcRight-12-g_pc.TextWidth(more),y=g_pcBottom-14;
      g_pc.FillRectangle(x-2,y-1,g_pcRight-10,y+12,ColorToARGB(UiPanel()));
      PanelText(x,y,more,UiDim());
     }
  }

string PanelOrderName(int type)
  {
   switch(type)
     {
      case OP_BUY: return "BUY";
      case OP_SELL: return "SELL";
      case OP_BUYSTOP: return "BUY STOP";
      case OP_SELLSTOP: return "SELL STOP";
      case OP_BUYLIMIT: return "BUY LIMIT";
      case OP_SELLLIMIT: return "SELL LIMIT";
     }
   return "";
  }

// Estimated net account-currency P/L from entry to the selected order's exit.
string PanelExitMoney(double exitPrice)
  {
   if(exitPrice<=0) return "Not set";
   // SymbolInfoDouble gives a price increment, not a guessed pip size.
   double tickSize=SymbolInfoDouble(OrderSymbol(),SYMBOL_TRADE_TICK_SIZE);
   double tickValue=SymbolInfoDouble(OrderSymbol(),SYMBOL_TRADE_TICK_VALUE);
   if(tickSize<=0 || tickValue<=0) return "N/A";
   int type=OrderType();
   bool buy=(type==OP_BUY || type==OP_BUYLIMIT || type==OP_BUYSTOP);
   double move=buy ? exitPrice-OrderOpenPrice() : OrderOpenPrice()-exitPrice;
   double net=move/tickSize*tickValue*OrderLots()+OrderSwap()-CommissionCost(OrderLots());
   return (net>=0?"+":"")+DoubleToString(net,2);
  }

// Session-local evidence of a successful trailing modification, not just an SL.
struct PanelTrailState
  {
   int ticket;
   double stop;
  };
PanelTrailState g_panelTrails[];

void PanelRememberTrail(int ticket,double stop)
  {
   if(ticket<=0 || stop<=0) return;
   int n=ArraySize(g_panelTrails);
   for(int i=0;i<n;i++)
      if(g_panelTrails[i].ticket==ticket) { g_panelTrails[i].stop=stop; return; }
   if(ArrayResize(g_panelTrails,n+1)!=n+1) return;
   g_panelTrails[n].ticket=ticket; g_panelTrails[n].stop=stop;
  }

void PanelPruneTrails()
  {
   for(int i=ArraySize(g_panelTrails)-1;i>=0;i--)
     {
      bool closed=!OrderSelect(g_panelTrails[i].ticket,SELECT_BY_TICKET,MODE_TRADES);
      if(!closed) closed=(OrderCloseTime()!=0);
      if(!closed) continue;
      int last=ArraySize(g_panelTrails)-1;
      g_panelTrails[i]=g_panelTrails[last];
      ArrayResize(g_panelTrails,last);
     }
  }

string PanelTrailMoney()
  {
   if(OrderType()!=OP_BUY && OrderType()!=OP_SELL) return "-";
   double stop=OrderStopLoss();
   if(stop<=0) return "-";
   for(int i=0;i<ArraySize(g_panelTrails);i++)
      if(g_panelTrails[i].ticket==OrderTicket())
        {
         // A manual/BE adjustment or removed SL must not be labelled as trailing.
         if(MathAbs(g_panelTrails[i].stop-stop)>activeSymbolPoint*0.5) return "-";
         return "ON "+PanelExitMoney(stop);
        }
   return "-";
  }

string PanelLiveMoney()
  {
   if(OrderType()!=OP_BUY && OrderType()!=OP_SELL) return "Pending";
   double net=OrderProfit()+OrderSwap()-CommissionCost(OrderLots());
   return (net>=0?"+":"")+DoubleToString(net,2);
  }

void PanelCell(int x,int y,int width,string text,color ink)
  {
   if(g_pc.TextWidth(text)>width-4)
     {
      while(StringLen(text)>1 && g_pc.TextWidth(text+"...")>width-4)
         text=StringSubstr(text,0,StringLen(text)-1);
      text+="...";
     }
   PanelText(x,y,text,ink);
  }

void PanelTradeTable()
  {
   PanelPruneTrails();
   int tickets[];
   int pendingTickets[];
   for(int i=0;i<OrdersTotal();i++)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderCloseTime()!=0 || !IsMatchingOrderIdentity()) continue;
      if(OrderType()<OP_BUY || OrderType()>OP_SELLSTOP) continue;
      if(OrderType()==OP_BUY || OrderType()==OP_SELL)
        {
         int n=ArraySize(tickets);
         if(ArrayResize(tickets,n+1)==n+1) tickets[n]=OrderTicket();
        }
      else
        {
         int n=ArraySize(pendingTickets);
         if(ArrayResize(pendingTickets,n+1)==n+1) pendingTickets[n]=OrderTicket();
        }
     }
   // Stable pagination even when the terminal reorders its trade pool.
   ArraySort(tickets);
   ArraySort(pendingTickets);
   // One ordered list: EVERY market position before ANY pending order.
   int totalRows=ArraySize(tickets)+ArraySize(pendingTickets);
   int pageRows=g_focusRows;
   int tableWidth=g_focusTableW;
   int pages=(int)MathMax(1,(totalRows+pageRows-1)/pageRows);
   g_pcTradePage=g_pcTradePage%pages;
   int tableTop=g_pcH-PC_TABLE_BOTTOM_GAP-g_focusDockH;
   g_pcBottom=tableTop-26;
   g_pc.FillRectangle(8,tableTop,tableWidth-1,g_pcH-PC_TABLE_BOTTOM_GAP+1,ColorToARGB(UiBand()));
   for(int band=0;band<pageRows;band++)
      if(band%2==0) g_pc.FillRectangle(8,tableTop+34+band*20,tableWidth-8,tableTop+53+band*20,ColorToARGB(UiPanel()));
   if(showEquityCurve)
     {
      g_pc.FillRectangle(tableWidth+12,tableTop,g_pcW-1,g_pcH-PC_TABLE_BOTTOM_GAP+1,ColorToARGB(UiPanel()));
      PanelText(tableWidth+24,tableTop+3,"CLOSED EQUITY",UiAccent());
      PanelCell(g_pcW-90,tableTop+3,80,(g_totalClosedPL>=0?"+":"")+DoubleToString(g_totalClosedPL,2),g_totalClosedPL>=0?UiGood():UiBad());
     }
   string currency=AccountCurrency();
   string unit=(currency=="USD")?"$":currency;
   string title="TRADES "+currency+" | OPEN "+IntegerToString(ArraySize(tickets))+
                " | PENDING "+IntegerToString(ArraySize(pendingTickets));
   PanelCell(12,tableTop+2,tableWidth-120,title,UiAccent());
   string section="PAGE "+IntegerToString(g_pcTradePage+1)+"/"+IntegerToString(pages);
   PanelText(tableWidth-100,tableTop+2,section,UiDim());
   int cols[8];
   cols[0]=12;cols[1]=12+(tableWidth-24)*16/100;cols[2]=12+(tableWidth-24)*34/100;
   cols[3]=12+(tableWidth-24)*42/100;cols[4]=12+(tableWidth-24)*56/100;
   cols[5]=12+(tableWidth-24)*70/100;cols[6]=12+(tableWidth-24)*84/100;cols[7]=tableWidth-12;
   string heads[7];
   heads[0]="TICKET";heads[1]="TYPE";heads[2]="LOTS";heads[3]="LIVE "+unit;
   heads[4]="TP~ "+unit;heads[5]="SL~ "+unit;heads[6]="TRAIL "+unit;
   for(int h=0;h<7;h++) PanelCell(cols[h],tableTop+18,cols[h+1]-cols[h],heads[h],UiDim());
   if(ArraySize(tickets)+ArraySize(pendingTickets)==0) PanelText(12,tableTop+36,"No matching trades",UiDim());
   for(int row=0;row<pageRows;row++)
     {
      int index=g_pcTradePage*pageRows+row;
      if(index>=totalRows) break;
      int ticket=0;
      if(index<ArraySize(tickets)) ticket=tickets[index];
      else ticket=pendingTickets[index-ArraySize(tickets)];
      if(!OrderSelect(ticket,SELECT_BY_TICKET,MODE_TRADES) || OrderCloseTime()!=0) continue;
      string values[7];
      values[0]=IntegerToString(OrderTicket()); values[1]=PanelOrderName(OrderType());
      values[2]=DoubleToString(OrderLots(),2);values[3]=PanelLiveMoney();
      values[4]=PanelExitMoney(OrderTakeProfit());values[5]=PanelExitMoney(OrderStopLoss());
      values[6]=PanelTrailMoney();
      for(int c=0;c<7;c++)
        {
         color ink=UiInk();
         if(c>=3 && StringFind(values[c],"+")==0) ink=UiGood();
         if(c>=3 && StringFind(values[c],"-")==0) ink=UiBad();
         if(c==6 && StringFind(values[c],"ON +")==0) ink=UiGood();
         if(c==6 && StringFind(values[c],"ON -")==0) ink=UiBad();
         if(OrderType()>OP_SELL && c==1) ink=UiAmber();
         PanelCell(cols[c],tableTop+36+row*20,cols[c+1]-cols[c],values[c],ink);
        }
     }

  }

void PanelDraw(bool force)
  {
   if(!PanelEnabled())
     {
      PanelDestroy();
      return;
     }
   uint nowMs=GetTickCount();
   if(!force && g_pcReady && nowMs-g_pcLastMs<200) return;
   g_pcLastMs=nowMs;
   // Use actual window size, not the HUD's minimum-size assumptions.
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int ch=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS);
   if(cw!=g_chartW || ch!=g_chartH) HudLayout();
   int x=g_px[3],y=g_py[3],w=g_pw[3],h=g_ph[3];
   // Fall back to native chart if there is not enough room for a readable panel.
   if(!g_focusReady || w<400 || h<160)
     {
      PanelDestroy();
      return;
     }
   if(!g_pcReady || w!=g_pcW || h!=g_pcH || x!=g_pcX || y!=g_pcY)
     {
      if(g_pcReady) g_pc.Destroy();
      EqCanvasDestroy(); // Recreate above the new full-width chart surface.
      ObjectsDeleteAll(0,PC_BUTTON); // Recreate controls above the new bitmap.
      g_pcReady=false;
      if(!g_pc.CreateBitmapLabel(0,0,PC_NAME,x,y,w,h,COLOR_FORMAT_ARGB_NORMALIZE))
        {
         Print("gold_x9: custom chart allocation failed: ",GetLastError());
         g_pc.Destroy(); // Also release partially allocated resources.
         PanelDestroy();
         return;
        }
      g_pcReady=true; g_pcX=x; g_pcY=y; g_pcW=w; g_pcH=h;
      g_pc.FontSet("Consolas",-90);
      ObjectSetInteger(0,PC_NAME,OBJPROP_BACK,false);
      ObjectSetInteger(0,PC_NAME,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,PC_NAME,OBJPROP_HIDDEN,true);
      if(!g_pcSaved)
        {
         g_pcOldLevels=ChartGetInteger(0,CHART_SHOW_TRADE_LEVELS);
         g_pcOldForeground=ChartGetInteger(0,CHART_FOREGROUND);
         g_pcOldMouseMove=ChartGetInteger(0,CHART_EVENT_MOUSE_MOVE);
         g_pcOldMouseScroll=ChartGetInteger(0,CHART_MOUSE_SCROLL);
         g_pcSaved=true;
        }
      ChartSetInteger(0,CHART_SHOW_TRADE_LEVELS,false);
      ChartSetInteger(0,CHART_FOREGROUND,false);
      ChartSetInteger(0,CHART_EVENT_MOUSE_MOVE,true);
      ChartSetInteger(0,CHART_MOUSE_SCROLL,g_pcMoveMode?false:g_pcOldMouseScroll);
      // Clear any legacy result objects; no result cards are drawn.
      ObjectsDeleteAll(0,TAG_PREFIX);
     }
   PanelHideNative();
   g_pc.Erase(ColorToARGB(UiPanel()));
   g_pcRight=w-83; g_pcBottom=h-52;
   PanelToolbar();

   PanelTradeTable();

   datetime latest=iTime(activeTradeSymbol,Period(),0);
   if(g_pcOffset>0 && latest!=g_pcLatest && g_pcLatest>0)
     {
      int delta=iBarShift(activeTradeSymbol,Period(),g_pcLatest,true);
      if(delta>0) g_pcOffset+=delta;
     }
   g_pcLatest=latest;
   int available=iBars(activeTradeSymbol,Period());
   g_pcOffset=(int)MathMax(0,MathMin(g_pcOffset,MathMax(0,available-10)));
   MqlRates rates[];
   ArraySetAsSeries(rates,true);
   int count=CopyRates(activeTradeSymbol,(ENUM_TIMEFRAMES)Period(),g_pcOffset,g_pcBars,rates);
   if(count<2)
     {
      g_pcRenderedBars=0;
      PanelText(15,65,"Waiting for broker candle history...",UiDim());
      g_pc.Update();EqDraw(); return;
     }
   g_pcRenderedBars=count;g_pcLastVisiblePrice=rates[0].close;
   // Use actual broker OHLC, including the forming candle. Never invent candles.
   g_pcLow=rates[0].low; g_pcHigh=rates[0].high;
   for(int i=1;i<count;i++)
     { g_pcLow=MathMin(g_pcLow,rates[i].low); g_pcHigh=MathMax(g_pcHigh,rates[i].high); }
   PanelLevel levels[];
   for(int pos=0;pos<OrdersTotal();pos++)
     {
      if(!OrderSelect(pos,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderCloseTime()!=0 || !IsMatchingOrderIdentity()) continue;
      int type=OrderType();
      if(type<OP_BUY || type>OP_SELLSTOP) continue;
      bool market=(type==OP_BUY || type==OP_SELL);
      string ticket="#"+IntegerToString(OrderTicket());
      string text=ticket+" "+PanelOrderName(type)+" "+DoubleToString(OrderLots(),2);
      text+=" LIVE "+PanelLiveMoney()+" TRAIL "+PanelTrailMoney();
      int kind=market?(type==OP_BUY?0:1):((type==OP_BUYSTOP || type==OP_BUYLIMIT)?2:3);
      PanelAddLevel(levels,OrderOpenPrice(),text,PanelLevelColor(kind),kind);
      PanelAddLevel(levels,OrderStopLoss(),ticket+" SL~ "+PanelExitMoney(OrderStopLoss()),PanelLevelColor(5),5);
      PanelAddLevel(levels,OrderTakeProfit(),ticket+" TP~ "+PanelExitMoney(OrderTakeProfit()),PanelLevelColor(4),4);
     }
   string detail="Amounts in "+AccountCurrency()+"; live P/L uses dashboard commission settings. TP/SL estimate net from entry, including current swap; future costs/slippage may differ.";
   for(int tip=0;tip<ArraySize(levels);tip++)
      detail+="\n"+levels[tip].text+" @"+DoubleToString(levels[tip].price,activeSymbolDigits);
   ObjectSetString(0,PC_NAME,OBJPROP_TOOLTIP,detail);
   MqlTick tick;
   bool quoted=SymbolInfoTick(activeTradeSymbol,tick) && tick.bid>0;
   if(quoted && (g_pcQuoteTime!=tick.time || g_pcQuoteSeenMs==0))
     { g_pcQuoteTime=tick.time; g_pcQuoteSeenMs=nowMs; }
   if(g_pcOffset==0 && quoted)
     { g_pcLow=MathMin(g_pcLow,tick.bid); g_pcHigh=MathMax(g_pcHigh,MathMax(tick.bid,tick.ask)); }
   if(g_pcFitOrders)
      for(int l=0;l<ArraySize(levels);l++)
        { g_pcLow=MathMin(g_pcLow,levels[l].price); g_pcHigh=MathMax(g_pcHigh,levels[l].price); }
   double pad=MathMax((g_pcHigh-g_pcLow)*0.08,activeSymbolPoint*10);
   g_pcLow-=pad; g_pcHigh+=pad;
   g_pcAutoLow=g_pcLow;g_pcAutoHigh=g_pcHigh;
   if(g_pcManualY)
     {
      g_pcLow=g_pcViewCenter-g_pcViewSpan*0.5;
      g_pcHigh=g_pcViewCenter+g_pcViewSpan*0.5;
     }
   for(int grid=0;grid<=4;grid++)
     {
      double price=g_pcLow+(g_pcHigh-g_pcLow)*grid/4.0;
      int gy=PanelPriceY(price);
      g_pc.Line(10,gy,g_pcRight,gy,ColorToARGB(UiBorder()));
      if(quoted && tick.bid>=g_pcLow && tick.bid<=g_pcHigh && MathAbs(gy-PanelPriceY(tick.bid))<16) continue;
      PanelText(g_pcRight+5,gy-6,DoubleToString(price,activeSymbolDigits),UiDim());
     }
   int body=(int)MathMax(1,MathMin(18,PanelBarSpacing(count)*0.7));
   int oldestVisible=-1,newestVisible=-1;
   for(int bar=count-1;bar>=0;bar--)
     {
      int bx=PanelBarX(bar,count);
      if(bx<12 || bx>g_pcRight-10) continue;
      if(oldestVisible<0) oldestVisible=bar;
      newestVisible=bar;
      if(rates[bar].high<g_pcLow || rates[bar].low>g_pcHigh) continue;
      uint ink=ColorToARGB(rates[bar].close>=rates[bar].open ? UiBull() : UiBear());
      g_pc.Line(bx,PanelPriceY(rates[bar].high),bx,PanelPriceY(rates[bar].low),ink);
      double bodyHigh=MathMax(rates[bar].open,rates[bar].close);
      double bodyLow=MathMin(rates[bar].open,rates[bar].close);
      if(bodyHigh<g_pcLow || bodyLow>g_pcHigh) continue;
      int top=PanelPriceY(bodyHigh);
      int bottom=(int)MathMin(g_pcBottom,MathMax(top+1,PanelPriceY(bodyLow)));
      g_pc.FillRectangle((int)MathMax(12,bx-body/2),top,
                        (int)MathMin(g_pcRight-10,bx+body/2),bottom,ink);
     }
   // Actual price-level lines; compact type labels are laid out separately.
   for(int line=0;line<ArraySize(levels);line++)
     {
      if(levels[line].price<g_pcLow || levels[line].price>g_pcHigh) continue;
      PanelDash(PanelPriceY(levels[line].price),levels[line].ink);
     }
   if(quoted && tick.bid>=g_pcLow && tick.bid<=g_pcHigh)
     {
      int by=PanelPriceY(tick.bid);
      PanelDash(by,UiAccent());
      g_pc.FillRectangle(g_pcRight+1,by-7,w-2,by+8,ColorToARGB(UiAccent()));
      PanelText(g_pcRight+4,by-6,DoubleToString(tick.bid,activeSymbolDigits),UiPanel());
     }
   PanelLevelLabels(levels);
   // Time labels follow visible candles after horizontal dragging; blank gutter stays blank.
   int labelEdge=-1000;
   if(oldestVisible>=0)
      for(int axis=0;axis<4;axis++)
        {
         int bar=oldestVisible-(oldestVisible-newestVisible)*axis/3;
         string stamp=TimeToString(rates[bar].time,axis==0?(TIME_DATE|TIME_MINUTES):TIME_MINUTES);
         int tw=g_pc.TextWidth(stamp);
         int tx=(int)MathMax(12,MathMin(g_pcRight-tw,PanelBarX(bar,count)-tw/2));
         if(tx<=labelEdge+8) continue;
         PanelText(tx,g_pcBottom+9,stamp,UiDim());labelEdge=tx+tw;
        }
   string feed=quoted ? "Tick "+TimeToString(tick.time,TIME_SECONDS) : "No quote";
   if(quoted && (TimeCurrent()-tick.time>60 || nowMs-g_pcQuoteSeenMs>60000)) feed+=" (STALE)";
   // Quote status and navigation help remain accessible on hover, not over the chart.
   string status=(g_pcOffset==0?"LIVE | ":"HISTORY | ")+feed;
   ObjectSetString(0,PC_NAME,OBJPROP_TOOLTIP,detail+"\n"+status+"\nClick the trade table for the next rows: all open positions first, then pending orders. LIVE returns to the beginning. Set chartTradeRows to change visible rows.");
   g_pc.Update();
   EqDraw();
  }

bool PanelClick(string name)
  {
   if(StringFind(name,PC_BUTTON)!=0) return false;
   string key=StringSubstr(name,StringLen(PC_BUTTON));
   if(key=="in") g_pcBars=(int)MathMax(16,g_pcBars-16);
   if(key=="out") g_pcBars=(int)MathMin(240,g_pcBars+16);
   if(key=="older") g_pcOffset+=g_pcBars/2;
   if(key=="newer") g_pcOffset=(int)MathMax(0,g_pcOffset-g_pcBars/2);
   g_pcDragging=false;
   if(key=="live") { g_pcOffset=0;g_pcTradePage=0;g_pcPanX=0;g_pcManualY=false; }
   if(key=="center") PanelCenterView();
   if(key=="vplus") PanelVerticalZoom(0.8);
   if(key=="vminus") PanelVerticalZoom(1.25);
   if(key=="move")
     {
      g_pcMoveMode=!g_pcMoveMode;
      ChartSetInteger(0,CHART_MOUSE_SCROLL,g_pcMoveMode?false:g_pcOldMouseScroll);
     }
   if(key=="range") { g_pcFitOrders=!g_pcFitOrders;g_pcManualY=false; }
   PanelDraw(true);
   ChartRedraw(0);
   return true;
  }

bool PanelTableClick(int x,int y)
  {
   if(!g_pcReady) return false;
   int tableTop=g_pcY+g_pcBottom+26;
   if(x<g_pcX+8 || x>=g_pcX+g_focusTableW-8 || y<tableTop || y>=g_pcY+g_pcH-PC_TABLE_BOTTOM_GAP+1) return false;
   uint now=GetTickCount();
   if(g_pcLastDragMs!=0 && now-g_pcLastDragMs<350) return true;
   // Some terminal builds send both object and chart click notifications.
   if(g_pcLastTableClickMs!=0 && now-g_pcLastTableClickMs<250) return true;
   g_pcLastTableClickMs=now;
   g_pcTradePage++;
   PanelDraw(true);
   ChartRedraw(0);
   return true;
  }

double SymbolAsk()         { return MarketInfo(activeTradeSymbol, MODE_ASK); }
double SymbolBid()         { return MarketInfo(activeTradeSymbol, MODE_BID); }
double SymbolPoint()       { return MarketInfo(activeTradeSymbol, MODE_POINT); }
int    SymbolDigits()      { return (int)MarketInfo(activeTradeSymbol, MODE_DIGITS); }
double SymbolStopsLevel()  { return MarketInfo(activeTradeSymbol, MODE_STOPLEVEL)   * activeSymbolPoint; }
double SymbolFreezeLevel() { return MarketInfo(activeTradeSymbol, MODE_FREEZELEVEL) * activeSymbolPoint; }
double SymbolVolumeMax()   { return MarketInfo(activeTradeSymbol, MODE_MAXLOT); }
double SymbolVolumeMin()   { return MarketInfo(activeTradeSymbol, MODE_MINLOT); }
double SymbolVolumeStep()  { return MarketInfo(activeTradeSymbol, MODE_LOTSTEP); }

bool SelectPending(int index)
  {
   selTicket = -1; selType = -1; selPrice = 0.0; selMagic = 0; selSymbol = "";
   if(index < 0 || index >= OrdersTotal()) return false;
   if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES)) return false;
   int type = OrderType();
   if(type != OP_BUYLIMIT && type != OP_SELLLIMIT && type != OP_BUYSTOP && type != OP_SELLSTOP) return false;
   selTicket = OrderTicket(); selType = type; selPrice = OrderOpenPrice(); selMagic = OrderMagicNumber(); selSymbol = OrderSymbol();
   return true;
  }

bool SelectOwnPosition(int index)
  {
   selTicket = -1; selType = -1; selPrice = 0.0; selMagic = 0; selSymbol = "";
   if(index < 0 || index >= OrdersTotal()) return false;
   if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES)) return false;
   int type = OrderType();
   if(type != OP_BUY && type != OP_SELL) return false;
   if(OrderMagicNumber() != activeMagicNumber) return false;
   if(OrderSymbol() != activeTradeSymbol) return false;
   selTicket = OrderTicket(); selType = type; selPrice = OrderOpenPrice(); selMagic = OrderMagicNumber(); selSymbol = OrderSymbol();
   return true;
  }

bool IsOwnPending(int wantedType)
  {
   if(selMagic != activeMagicNumber) return false;
   if(selSymbol != activeTradeSymbol) return false;
   if(wantedType >= 0 && selType != wantedType) return false;
   return true;
  }

int countOwnPositions()
  {
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(SelectOwnPosition(i)) count++;
   return count;
  }

double CommissionCost(double lots)
  {
   if(lots <= 0.0) return 0.0;
   return NormalizeDouble((lots / 0.01) * 0.07, 2);
  }

double NormalizeLots(double lots)
  {
   double minLot  = SymbolVolumeMin();
   double maxLot  = SymbolVolumeMax();
   double lotStep = SymbolVolumeStep();
   if(minLot  <= 0.0) minLot  = 0.01;
   if(maxLot  <= 0.0) maxLot  = maxLotCap;
   if(lotStep <= 0.0) lotStep = 0.01;
   if(maxLotCap > 0.0 && maxLot > maxLotCap) maxLot = maxLotCap;
   if(lots < minLot) lots = minLot;
   if(lots > maxLot) lots = maxLot;
   int stepDigits = 2;
   if(lotStep >= 1.0)      stepDigits = 0;
   else if(lotStep >= 0.1) stepDigits = 1;
   lots = MathFloor(lots / lotStep + 0.0000001) * lotStep;
   if(lots < minLot) lots = minLot;
   return NormalizeDouble(lots, stepDigits);
  }

double calculateStrategyLots(double entryPrice, double slPrice)
  {
   double lots = fixedLotSize;
   switch(lotSizingMethod)
     {
      case MANUAL_LOTS:
        {
         lots = fixedLotSize;
         if(riskScaleFactor > 0.0) lots = lots * (riskScaleFactor / 100.0);
         break;
        }
      case TIERED_LOTS:
        {
         double meter     = tieredLotsEffective;
         double tierMult  = MathPow(10.0, (meter - 1.0) / 99.0);
         lots = fixedLotSize * tierMult;
         if(riskScaleFactor > 0.0)    lots = lots * (riskScaleFactor / 100.0);
         if(strategyRiskWeight > 0.0) lots = lots * (strategyRiskWeight / weightedRiskDivider);
         break;
        }
      case RISK_SCALE_FACTOR:
        {
         double slDistance = MathAbs(entryPrice - slPrice);
         if(slDistance <= 0.0 || activeTickSize <= 0.0 || activeTickValue <= 0.0)
           { lots = fixedLotSize; break; }
         double riskPercent = (riskScaleFactor > 0.0) ? riskScaleFactor : 1.0;
         double riskMoney   = AccountEquity() * (riskPercent / 100.0);
         if(strategyRiskWeight > 0.0) riskMoney = riskMoney * strategyRiskWeight;
         double lossPerLot  = (slDistance / activeTickSize) * activeTickValue;
         if(lossPerLot <= 0.0) { lots = fixedLotSize; break; }
         lots = riskMoney / lossPerLot;
         break;
        }
      default:
         lots = fixedLotSize;
         break;
     }
   if(g_lotMultiplier > 0.0 && g_lotMultiplier != 1.0) lots = lots * g_lotMultiplier;
   return NormalizeLots(lots);
  }

void FixStops(int type, double price, double &sl, double &tp)
  {
   double minDist = activeStopLevel;
   if(minDist <= 0.0) minDist = activeSymbolPoint;
   bool isBuySide = (type == OP_BUYSTOP || type == OP_BUYLIMIT || type == OP_BUY);
   if(isBuySide)
     {
      if(sl > 0.0 && (price - sl) < minDist) sl = price - minDist;
      if(tp > 0.0 && (tp - price) < minDist) tp = price + minDist;
      if(sl > 0.0 && sl >= price) sl = 0.0;
      if(tp > 0.0 && tp <= price) tp = 0.0;
     }
   else
     {
      if(sl > 0.0 && (sl - price) < minDist) sl = price + minDist;
      if(tp > 0.0 && (price - tp) < minDist) tp = price - minDist;
      if(sl > 0.0 && sl <= price) sl = 0.0;
      if(tp > 0.0 && tp >= price) tp = 0.0;
     }
   sl = NormalizeDouble(sl, activeSymbolDigits);
   tp = NormalizeDouble(tp, activeSymbolDigits);
  }

bool InDeadWindow(datetime t)
  {
   int from = deadWindowFromHour; if(from < 0 || from > 23) from = 0;
   int to   = deadWindowToHour;   if(to   < 0 || to   > 23) to   = 0;
   if(from == to) return false;
   MqlDateTime dt; TimeToStruct(t, dt);
   if(from < to)  return (dt.hour >= from && dt.hour < to);
   return (dt.hour >= from || dt.hour < to);
  }

void LogDeadWindowSkip(datetime t)
  {
   MqlDateTime dt; TimeToStruct(t, dt);
   if(dt.hour == g_lastDeadWinLogH) return;
   g_lastDeadWinLogH = dt.hour;
   Print("gold_x9 LAB M2: entry skipped - dead window (", dt.hour, ":00 server).");
  }

void LogHaltSkip()
  {
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   if(dt.hour == g_lastHaltSkipLogH) return;
   g_lastHaltSkipLogH = dt.hour;
   Print("gold_x9 LAB M3: entry skipped - equity-curve halt (DD ", DoubleToString((g_peakEquityLab - AccountEquity()) / g_peakEquityLab * 100.0, 1), "% >= ", DoubleToString(equityCurveHaltPct, 1), "%).");
  }

int SendPendingOrder(int type, double lots, double price, double sl, double tp, datetime expiration)
  {
   if(enableDeadWindow && InDeadWindow(TimeCurrent()))
     { LogDeadWindowSkip(TimeCurrent()); return -1; }
   if(enableEquityCurveHalt && equityHaltMode == 0 && g_equityHalted && !g_probationWeek)
     { LogHaltSkip(); return -1; }

   int   slippagePoints = 30;
   color arrowColor = (type == OP_BUYSTOP || type == OP_BUYLIMIT) ? clrDodgerBlue : clrOrangeRed;

   for(int attempt = 0; attempt < 5; attempt++)
     {
      RefreshRates();
      double neededMargin = MarketInfo(activeTradeSymbol, MODE_MARGINREQUIRED) * lots;
      if(neededMargin > 0.0 && neededMargin > AccountFreeMargin())
        {
         Print("gold_x9: insufficient free margin. Needed ", DoubleToString(neededMargin, 2), " Free ", DoubleToString(AccountFreeMargin(), 2));
         return -1;
        }

      int ticket = OrderSend(activeTradeSymbol, type, lots, price, slippagePoints, sl, tp, activeComment, activeMagicNumber, expiration, arrowColor);
      if(ticket > 0) return ticket;

      int err = GetLastError();
      if(err == ERR_TRADE_CONTEXT_BUSY || err == ERR_REQUOTE || err == ERR_PRICE_CHANGED || err == ERR_OFF_QUOTES)
        { Sleep(300); ResetLastError(); continue; }

      Print("gold_x9: OrderSend failed. Type=", type, " Price=", DoubleToString(price, activeSymbolDigits), " SL=", DoubleToString(sl, activeSymbolDigits), " TP=", DoubleToString(tp, activeSymbolDigits), " Lots=", DoubleToString(lots, 2), " Error=", err, " (", ErrorDescription(err), ")");
      return -1;
     }
   Print("gold_x9: OrderSend exhausted retries for type ", type);
   return -1;
  }

string ErrorDescription(int code)
  {
   switch(code)
     {
      case 0:   return "No error";
      case 1:   return "No error but result unknown";
      case 2:   return "Common error";
      case 3:   return "Invalid trade parameters";
      case 4:   return "Trade server busy";
      case 6:   return "No connection with trade server";
      case 8:   return "Too frequent requests";
      case 64:  return "Account disabled";
      case 65:  return "Invalid account";
      case 128: return "Trade timeout";
      case 129: return "Invalid price";
      case 130: return "Invalid stops (too close to market)";
      case 131: return "Invalid trade volume";
      case 132: return "Market closed";
      case 133: return "Trade disabled";
      case 134: return "Not enough money";
      case 135: return "Price changed";
      case 136: return "Off quotes";
      case 137: return "Broker busy";
      case 138: return "Requote";
      case 139: return "Order locked";
      case 140: return "Buy only allowed";
      case 141: return "Too many requests";
      case 145: return "Modification denied (order too close to market)";
      case 146: return "Trade context busy";
      case 147: return "Expirations denied by broker";
      case 148: return "Too many open and pending orders";
      case 149: return "Hedge prohibited";
      default:  return "Unknown error " + IntegerToString(code);
     }
  }

int ParseSid(string comment)
  {
   for(int s = 1; s <= 9; s++)
      if(StringFind(comment, " S" + IntegerToString(s)) >= 0) return s;
   return 9;
  }


bool IsMatchingOrderIdentity()
  {
   // Shared reporting identity; pending levels use this without market-type gating.
   if(OrderSymbol() != activeTradeSymbol) return false;
   if(!tagOnlyMyMagic) return true;
   if(filterMatchMode == MATCH_ALL_SYMBOL) return true;

   bool magicMatch   = (OrderMagicNumber() == activeMagicNumber);
   string cmt        = OrderComment();
   string searchCmt  = tradeComment;
   bool commentMatch = false;
   if(searchCmt != "")
     {
      if(StringFind(cmt, searchCmt) >= 0) commentMatch = true;
      else if(StringFind(cmt, "gold X9") >= 0 || StringFind(cmt, "X9") >= 0) commentMatch = true;
     }

   if(filterMatchMode == MATCH_MAGIC_ONLY)     return magicMatch;
   if(filterMatchMode == MATCH_COMMENT_ONLY)   return commentMatch;
   return (magicMatch || commentMatch);
  }

bool IsMatchingOrder()
  {
   int t=OrderType();
   if(t!=OP_BUY && t!=OP_SELL) return false;
   return IsMatchingOrderIdentity();
  }

void TagDeleteAll()
  {
   ObjectsDeleteAll(0,TAG_PREFIX);
  }

//=== C2: smooth equity curve ===
#define EQ_PLOT_W 249
#define EQ_PLOT_H 85

void EqPush(double v, datetime t)
  {
   int idx = g_eqN % EQ_MAX;
   g_eqVal[idx] = v;
   g_eqT[idx]   = t;
   if(g_eqN==0) { g_eqRunningPeak=v; g_eqRunningEMA=v; }
   else
     {
      double alpha=2.0/(MathMax(1,MathMin(100,eqCurveEmaPeriod))+1.0);
      g_eqRunningEMA+=alpha*(v-g_eqRunningEMA);
      g_eqRunningPeak=MathMax(g_eqRunningPeak,v);
     }
   g_eqEMA[idx]=g_eqRunningEMA;
   g_eqDD[idx]=(g_eqRunningPeak>0)?MathMax(0.0,(g_eqRunningPeak-v)/g_eqRunningPeak*100.0):0.0;
   g_eqN++;
  }

int EqCount()
  {
   return (g_eqN < EQ_MAX) ? g_eqN : EQ_MAX;
  }

void EqItem(int k, double &v, datetime &t)
  {
   int base = (g_eqN > EQ_MAX) ? g_eqN - EQ_MAX : 0;
   int idx  = (base + k) % EQ_MAX;
   v = g_eqVal[idx];
   t = g_eqT[idx];
  }

CCanvas g_eqCanvas;
bool g_eqCanvasReady=false;
int g_eqCanvasX=0,g_eqCanvasY=0,g_eqCanvasW=0,g_eqCanvasH=0;

void EqCanvasDestroy()
  {
   if(g_eqCanvasReady) g_eqCanvas.Destroy();
   g_eqCanvasReady=false;
  }

void EqDraw()
  {
   if(!showEquityCurve || !showDashboardPanel || !g_focusReady) { EqCanvasDestroy(); return; }
   if(g_pw[4]<=0) return;
   int ox=g_px[4]+12,oy=g_py[4]+26;
   int width=g_pw[4]-24,height=g_ph[4]-34;
   if(width<100 || height<40) { EqCanvasDestroy(); return; }
   string name=HUD_PREFIX+"eq_curve";
   if(!g_eqCanvasReady || ObjectFind(0,name)<0 || ox!=g_eqCanvasX || oy!=g_eqCanvasY || width!=g_eqCanvasW || height!=g_eqCanvasH)
     {
      EqCanvasDestroy();
      // Remove the old disconnected rectangle-based curve objects.
      ObjectsDeleteAll(0,HUD_PREFIX+"eql");
      ObjectsDeleteAll(0,HUD_PREFIX+"eqf");
      if(!g_eqCanvas.CreateBitmapLabel(0,0,name,ox,oy,width,height,COLOR_FORMAT_ARGB_NORMALIZE))
        { g_eqCanvas.Destroy(); return; }
      g_eqCanvasReady=true;g_eqCanvasX=ox;g_eqCanvasY=oy;g_eqCanvasW=width;g_eqCanvasH=height;
      ObjectSetInteger(0,name,OBJPROP_BACK,false);
      ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
      ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
      g_eqCanvas.FontSet("Consolas",-80);
     }
   g_eqCanvas.Erase(ColorToARGB(UiPanel()));
   int kept=EqCount();
   int nUse=(int)MathMin(kept,MathMax(2,MathMin(96,eqCurveSamples)));
   if(nUse==0)
     {
      g_eqCanvas.TextOut(5,22,"No closed results",ColorToARGB(UiDim()));
      g_eqCanvas.Update();return;
     }
   double smooth[96],dd[96];
   ArrayInitialize(smooth,0.0);ArrayInitialize(dd,0.0);
   double low=1e18,high=-1e18,maxDD=0.0;
   int base=(g_eqN>EQ_MAX)?g_eqN-EQ_MAX:0;
   for(int i=0;i<nUse;i++)
     {
      int idx=(base+kept-nUse+i)%EQ_MAX;
      smooth[i]=g_eqEMA[idx];dd[i]=g_eqDD[idx];
      low=MathMin(low,smooth[i]);high=MathMax(high,smooth[i]);
      maxDD=MathMax(maxDD,dd[i]);
     }
   double pad=MathMax(0.01,(high-low)*0.08);
   low-=pad;high+=pad;
   double ddScale=MathMax(1.0,MathCeil(maxDD*10.0)/10.0);
   int period=(int)MathMax(1,MathMin(100,eqCurveEmaPeriod));
   g_eqCanvas.TextOut(4,0,"EMA("+IntegerToString(period)+")",ColorToARGB(UiCurve()));
   if(showEquityDDLine)
      g_eqCanvas.TextOut(85,0,"DD 0-"+DoubleToString(ddScale,1)+"%",ColorToARGB(equityDDLineColor));
   string tip="Closed results only. Equity EMA("+IntegerToString(period)+
      "): "+DoubleToString(smooth[nUse-1],2)+" "+AccountCurrency()+
      ". DD uses unsmoothed closed results from the running peak: "+DoubleToString(dd[nUse-1],2)+"%.";
   if(showEquityDDLine) tip+=" DD scale: 0% at top, "+DoubleToString(ddScale,1)+"% at bottom (separate from equity scale).";
   ObjectSetString(0,name,OBJPROP_TOOLTIP,tip);
   int left=4,right=width-5,top=18,bottom=height-9;
   int prevY=0,prevDD=0;
   for(int x=left;x<=right;x++)
     {
      double position=(double)(x-left)*(nUse-1)/(right-left);
      int segment=(int)MathMin(MathFloor(position),MathMax(0,nUse-2));
      double u=position-segment;
      // Smooth, bounded interpolation: no overshoot between EMA samples.
      double weight=u*u*(3.0-2.0*u);
      int next=(int)MathMin(segment+1,nUse-1);
      double value=smooth[segment]+(smooth[next]-smooth[segment])*weight;
      double drawdown=dd[segment]+(dd[next]-dd[segment])*weight;
      int y=top+(int)MathRound((high-value)/(high-low)*(bottom-top));
      int dy=top+(int)MathRound(drawdown/ddScale*(bottom-top));
      if(x>left)
        {
         g_eqCanvas.Line(x-1,prevY,x,y,ColorToARGB(UiCurve()));
         g_eqCanvas.Line(x-1,prevY+1,x,y+1,ColorToARGB(UiCurve()));
         if(showEquityDDLine) g_eqCanvas.Line(x-1,prevDD,x,dy,ColorToARGB(equityDDLineColor));
        }
      prevY=y;prevDD=dy;
     }
   g_eqCanvas.Update();
  }

// Closed-result curve: cached independently of chart result tags.
struct ClosedEquityDeal
  {
   int ticket;
   datetime closed;
   double net;
  };
ClosedEquityDeal g_eqHistory[];
bool g_eqHistoryReady=false;
double g_eqClosedBase=0.0;
datetime g_eqBaseTime=0;

void SeedEquityHistory()
  {
   int total=OrdersHistoryTotal();
   ClosedEquityDeal deals[];
   if(ArrayResize(deals,total)!=total) return;
   int count=0;
   double closedNet=0.0;
   for(int i=0;i<total;i++)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_HISTORY)) return; // Retry an incomplete snapshot.
      if(!IsMatchingOrder() || OrderCloseTime()<=0) continue;
      deals[count].ticket=OrderTicket();
      deals[count].closed=OrderCloseTime();
      deals[count].net=OrderProfit()+OrderSwap()-CommissionCost(OrderLots());
      closedNet+=deals[count].net;
      count++;
     }
   ArrayResize(deals,count);
   bool changed=(!g_eqHistoryReady || count!=ArraySize(g_eqHistory));
   if(!changed)
      for(int c=0;c<count;c++)
         if(deals[c].ticket!=g_eqHistory[c].ticket || deals[c].closed!=g_eqHistory[c].closed ||
            deals[c].net!=g_eqHistory[c].net) { changed=true; break; }
   if(!changed) return; // Floating equity, ticks and deposits alone cannot add samples.
   if(ArrayResize(g_eqHistory,count)!=count) return;
   for(int j=0;j<count;j++) g_eqHistory[j]=deals[j];
   if(!g_eqHistoryReady)
     {
      g_eqClosedBase=AccountBalance()-closedNet;
      g_eqBaseTime=TimeCurrent();
      g_eqHistoryReady=true;
     }
   // Terminal history is not guaranteed to be ordered. Sort only on a changed snapshot.
   for(int a=1;a<count;a++)
     {
      ClosedEquityDeal item=deals[a];
      int b=a-1;
      while(b>=0)
        {
         if(deals[b].closed<item.closed ||
            (deals[b].closed==item.closed && deals[b].ticket<=item.ticket)) break;
         deals[b+1]=deals[b]; b--;
        }
      deals[b+1]=item;
     }
   if(count>0 && g_eqBaseTime>=deals[0].closed) g_eqBaseTime=deals[0].closed-1;
   g_eqN=0;
   double cumulative=g_eqClosedBase;
   EqPush(cumulative,g_eqBaseTime);
   for(int d=0;d<count;d++)
     {
      cumulative+=deals[d].net;
      EqPush(cumulative,deals[d].closed);
     }
  }

int OnInit()
  {
   g_pcBars=(int)MathMax(16,MathMin(240,chartStartBars));
   g_pcOffset=(int)MathMax(0,chartStartOffset);
   g_pcFitOrders=chartStartFitOrders;
   int      resetOuterIndex;
   int      resetInnerIndex;
   datetime nowDateTime;

   tieredLotsEffective = tieredLotRiskMeter;
   if(tieredLotsEffective > 100.0) tieredLotsEffective = 100.0;
   if(tieredLotsEffective <= 0.0)  tieredLotsEffective = 1.0;

   activeComment       = tradeComment + " S9";
   if(StringLen(activeComment) > 28)
      activeComment = StringSubstr(activeComment, 0, 28);
   activeMagicNumber   = inputMagicNumber;
   activeTradeSymbol   = Symbol();
   activeSymbolPoint   = SymbolPoint();
   activeSymbolDigits  = SymbolDigits();
   activePipFactor     = activeSymbolPoint;

   if(activeSymbolPoint <= 0.0 || activeSymbolDigits <= 0)
     {
      Print("gold_x9: symbol ", activeTradeSymbol, " not ready at init (point=", activeSymbolPoint, ")");
      return(INIT_FAILED);
     }

   if(activeSymbolDigits == 3 || activeSymbolDigits == 5)
      activePipFactor = activeSymbolPoint * 10.0;
   else if(activeSymbolDigits == 1)
      activePipFactor = activeSymbolPoint / 10.0;

   Spread            = SymbolAsk() - SymbolBid();
   activeStopLevel   = SymbolStopsLevel();
   activeFreezeLevel = SymbolFreezeLevel();

   activeTickSize  = MarketInfo(activeTradeSymbol, MODE_TICKSIZE);
   activeTickValue = MarketInfo(activeTradeSymbol, MODE_TICKVALUE);
   if(activeTickSize <= 0.0) activeTickSize = activeSymbolPoint;

   activeFractalTimeFrame  = fractalTimeFrame;
   activeRescanTimeFrame   = rescanMinutes;
   activeFractalRight      = fractalRight;
   activeFractalLeft       = fractalLeft;
   activeMaxSearch         = fractalMaxSearch;
   activeMaxPending        = maxPendingOrders;
   activeDuplicateDistance = (double)duplicatePointDistance * activePipFactor;
   activeExpiryHours       = pendingExpiryHours;
   activeExitTimeFrame     = exitTimeFrame;
   activeMaxPositions      = maxOpenPositions;

   activateStrategyContext();

   if(stopLossDistance <= 0)
     {
      stopLossDistance = activeSymbolPoint;
      tpDistance = activeSymbolPoint;
     }

   activeBreakEvenLockPct = breakEvenLockPct;
   if(activeBreakEvenLockPct >= breakEvenTriggerPct)
      activeBreakEvenLockPct = breakEvenTriggerPct / 2.0;
   if(activeBreakEvenLockPct < 0.0)
      activeBreakEvenLockPct = 0.0;

   if(trailDistance != 0 && trailDistance < activeFreezeLevel) trailDistance = activeFreezeLevel;
   if(trailDistance < activeStopLevel) trailDistance = activeStopLevel;
   if(stopLossDistance < activeStopLevel * 2.0) stopLossDistance = activeStopLevel * 2.0;

   if(activeFractalRight < 1) activeFractalRight = 1;
   if(activeFractalLeft  < 1) activeFractalLeft  = 1;
   if(fractalMinDistance < 0.1) fractalMinDistance = 0.1;
   if(activeMaxPositions < 1)   activeMaxPositions = 1;
   if(activeMaxPending   < 1)   activeMaxPending   = 1;

   pendingExpirySeconds = activeExpiryHours * 3600;
   if(activeExpiryHours > 0) pendingExpiry = TimeCurrent() + (int)pendingExpirySeconds;
   else pendingExpiry = 0;

   if(virtualExpiration) pendingExpiry = 0;

   findSwingPoints(activeFractalTimeFrame, true);
   findSwingPoints(activeFractalTimeFrame, false);

   lastSwingHigh = NormalizeDouble(lastSwingHigh, activeSymbolDigits);
   lastSwingLow  = NormalizeDouble(lastSwingLow,  activeSymbolDigits);

   double brokerMaxVol = SymbolVolumeMax();
   if(brokerMaxVol > 0.0 && maxLotCap > brokerMaxVol) maxLotCap = brokerMaxVol;

   for(resetOuterIndex = 0; resetOuterIndex < virtualStopLossStoreSize; resetOuterIndex++)
      for(resetInnerIndex = 0; resetInnerIndex < 2; resetInnerIndex++)
         virtualStopLossStore[resetOuterIndex][resetInnerIndex] = 0.0;

   for(resetOuterIndex = 0; resetOuterIndex < 100; resetOuterIndex++)
      for(resetInnerIndex = 0; resetInnerIndex < 2; resetInnerIndex++)
         orderPriceMap[resetOuterIndex][resetInnerIndex] = 0.0;

   nowDateTime = TimeCurrent();
   MqlDateTime dt; TimeToStruct(nowDateTime, dt);
   lastHour = dt.hour;

   perStrategyPendingRescanBars = 0;
   perStrategyRescanBars        = 0;

   lastFractalScanTime = 0;
   lastExitManageTime  = 0;

   strategyLots = calculateStrategyLots(SymbolBid(), SymbolBid() - stopLossDistance);

   g_activeTheme=(int)hudTheme;
   if(g_activeTheme<0||g_activeTheme>3)g_activeTheme=HUD_GRAPHITE;
   if(applyChartStyle) ApplyChartStyle();

   g_dayKey            = 0;
   g_ddHalted          = false;

   g_peakEquityLab     = 0.0;
   g_equityHalted      = false;
   g_probationWeek     = false;
   g_lotMultiplier     = 1.0;
   g_lastWeekKey       = -1;
   g_lastDeadWinLogH   = -1;
   g_lastHaltSkipLogH  = -1;
   for(int pk = 0; pk < 200; pk++) g_partialKeys[pk] = "";

   RefreshStats();

   ObjectsDeleteAll(0, HUD_PREFIX);
   if(showDashboardPanel)
     {
      HudLayout();
      HudCreate();
      HudLayout();
     }

   if(showEquityCurve) SeedEquityHistory();

   // Remove legacy EA result cards even when old presets kept them on exit.
   TagDeleteAll();

   HudTick(true);
   EqDraw();
   PanelDraw(true);
   if(PanelEnabled()) EventSetTimer(1);

   Print("gold_x9 v6.74 (MQL4) initialised on ", activeTradeSymbol, " digits=", activeSymbolDigits, " point=", DoubleToString(activeSymbolPoint, activeSymbolDigits), " result boxes=removed", " hud=", (showDashboardPanel ? "on" : "off"));
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   PanelDestroy();
   EqCanvasDestroy();
   ObjectsDeleteAll(0, HUD_PREFIX);
   TagDeleteAll();
   ChartRedraw(0);
  }

void OnTimer()
  {
   // Refresh counts even if an order changes between market ticks.
   // Display only: no order-management calls from the timer.
   HudTick(false);
   PanelDraw(false);
  }

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
  {
   if(id==CHARTEVENT_MOUSE_MOVE)
     { PanelMouseMove((int)lparam,(int)dparam,(int)StringToInteger(sparam)); return; }
   if(id==CHARTEVENT_OBJECT_CLICK && PanelClick(sparam)) return;
   if((id==CHARTEVENT_CLICK || (id==CHARTEVENT_OBJECT_CLICK && sparam==PC_NAME))
      && PanelTableClick((int)lparam,(int)dparam)) return;
   if(id==CHARTEVENT_OBJECT_CLICK && sparam==HUD_PREFIX+"theme_cycle")
     { HudCycleTheme(); return; }
   if(id!=CHARTEVENT_CHART_CHANGE)return;
   uint ms=GetTickCount();
   if(ms-g_lastChartChgMs<200)return;
   g_lastChartChgMs=ms;
   if(showDashboardPanel){HudLayout();EqDraw();}
   PanelDraw(true);
  }

void OnTick()
  {
   activateStrategyContext();
   TrackEquityAndDD();
   HudTick(false);
   PanelDraw(false);

   datetime now = TimeCurrent();
   int exitIntervalSeconds = PeriodSeconds(activeExitTimeFrame);
   if(exitIntervalSeconds < 1) exitIntervalSeconds = 60;

   if(lastExitManageTime == 0 || (now - lastExitManageTime) >= exitIntervalSeconds)
     {
      lastExitManageTime = now;
      expireStalePendingOrders();
      manageOpenPositions();
     }

   if(g_ddHalted) return;
   if(countOwnPositions() >= activeMaxPositions) return;

   int rescanSeconds = activeRescanTimeFrame * 60;
   if(rescanSeconds < 1) rescanSeconds = 60;
   if(lastFractalScanTime != 0 && (now - lastFractalScanTime) < rescanSeconds) return;
   lastFractalScanTime = now;

   runStrategyTick(true);
   runStrategyTick(false);
  }

void activateStrategyContext()
  {
   Spread            = SymbolAsk() - SymbolBid();
   activeStopLevel   = SymbolStopsLevel();
   activeFreezeLevel = SymbolFreezeLevel();

   double refPrice = SymbolBid();
   if(refPrice <= 0.0) refPrice = SymbolAsk();

   fractalMinDistance = (minFractalClearancePct / 100.0) * refPrice;
   buyEntryOffset     = (buyEntryOffsetPct      / 100.0) * refPrice;
   sellEntryOffset    = (sellEntryOffsetPct     / 100.0) * refPrice;
   stopLossDistance   = (stopLossPct            / 100.0) * refPrice;
   tpDistance         = (takeProfitPct          / 100.0) * refPrice;
   trailDistance      = (trailDistancePct       / 100.0) * refPrice;
  }

double findSwingPoints(ENUM_TIMEFRAMES tf, bool findHigh)
  {
   bool   found = false;
   int    barIndex = activeFractalLeft + 1;
   double candidateExtreme = 0.0;
   int    candidateBar = 0;
   double historicalExtreme = 0.0;
   double normalizedPrice = 0.0;
   bool   duplicateFound = false;
   int    newerScan, olderScan, h, i;
   bool   olderOk, newerOk;
   double currentAsk, currentBid, targetPrice;
   int    totalOrders;
   int    barsAvailable = Bars(activeTradeSymbol, tf);

   do
     {
      olderOk = true; newerOk = true;
      if(barsAvailable > 0 && barIndex + MathMax(activeFractalRight, activeFractalLeft) >= barsAvailable)
         break;

      for(newerScan = barIndex - 1; newerScan >= barIndex - activeFractalLeft; newerScan--)
        {
         if(findHigh) { if(iHigh(activeTradeSymbol, tf, newerScan) >= iHigh(activeTradeSymbol, tf, barIndex)) newerOk = false; }
         else         { if(iLow(activeTradeSymbol, tf, newerScan)  <= iLow(activeTradeSymbol, tf, barIndex))  newerOk = false; }
        }

      for(olderScan = barIndex + 1; olderScan <= barIndex + activeFractalRight; olderScan++)
        {
         if(findHigh) { if(iHigh(activeTradeSymbol, tf, olderScan) >= iHigh(activeTradeSymbol, tf, barIndex)) olderOk = false; }
         else         { if(iLow(activeTradeSymbol, tf, olderScan)  <= iLow(activeTradeSymbol, tf, barIndex))  olderOk = false; }
        }

      currentAsk = SymbolAsk();
      currentBid = SymbolBid();

      if(newerOk && olderOk)
        {
         if(findHigh && (iHigh(activeTradeSymbol, tf, barIndex) < currentAsk + fractalMinDistance))
            newerOk = false;
         if(!findHigh && (iLow(activeTradeSymbol, tf, barIndex) > currentBid - fractalMinDistance))
            newerOk = false;
        }

      if(newerOk && olderOk)
        {
         candidateExtreme  = findHigh ? iHigh(activeTradeSymbol, tf, barIndex) : iLow(activeTradeSymbol, tf, barIndex);
         candidateBar      = barIndex;
         historicalExtreme = findHigh ? iHigh(activeTradeSymbol, tf, 0)        : iLow(activeTradeSymbol, tf, 0);

         for(h = 1; h < candidateBar; h++)
           {
            if(findHigh && iHigh(activeTradeSymbol, tf, h) > historicalExtreme) historicalExtreme = iHigh(activeTradeSymbol, tf, h);
            if(!findHigh && iLow(activeTradeSymbol, tf, h) < historicalExtreme) historicalExtreme = iLow(activeTradeSymbol, tf, h);
           }

         if((findHigh && candidateExtreme >= historicalExtreme) || (!findHigh && candidateExtreme <= historicalExtreme))
           {
            normalizedPrice = NormalizeDouble(candidateExtreme, activeSymbolDigits);
            duplicateFound = false;
            totalOrders    = OrdersTotal();
            for(i = 0; i < totalOrders; i++)
              {
               if(SelectPending(i))
                 {
                  if(IsOwnPending(-1))
                    {
                     if(findHigh && selType == OP_BUYSTOP)
                       {
                        targetPrice = normalizedPrice + buyEntryOffset;
                        if(MathAbs(selPrice - targetPrice) < activeDuplicateDistance) { duplicateFound = true; break; }
                       }
                     else if(!findHigh && selType == OP_SELLSTOP)
                       {
                        targetPrice = normalizedPrice - sellEntryOffset;
                        if(MathAbs(selPrice - targetPrice) < activeDuplicateDistance) { duplicateFound = true; break; }
                       }
                    }
                 }
              }

            if(!duplicateFound)
              {
               found = true;
               if(findHigh) lastSwingHigh = normalizedPrice;
               else         lastSwingLow  = normalizedPrice;
               break;
              }
           }
        }
      barIndex++;
     }
   while(!found && barIndex < activeMaxSearch);

   if(!found)
     {
      if(findHigh) lastSwingHigh = 0.0;
      else         lastSwingLow  = 0.0;
     }
   return findHigh ? lastSwingHigh : lastSwingLow;
  }

void runStrategyTick(bool isBuy)
  {
   placeEntry(isBuy);
  }

bool placeEntry(bool isBuy)
  {
   int    pendingType = isBuy ? OP_BUYSTOP : OP_SELLSTOP;
   double swingPrice  = findSwingPoints(activeFractalTimeFrame, isBuy);
   if(swingPrice <= 0.0) return false;

   int pendingCount = 0;
   int totalOrders  = OrdersTotal();
   for(int i = 0; i < totalOrders; i++)
      if(SelectPending(i))
         if(IsOwnPending(pendingType)) pendingCount++;

   if(pendingCount >= activeMaxPending) return false;

   double entryPrice = isBuy ? NormalizeDouble(lastSwingHigh + buyEntryOffset, activeSymbolDigits) : NormalizeDouble(lastSwingLow - sellEntryOffset, activeSymbolDigits);

   if(entryAdjustment != 0.0) entryPrice = NormalizeDouble(entryPrice + entryAdjustment * activeSymbolPoint, activeSymbolDigits);

   datetime orderExpiration = 0;
   if(pendingExpiryHours > 0 && !virtualExpiration) orderExpiration = TimeCurrent() + pendingExpiryHours * 3600;

   double slPrice = isBuy ? NormalizeDouble(entryPrice - stopLossDistance, activeSymbolDigits) : NormalizeDouble(entryPrice + stopLossDistance, activeSymbolDigits);
   double tpPrice = isBuy ? NormalizeDouble(entryPrice + tpDistance, activeSymbolDigits) : NormalizeDouble(entryPrice - tpDistance, activeSymbolDigits);

   if(stopLossAdjustment != 0.0) slPrice = NormalizeDouble(slPrice + stopLossAdjustment * activeSymbolPoint, activeSymbolDigits);
   if(tpAdjustment != 0.0)       tpPrice = NormalizeDouble(tpPrice + tpAdjustment * activeSymbolPoint, activeSymbolDigits);

   FixStops(pendingType, entryPrice, slPrice, tpPrice);

   double lots = calculateStrategyLots(entryPrice, slPrice);
   if(lots <= 0.0) return false;
   strategyLots = lots;

   int ticket = SendPendingOrder(pendingType, lots, entryPrice, slPrice, tpPrice, orderExpiration);
   if(ticket < 0 && orderExpiration > 0 && GetLastError() == 147)
     {
      ResetLastError();
      ticket = SendPendingOrder(pendingType, lots, entryPrice, slPrice, tpPrice, 0);
     }

   if(ticket > 0)
     {
      lastTradeTicket = ticket;
      for(int m = 0; m < 100; m++)
        {
         if(orderPriceMap[m][0] == 0.0)
           {
            orderPriceMap[m][0] = (double)lastTradeTicket;
            orderPriceMap[m][1] = entryPrice;
            break;
           }
        }
      return true;
     }
   return false;
  }

void expireStalePendingOrders()
  {
   if(activeExpiryHours <= 0) return;
   datetime now     = TimeCurrent();
   datetime lifetime = (datetime)(activeExpiryHours * 3600);

   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      if(!SelectPending(i)) continue;
      if(!IsOwnPending(-1)) continue;
      if(!OrderSelect(selTicket, SELECT_BY_TICKET, MODE_TRADES)) continue;
      if(OrderExpiration() > 0) continue;

      if(now - OrderOpenTime() >= lifetime)
        {
         if(!OrderDelete(selTicket, clrGray))
            Print("gold_x9: OrderDelete failed. Ticket=", selTicket, " Error=", GetLastError(), " (", ErrorDescription(GetLastError()), ")");
         else
            Print("gold_x9: expired pending order deleted. Ticket=", selTicket, " AgeHours=", (int)((now - OrderOpenTime()) / 3600));
        }
     }
  }

bool PartialKeyExists(string key)
  {
   for(int i = 0; i < 200; i++)
      if(g_partialKeys[i] == key) return true;
   return false;
  }

void PartialKeyAdd(string key)
  {
   for(int i = 0; i < 200; i++)
     {
      if(g_partialKeys[i] == "")
        {
         g_partialKeys[i] = key;
         return;
        }
     }
   g_partialKeys[199] = key;
  }

void manageOpenPositions()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      if(!SelectOwnPosition(i)) continue;
      if(!OrderSelect(selTicket, SELECT_BY_TICKET, MODE_TRADES)) continue;

      int    type     = OrderType();
      double openPr   = OrderOpenPrice();
      double curSL    = OrderStopLoss();
      double curTP    = OrderTakeProfit();
      bool   isBuy    = (type == OP_BUY);

      double exitPrice = isBuy ? SymbolBid() : SymbolAsk();
      if(exitPrice <= 0.0 || openPr <= 0.0) continue;

      double move          = isBuy ? (exitPrice - openPr) : (openPr - exitPrice);
      double favorablePct  = (move / openPr) * 100.0;
      double lossPct       = (-move / openPr) * 100.0;

      double newSL = curSL;
      double newTP = curTP;
      bool   changed = false;
      bool   trailChanged = false;

      if(enableAgedLossCut)
        {
         double ageHours     = (TimeCurrent() - OrderOpenTime()) / 3600.0;
         bool   profitLocked = isBuy ? (curSL >= openPr) : (curSL > 0.0 && curSL <= openPr);
         if(ageHours >= agedLossHours && lossPct >= agedLossMinLossPct && !profitLocked)
           {
            double svTPx = isBuy ? openPr - (openPr * salvagePct / 100.0) : openPr + (openPr * salvagePct / 100.0);
            svTPx = NormalizeDouble(svTPx, activeSymbolDigits);
            bool salvageArmed = (curTP > 0.0 && MathAbs(curTP - svTPx) < 2.0 * activeSymbolPoint);
            if(!salvageArmed)
              {
               newTP = svTPx; changed = true;
               Print("gold_x9 LAB M1: aged loss ticket=", selTicket, " (", DoubleToString(ageHours, 1), "h, -", DoubleToString(lossPct, 3), "%) - salvage armed late.");
              }
            else
              {
               double closedPL = OrderProfit() + OrderSwap() + OrderCommission();
               RefreshRates();
               if(OrderClose(selTicket, OrderLots(), exitPrice, 30, clrRed))
                  Print("gold_x9 LAB M1: aged-loss cut (held ", DoubleToString(ageHours, 1), "h, P/L ", DoubleToString(closedPL, 2), "). Ticket=", selTicket);
               else
                  Print("gold_x9 LAB M1: aged-loss cut FAILED ticket=", selTicket, " error=", GetLastError());
               continue;
              }
           }
        }

      double beTrigger = breakEvenTriggerPct + breakEvenAdjustment;
      if(favorablePct >= beTrigger)
        {
         double bePrice = isBuy ? openPr + (openPr * activeBreakEvenLockPct / 100.0) : openPr - (openPr * activeBreakEvenLockPct / 100.0);
         bePrice = NormalizeDouble(bePrice, activeSymbolDigits);
         if(isBuy  && bePrice > newSL) { newSL = bePrice; changed = true; }
         if(!isBuy && (newSL <= 0.0 || bePrice < newSL)) { newSL = bePrice; changed = true; }
        }

      double trTrigger = trailTriggerPct + trailAdjustment;
      if(favorablePct >= trTrigger && favorablePct <= maxTrailPct)
        {
         double trDistance = (exitPrice * trailDistancePct / 100.0);
         if(enableMidTargetTrail)
           {
            double stagePct = (favorablePct >= midTargetPct) ? trailDistanceAfterMidPct : trailDistanceWidePct;
            trDistance = (exitPrice * stagePct / 100.0);
           }
         if(trDistance < activeStopLevel)   trDistance = activeStopLevel;
         if(trDistance < activeFreezeLevel) trDistance = activeFreezeLevel;

         double trSL = isBuy ? exitPrice - trDistance : exitPrice + trDistance;
         trSL = NormalizeDouble(trSL, activeSymbolDigits);

         if(isBuy  && trSL > newSL) { newSL = trSL; changed = true; trailChanged = true; }
         if(!isBuy && (newSL <= 0.0 || trSL < newSL)) { newSL = trSL; changed = true; trailChanged = true; }
        }

      double svTrigger = salvageTriggerPct + salvageAdjustment;
      if(svTrigger > 0.0 && lossPct >= svTrigger)
        {
         double svTP = isBuy ? openPr - (openPr * salvagePct / 100.0) : openPr + (openPr * salvagePct / 100.0);
         svTP = NormalizeDouble(svTP, activeSymbolDigits);
         if(isBuy  && (curTP <= 0.0 || svTP < curTP)) { newTP = svTP; changed = true; }
         if(!isBuy && (curTP <= 0.0 || svTP > curTP)) { newTP = svTP; changed = true; }
        }

      if(enablePartialPay && favorablePct >= midTargetPct)
        {
         string pkey = IntegerToString((int)OrderOpenTime()) + "_" + DoubleToString(openPr, activeSymbolDigits);
         if(!PartialKeyExists(pkey))
           {
            double lotStep  = MarketInfo(activeTradeSymbol, MODE_LOTSTEP);
            double minLot   = MarketInfo(activeTradeSymbol, MODE_MINLOT);
            double openLots = OrderLots();
            double halfLot  = 0.0;
            if(lotStep > 0.0) halfLot = NormalizeDouble(MathFloor(openLots / 2.0 / lotStep) * lotStep, 2);
            if(lotStep > 0.0 && halfLot >= minLot && (openLots - halfLot) >= minLot)
              {
               RefreshRates();
               if(OrderClose(selTicket, halfLot, exitPrice, 30, clrGold))
                 {
                  PartialKeyAdd(pkey);
                  Print("gold_x9 LAB M4b: partial pay at mid target. Ticket=", selTicket, " closed ", DoubleToString(halfLot, 2), " lots at +", DoubleToString(favorablePct, 3), "%.");
                  continue;
                 }
               else
                  Print("gold_x9 LAB M4b: partial close FAILED ticket=", selTicket, " error=", GetLastError());
              }
            else
               PartialKeyAdd(pkey);
           }
        }

      if(!changed) continue;

      int asPendingType = isBuy ? OP_BUY : OP_SELL;
      FixStops(asPendingType, exitPrice, newSL, newTP);

      if(MathAbs(newSL - curSL) < activeSymbolPoint && MathAbs(newTP - curTP) < activeSymbolPoint)
         continue;

      if(!OrderModify(selTicket, openPr, newSL, newTP, OrderExpiration(), clrAqua))
        {
         int err = GetLastError();
         if(err != 1)
            Print("gold_x9: OrderModify failed. Ticket=", selTicket, " SL=", DoubleToString(newSL, activeSymbolDigits), " TP=", DoubleToString(newTP, activeSymbolDigits), " Error=", err, " (", ErrorDescription(err), ")");
        }
      else
        {
         if(trailChanged && newSL>0 &&
            ((isBuy && newSL>curSL+activeSymbolPoint*0.5) ||
             (!isBuy && (curSL<=0 || newSL<curSL-activeSymbolPoint*0.5))))
            PanelRememberTrail(selTicket,newSL);
         Print("gold_x9: position ", selTicket, " managed. fav=", DoubleToString(favorablePct, 3), "% loss=", DoubleToString(lossPct, 3), "% SL ", DoubleToString(curSL, activeSymbolDigits), " -> ", DoubleToString(newSL, activeSymbolDigits), " TP ", DoubleToString(curTP, activeSymbolDigits), " -> ", DoubleToString(newTP, activeSymbolDigits));
        }

      Sleep(200);
     }
  }

void ApplyChartStyle()
  {
   if(g_pcReady && hideOriginalChart) { PanelHideNative(); return; }
   long chartId=0;
   color bg=UiChartBg(), fg=UiChartFg(), bull=UiBull(), bear=UiBear();
   ChartSetInteger(chartId,CHART_MODE,CHART_CANDLES);
   ChartSetInteger(chartId,CHART_SHOW_GRID,false);
   ChartSetInteger(chartId,CHART_COLOR_BACKGROUND,bg);
   ChartSetInteger(chartId,CHART_COLOR_FOREGROUND,fg);
   ChartSetInteger(chartId,CHART_COLOR_CHART_UP,bull);
   ChartSetInteger(chartId,CHART_COLOR_CANDLE_BULL,bull);
   ChartSetInteger(chartId,CHART_COLOR_CHART_DOWN,bear);
   ChartSetInteger(chartId,CHART_COLOR_CANDLE_BEAR,bear);
   ChartSetInteger(chartId,CHART_COLOR_BID,UiAccent());
   ChartSetInteger(chartId,CHART_COLOR_ASK,UiGood());
   ChartSetInteger(chartId,CHART_COLOR_VOLUME,UiDim());
   ChartSetInteger(chartId,CHART_COLOR_CHART_LINE,UiAccent());
   ChartSetInteger(chartId,CHART_COLOR_STOP_LEVEL,UiAmber());
   ChartSetInteger(chartId,CHART_AUTOSCROLL,true);
   ChartSetInteger(chartId,CHART_SHIFT,true);
   ChartRedraw(chartId);
  }


#define ACC_W 280
#define ACC_H 360
#define STR_W 280
#define STR_H 210
#define THM_W 1292
#define THM_H 90
#define LIV_W 1
#define LIV_H 1
#define EQP_W 280
#define EQP_H 145
#define TRK_W 1292
int           g_trkW     = TRK_W;
double        g_trkScale = 1.0;
#define TRK_H 150

// Design 4: exactly four palettes, applied to EVERY chart/table/control surface.
string HudThemeName()
  {
   if(g_activeTheme==HUD_LIGHT) return "LIGHT";
   if(g_activeTheme==HUD_MIDNIGHT) return "MIDNIGHT";
   if(g_activeTheme==HUD_EMERALD) return "EMERALD";
   return "GRAPHITE";
  }
color UiInk(){return g_activeTheme==HUD_LIGHT?C'22,38,55':C'237,243,249';}
color UiDim(){return g_activeTheme==HUD_LIGHT?C'94,111,128':C'156,173,191';}
color UiPanel(){switch(g_activeTheme){case HUD_LIGHT:return C'255,255,255';case HUD_MIDNIGHT:return C'18,29,48';case HUD_EMERALD:return C'19,39,32';default:return C'23,25,31';}}
color UiBand(){switch(g_activeTheme){case HUD_LIGHT:return C'240,245,250';case HUD_MIDNIGHT:return C'26,43,65';case HUD_EMERALD:return C'27,55,44';default:return C'35,38,46';}}
color UiBorder(){return g_activeTheme==HUD_LIGHT?C'212,222,232':(g_activeTheme==HUD_EMERALD?C'49,78,65':C'49,62,78');}
color UiAccent(){switch(g_activeTheme){case HUD_LIGHT:return C'31,98,199';case HUD_MIDNIGHT:return C'83,169,252';case HUD_EMERALD:return C'118,210,165';default:return C'185,203,224';}}
color UiGood(){return g_activeTheme==HUD_LIGHT?C'12,130,96':C'89,207,169';}
color UiBad(){return g_activeTheme==HUD_LIGHT?C'190,63,81':C'243,130,145';}
color UiAmber(){return g_activeTheme==HUD_LIGHT?C'154,108,19':C'226,192,115';}
color UiCurve(){return UiAccent();}
color UiChartBg(){switch(g_activeTheme){case HUD_LIGHT:return C'237,242,247';case HUD_MIDNIGHT:return C'9,17,30';case HUD_EMERALD:return C'8,24,18';default:return C'13,14,17';}}
color UiChartFg(){return UiInk();}
color UiBull(){return UiGood();}
color UiBear(){return UiBad();}

color HudDim2() { return UiDim(); }

string MonthStr(int m)
  {
   switch(m)
     {
      case 1:  return "Jan"; case 2:  return "Feb"; case 3:  return "Mar"; case 4:  return "Apr";
      case 5:  return "May"; case 6:  return "Jun"; case 7:  return "Jul"; case 8:  return "Aug";
      case 9:  return "Sep"; case 10: return "Oct"; case 11: return "Nov"; default: return "Dec";
     }
  }

string HudDate(datetime t)
  {
   MqlDateTime st; TimeToStruct(t, st);
   return StringFormat("%d %s %02d:%02d", st.day, MonthStr(st.mon), st.hour, st.min);
  }

void HudRectObj(string name, int panel, int dx, int dy, int w, int h, color bgc, color bord)
  {
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_CORNER,      CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_XSIZE,       w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE,       h);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR,     bgc);
   ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, name, OBJPROP_COLOR,       bord);
   ObjectSetInteger(0, name, OBJPROP_FILL,        true);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE,  false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN,      true);
   ObjectSetInteger(0, name, OBJPROP_BACK,        false);
   if(g_hN < HUD_MAXO)
     {
      g_hName[g_hN] = name; g_hPanel[g_hN] = panel; g_hDx[g_hN] = dx; g_hDy[g_hN] = dy; g_hRA[g_hN] = 0; g_hSize[g_hN] = 0; g_hRect[g_hN] = 1; g_hW[g_hN] = w; g_hH[g_hN] = h; g_hN++;
     }
  }

int TextW(string s, int size)
  {
   return (int)MathCeil(StringLen(s) * size * 0.82) + 2;
  }

void HudLabelObj(string name, int panel, int dx, int dy, string text, color c, int size, bool ra, bool bold)
  {
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetString (0, name, OBJPROP_TEXT,      text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,     c);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,  size);
   ObjectSetString (0, name, OBJPROP_FONT,      bold ? "Arial Bold" : "Arial");
   ObjectSetInteger(0, name, OBJPROP_ANCHOR,    ANCHOR_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_CORNER,    CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN,    true);
   ObjectSetInteger(0, name, OBJPROP_BACK,      false);
   if(g_hN < HUD_MAXO)
     {
      g_hName[g_hN] = name; g_hPanel[g_hN] = panel; g_hDx[g_hN] = dx; g_hDy[g_hN] = dy; g_hRA[g_hN] = ra ? 1 : 0; g_hSize[g_hN] = size; g_hRect[g_hN] = 0; g_hW[g_hN] = 0; g_hH[g_hN] = 0; g_hN++;
     }
  }

int HudFind(string name)
  {
   for(int i = 0; i < g_hN; i++) if(g_hName[i] == name) return i;
   return -1;
  }

void HudMoveAll()
  {
   for(int i = 0; i < g_hN; i++)
     {
      int p = g_hPanel[i];
      int x = g_px[p] + g_hDx[i];
      int y = g_py[p] + g_hDy[i];
      if(g_hRect[i] == 0 && g_hRA[i] == 1)
        {
         string txt = ObjectGetString(0, g_hName[i], OBJPROP_TEXT);
         x = g_px[p] + g_pw[p] - 15 - TextW(txt, g_hSize[i]);
        }
      ObjectSetInteger(0, g_hName[i], OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, g_hName[i], OBJPROP_YDISTANCE, y);
     }
  }

void HudSetText(string name, string text, color c)
  {
   int i = HudFind(name);
   if(i < 0) return;
   ObjectSetString(0,name,OBJPROP_TOOLTIP,text);
   if(g_hW[i]>0 && TextW(text,g_hSize[i])>g_hW[i])
     {
      while(StringLen(text)>1 && TextW(text+"...",g_hSize[i])>g_hW[i])
         text=StringSubstr(text,0,StringLen(text)-1);
      text+="...";
     }
   ObjectSetString (0, name, OBJPROP_TEXT,  text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   if(g_hRA[i] == 1)
     {
      int p = g_hPanel[i];
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, g_px[p] + g_pw[p] - 15 - TextW(text, g_hSize[i]));
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, g_py[p] + g_hDy[i]);
     }
  }

// Layout 4: header + metric ribbon, full-width chart, trade/equity dock, tracker.
// No bitmap skin or minimum-size inflation: use actual available chart pixels.
void FocusGeometry(int width,int height)
  {
   g_chartW=width;g_chartH=height;
   g_focusReady=(width>=800 && height>=400);
   for(int i=0;i<HUD_NP;i++) { g_px[i]=8;g_py[i]=8;g_pw[i]=0;g_ph[i]=0; }
   if(!g_focusReady) return;
   g_px[2]=8;g_py[2]=8;g_pw[2]=width-16;g_ph[2]=((width<1180)?140:108)-(height<560?20:0);
   g_px[5]=8;g_ph[5]=(height<560)?80:156;g_py[5]=height-g_ph[5]-8;g_pw[5]=width-16;
   g_px[3]=8;g_py[3]=g_py[2]+g_ph[2]+8;g_pw[3]=width-16;g_ph[3]=g_py[5]-8-g_py[3];
   int capacity=(int)MathMax(1,(g_ph[3]-10-(height<560?60:100)-26-44-8)/20);
   g_focusRows=(int)MathMin(capacity,MathMax(1,MathMin(40,chartTradeRows)));
   g_focusDockH=44+g_focusRows*20;
   int equityWidth=showEquityCurve?(int)MathMax(224,MathMin(360,g_pw[3]*0.28)):0;
   g_focusTableW=g_pw[3]-(equityWidth>0?equityWidth+12:0);
   g_px[4]=g_px[3]+g_focusTableW+12;
   g_py[4]=g_py[3]+g_ph[3]-8-g_focusDockH;
   g_pw[4]=equityWidth;g_ph[4]=g_focusDockH;
  }

void HudLayout()
  {
   int width=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int height=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS);
   bool resized=(width!=g_chartW || height!=g_chartH);
   FocusGeometry(width,height);
   if(resized && g_hN>0)
     {
      EqCanvasDestroy();
      ObjectsDeleteAll(0,HUD_PREFIX);
      g_hN=0;
      HudCreate();
     }
   HudMoveAll();
  }

void HudBoundLabel(string name,int panel,int x,int y,int width,string value,color ink,int size,bool bold)
  {
   HudLabelObj(name,panel,x,y,value,ink,size,false,bold);
   int idx=HudFind(name);
   if(idx>=0) g_hW[idx]=width;
  }

void HudCreate()
  {
   g_hN=0;
   if(!g_focusReady)
     {
      HudLabelObj(HUD_PREFIX+"small",2,8,8,"X9: enlarge chart to 800 x 400 for Focus dashboard",UiAccent(),9,false,true);
      HudMoveAll();return;
     }
   int width=g_pw[2];
   bool compact=(g_chartW<1180);
   bool shortView=(g_chartH<560);
   int trackerRows=shortView?1:5;
   int headerHeight=compact?68:36,metricY=headerHeight+8;
   HudRectObj(HUD_PREFIX+"header",2,0,0,width,headerHeight,UiPanel(),UiBorder());
   HudBoundLabel(HUD_PREFIX+"brand",2,12,8,150,"X9 / FULL FOCUS",UiAccent(),12,true);
   HudBoundLabel(HUD_PREFIX+"symbol",2,compact?12:174,compact?43:11,compact?122:114,
                 activeTradeSymbol+" M"+IntegerToString(Period()),UiAccent(),9,true);
   HudBoundLabel(HUD_PREFIX+"market_info",2,compact?528:686,compact?44:11,
                 compact?width-544:width-1034,"-",UiDim(),8,false);
   HudBoundLabel(HUD_PREFIX+"top_status",2,width-335,10,160,"TRADING ACTIVE",UiGood(),9,true);
   string theme=HUD_PREFIX+"theme_cycle";
   ObjectCreate(0,theme,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,theme,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,theme,OBJPROP_XDISTANCE,g_px[2]+width-167);
   ObjectSetInteger(0,theme,OBJPROP_YDISTANCE,g_py[2]+5);
   ObjectSetInteger(0,theme,OBJPROP_XSIZE,158);
   ObjectSetInteger(0,theme,OBJPROP_YSIZE,26);
   ObjectSetInteger(0,theme,OBJPROP_BGCOLOR,UiBand());
   ObjectSetInteger(0,theme,OBJPROP_COLOR,UiAccent());
   ObjectSetInteger(0,theme,OBJPROP_BORDER_COLOR,UiBorder());
   ObjectSetInteger(0,theme,OBJPROP_FONTSIZE,9);
   ObjectSetInteger(0,theme,OBJPROP_ZORDER,50);
   ObjectSetInteger(0,theme,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,theme,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,theme,OBJPROP_STATE,false);
   ObjectSetString(0,theme,OBJPROP_TEXT,"THEME: "+HudThemeName()+" >");
   ObjectSetString(0,theme,OBJPROP_TOOLTIP,"Switch Graphite / Light / Midnight / Emerald. Display only; trades unchanged.");
   string labels[6],ids[6];
   labels[0]="EQUITY";labels[1]="BALANCE";labels[2]="OPEN P/L";
   labels[3]="DAILY DD";labels[4]="OPEN POSITIONS";labels[5]="PENDING ORDERS";
   ids[0]="top_eq";ids[1]="top_balance";ids[2]="acc_W3";
   ids[3]="top_dd";ids[4]="top_pos";ids[5]="top_pending";
   for(int i=0;i<6;i++)
     {
      int x=i*width/6,cellWidth=(i+1)*width/6-x-5;
      HudRectObj(HUD_PREFIX+"metric"+IntegerToString(i),2,x,metricY,cellWidth,shortView?44:64,UiPanel(),UiBorder());
      HudBoundLabel(HUD_PREFIX+"metric_label"+IntegerToString(i),2,x+10,metricY+7,cellWidth-20,labels[i],UiDim(),8,true);
      HudBoundLabel(HUD_PREFIX+ids[i],2,x+10,metricY+26,cellWidth-20,"-",UiInk(),shortView?12:(g_chartW<1000?16:20),true);
     }
   HudRectObj(HUD_PREFIX+"trk_bg",5,0,0,g_pw[5],g_ph[5],UiPanel(),UiBorder());
   HudLabelObj(HUD_PREFIX+"trk_title",5,12,10,"TRADE TRACKER",UiAccent(),12,false,true);
   bool wide=(g_chartW>=1100 && !shortView);
   int tableWidth=g_pw[5]-(wide?238:0);
   for(int band=0;band<trackerRows;band++)
      HudRectObj(HUD_PREFIX+"trk_band"+IntegerToString(band),5,8,52+band*19,tableWidth-16,18,
         band%2==0?UiBand():UiPanel(),band%2==0?UiBand():UiPanel());
   int percentages[8];percentages[0]=0;percentages[1]=18;percentages[2]=29;percentages[3]=39;
   percentages[4]=52;percentages[5]=66;percentages[6]=83;percentages[7]=100;
   string heads[7];heads[0]="DATE";heads[1]="TRADES";heads[2]="LOTS";
   heads[3]="GAIN %";heads[4]="COST $";heads[5]="GROSS $";heads[6]="NET $";
   string unit=AccountCurrency()=="USD"?"$":AccountCurrency();
   heads[4]="COST "+unit;heads[5]="GROSS "+unit;heads[6]="NET "+unit;
   for(int c=0;c<7;c++)
     {
      int x=12+(tableWidth-24)*percentages[c]/100;
      int cw=(tableWidth-24)*(percentages[c+1]-percentages[c])/100-4;
      HudBoundLabel(HUD_PREFIX+"trk_H"+IntegerToString(c),5,x,35,cw,heads[c],UiDim(),8,true);
      for(int r=0;r<trackerRows;r++)
         HudBoundLabel(HUD_PREFIX+"trk_R"+IntegerToString(r)+"_"+IntegerToString(c),5,x,55+r*19,cw,"-",UiInk(),9,false);
     }
   if(wide)
     {
      string titles[5];titles[0]="WIN RATE";titles[1]="PROFIT FACTOR";titles[2]="EXPECTANCY";
      titles[3]="COST DRAG";titles[4]="BEST / WORST";
      for(int m=0;m<5;m++)
        {
         HudBoundLabel(HUD_PREFIX+"trk_SL"+IntegerToString(m),5,tableWidth+10,12+m*28,98,titles[m],UiDim(),8,true);
         HudBoundLabel(HUD_PREFIX+"trk_SV"+IntegerToString(m),5,tableWidth+110,12+m*28,116,"-",UiInk(),9,true);
        }
     }
   else
     {
      HudLabelObj(HUD_PREFIX+"trk_SL0",5,g_pw[5]-222,12,"WIN",UiDim(),8,false,true);
      HudLabelObj(HUD_PREFIX+"trk_SV0",5,g_pw[5]-189,11,"-",UiInk(),9,false,true);
      HudLabelObj(HUD_PREFIX+"trk_SL1",5,g_pw[5]-112,12,"PF",UiDim(),8,false,true);
      HudLabelObj(HUD_PREFIX+"trk_SV1",5,g_pw[5]-86,11,"-",UiInk(),9,false,true);
     }
   HudMoveAll();
  }

void HudCycleTheme()
  {
   // UI-only rebuild; no OnInit, no trade/risk state reset.
   g_activeTheme=(g_activeTheme+1)%4;
   PanelDestroy();EqCanvasDestroy();
   ObjectsDeleteAll(0,HUD_PREFIX);g_hN=0;
   if(applyChartStyle) ApplyChartStyle();
   HudLayout();HudCreate();HudTick(true);PanelDraw(true);EqDraw();
   ChartRedraw(0);
  }

void RefreshStats()
  {
   for(int s=0;s<10;s++){ statTrades[s]=0; statClosed[s]=0.0; statPerTrade[s]=0.0; }
   g_totalClosedPL=0.0; g_winCount=0; g_lossCount=0; g_grossWin=0.0; g_grossLoss=0.0;
   g_bestNet=0.0; g_worstNet=0.0; g_totalCommClosed=0.0; g_salvage=0; g_cuts=0; g_tN=0;
   double holdSum=0.0; int matched=0;
   int total=OrdersHistoryTotal();
   for(int i=0;i<total;i++)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_HISTORY)) continue;
      if(!IsMatchingOrder()) continue;
      int typ=OrderType();
      int sid=ParseSid(OrderComment());
      double gross=OrderProfit()+OrderSwap();
      double comm=CommissionCost(OrderLots());
      double net=gross-comm;
      statTrades[sid]++; statClosed[sid]+=net; g_totalClosedPL+=net;
      if(net>=0.0){g_winCount++;g_grossWin+=net;} else {g_lossCount++;g_grossLoss+=-net;}
      if(matched==0){g_bestNet=net;g_worstNet=net;} else {if(net>g_bestNet)g_bestNet=net;if(net<g_worstNet)g_worstNet=net;}
      g_totalCommClosed+=comm;
      holdSum+=(double)(OrderCloseTime()-OrderOpenTime());
      matched++;
      double tol=5.0*activePipFactor, cp=OrderClosePrice(), op=OrderOpenPrice();
      double tp=OrderTakeProfit(), sl=OrderStopLoss();
      bool isBuy=(typ==OP_BUY);
      if(tp>0.0 && MathAbs(cp-tp)<=tol){if((isBuy&&tp<op)||(!isBuy&&tp>op))g_salvage++;}
      else if(sl>0.0 && MathAbs(cp-sl)<=tol) g_cuts++;
     }
   for(int s2=1;s2<=9;s2++) statPerTrade[s2]=(statTrades[s2]>0)?statClosed[s2]/statTrades[s2]:0.0;
   g_avgHoldSec=(matched>0)?holdSum/matched:0.0;

   g_streak=0; bool first=true, sign=true;
   for(int z=total-1;z>=0;z--)
     {
      if(!OrderSelect(z,SELECT_BY_POS,MODE_HISTORY))continue;
      if(!IsMatchingOrder()) continue;
      bool win=(OrderProfit()+OrderSwap()-CommissionCost(OrderLots()))>=0.0;
      if(first){sign=win;first=false;}
      if(win!=sign)break;
      g_streak++;
     }
   if(!first&&!sign)g_streak=-g_streak;

   int keys[]; ArrayResize(keys,total); ArrayInitialize(keys,0); int nk=0;
   for(int q=0;q<total;q++)
     {
      if(!OrderSelect(q,SELECT_BY_POS,MODE_HISTORY))continue;
      if(!IsMatchingOrder()) continue;
      MqlDateTime ds; TimeToStruct(OrderCloseTime(),ds);
      int key=ds.year*10000+ds.mon*100+ds.day;
      bool seen=false;
      for(int u=0;u<nk;u++)if(keys[u]==key){seen=true;break;}
      if(!seen)keys[nk++]=key;
     }
   for(int a=1;a<nk;a++){int kv=keys[a],b=a-1;while(b>=0&&keys[b]<kv){keys[b+1]=keys[b];b--;}keys[b+1]=kv;}
   g_tN=(nk<5)?nk:5;
   for(int r=0;r<8;r++){g_tD[r]=0;g_tSide[r]=0;g_tLot[r]=0;g_tGain[r]=0;g_tComm[r]=0;g_tProf[r]=0;g_tNet[r]=0;}
   for(int q2=0;q2<total;q2++)
     {
      if(!OrderSelect(q2,SELECT_BY_POS,MODE_HISTORY))continue;
      if(!IsMatchingOrder()) continue;
      MqlDateTime dd; TimeToStruct(OrderCloseTime(),dd);
      int dk=dd.year*10000+dd.mon*100+dd.day;
      int row=-1;
      for(int rr=0;rr<g_tN;rr++)if(keys[rr]==dk){row=rr;break;}
      if(row<0)continue;
      MqlDateTime zero=dd; zero.hour=0;zero.min=0;zero.sec=0;
      g_tD[row]=StructToTime(zero);
      double gr=OrderProfit()+OrderSwap(), co=CommissionCost(OrderLots()), ne=gr-co;
      g_tSide[row]++; g_tLot[row]+=OrderLots(); g_tComm[row]+=co; g_tProf[row]+=gr; g_tNet[row]+=ne;
     }
   double balBase=MathMax(1.0,AccountBalance());
   for(int dr=0;dr<g_tN;dr++) g_tGain[dr]=g_tNet[dr]/balBase*100.0;
  }

void TrackEquityAndDD()
  {
   double eq = AccountEquity();
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   int dayKey = dt.year * 10000 + dt.mon * 100 + dt.day;

   if(dayKey != g_dayKey)
     {
      g_dayKey         = dayKey;
      g_dayStartEquity = eq;
      g_dayPeakEquity  = eq;
      if(g_ddHalted)
        {
         g_ddHalted = false;
         Print("gold_x9: new trading day - drawdown guard RESET, entries RESUMED. Day-start equity ", DoubleToString(eq, 2));
        }
      else Print("gold_x9: new trading day. Day-start equity ", DoubleToString(eq, 2));
     }

   if(eq > g_dayPeakEquity) g_dayPeakEquity = eq;

   double ddFromStart = (g_dayStartEquity > 0.0) ? (g_dayStartEquity - eq) / g_dayStartEquity * 100.0 : 0.0;
   double ddFromPeak  = (g_dayPeakEquity  > 0.0) ? (g_dayPeakEquity  - eq) / g_dayPeakEquity  * 100.0 : 0.0;

   g_currentDD = MathMax(0.0, MathMax(ddFromStart, ddFromPeak));

   double pauseAt  = maxAllowedDrawdownPct;
   double resumeAt = MathMax(0.0, maxAllowedDrawdownPct - 2.0);

   bool shouldHalt = g_ddHalted ? (g_currentDD > resumeAt) : (g_currentDD >= pauseAt);
   if(!enableDDHalt || maxAllowedDrawdownPct <= 0.0) shouldHalt = false;

   if(shouldHalt && !g_ddHalted)
     {
      g_ddHalted = true;
      Print("gold_x9: daily max drawdown reached (", DoubleToString(g_currentDD, 1), "% >= ", DoubleToString(maxAllowedDrawdownPct, 1), "%). New entries PAUSED until recovery or next trading day.");
     }
   else if(!shouldHalt && g_ddHalted)
     {
      g_ddHalted = false;
      Print("gold_x9: drawdown recovered to ", DoubleToString(g_currentDD, 1), "% - new entries RESUMED.");
     }

   if(enableEquityCurveHalt && equityCurveHaltPct > 0.0)
     {
      double eqLab = AccountEquity();
      if(eqLab > g_peakEquityLab) g_peakEquityLab = eqLab;
      if(g_peakEquityLab > 0.0)
        {
         double labDD   = (g_peakEquityLab - eqLab) / g_peakEquityLab * 100.0;
         double rearmAt = MathMax(0.0, equityCurveHaltPct - 2.0);

         MqlDateTime ldt; TimeToStruct(TimeCurrent(), ldt);
         int weekKey = ldt.year * 1000 + (ldt.day_of_year / 7);
         if(g_lastWeekKey < 0) g_lastWeekKey = weekKey;
         if(ldt.day_of_week == 1 && weekKey != g_lastWeekKey)
           {
            g_lastWeekKey = weekKey;
            if(g_equityHalted && !g_probationWeek)
              {
               g_probationWeek = true;
               Print("gold_x9 LAB M3: new week underwater - PROBATION week at half lot.");
              }
           }

         if(!g_equityHalted && labDD >= equityCurveHaltPct)
           {
            g_equityHalted = true;
            Print("gold_x9 LAB M3: equity-curve halt (DD ", DoubleToString(labDD, 1), "% >= ", DoubleToString(equityCurveHaltPct, 1), "%).");
           }
         else if(g_equityHalted && labDD <= rearmAt)
           {
            g_equityHalted    = false;
            g_probationWeek   = false;
            Print("gold_x9 LAB M3: equity recovered to ", DoubleToString(labDD, 1), "% from peak - breaker RE-ARMED.");
           }

         if(equityHaltMode == 0)
            g_lotMultiplier = g_probationWeek ? 0.5 : 1.0;
         else
            g_lotMultiplier = g_equityHalted ? 0.5 : 1.0;
        }
     }
   else g_lotMultiplier = 1.0;
  }

void HudTick(bool force)
  {
   if(!showDashboardPanel) return;
   if((int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS)!=g_chartW ||
      (int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS)!=g_chartH) HudLayout();
   if(!g_focusReady) return;
   uint ms = GetTickCount();
   if(!force && (ms - g_lastPanelMs) < 1000) return;
   g_lastPanelMs = ms;

   if(applyChartStyle) ApplyChartStyle();

   // Reporting uses the same filter for live and closed trades. Do not use
   // SelectOwnPosition here: that strict selector is for trade management.
   g_openPL = 0.0;
   int openCount = 0;
   int buyCount=0,sellCount=0,pendingBuy=0,pendingSell=0;
   ArrayInitialize(statOpenTrades, 0);
   ArrayInitialize(statOpenPL, 0.0);
   double openLots = 0.0, openPips = 0.0, openProfit = 0.0, openComm = 0.0, openSwap = 0.0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderCloseTime()!=0 || !IsMatchingOrderIdentity()) continue;
      int liveType=OrderType();
      if(liveType==OP_BUYSTOP || liveType==OP_BUYLIMIT) { pendingBuy++; continue; }
      if(liveType==OP_SELLSTOP || liveType==OP_SELLLIMIT) { pendingSell++; continue; }
      if(liveType!=OP_BUY && liveType!=OP_SELL) continue;
      if(liveType==OP_BUY) buyCount++; else sellCount++;
      // Triggered stops are now OP_BUY/OP_SELL, regardless of placement day.
      int sid = ParseSid(OrderComment());
      openCount++;
      statOpenTrades[sid]++;
      double pr = OrderProfit();
      double uiComm=CommissionCost(OrderLots());
      double liveNet = pr + OrderSwap() - uiComm;
      g_openPL   += liveNet;
      statOpenPL[sid] += liveNet;
      openProfit += pr;
      openComm   += uiComm;
      openSwap   += OrderSwap();
      openLots   += OrderLots();
      double op     = OrderOpenPrice();
      bool   isBuy  = (OrderType() == OP_BUY);
      double exitPr = isBuy ? SymbolBid() : SymbolAsk();
      openPips += (isBuy ? (exitPr - op) : (op - exitPr)) / activePipFactor;
     }

   RefreshStats();

   double totalPL  = g_totalClosedPL + g_openPL;
   double balance  = AccountBalance();
   double equity   = AccountEquity();
   int    nTrades  = g_winCount + g_lossCount;
   double winRate  = (nTrades > 0) ? (double)g_winCount / (double)nTrades * 100.0 : 0.0;
   double pf       = (g_grossLoss > 0.0) ? g_grossWin / g_grossLoss : 0.0;
   string n;

   string statusText;
   color statusColor;
   if(enableEquityCurveHalt && g_equityHalted && equityHaltMode == 0 && !g_probationWeek)
     { statusText = "HALT (equity DD)";         statusColor = UiBad();  }
   else if(g_lotMultiplier < 1.0)
     { statusText = "PROBATION 1/2 lot";        statusColor = UiAmber(); }
   else if(enableDeadWindow && InDeadWindow(TimeCurrent()))
     { statusText = "Dead window (no entries)"; statusColor = UiAmber(); }
   else if(g_ddHalted)
     { statusText = "PAUSED (max DD)";          statusColor = UiBad();  }
   else if(countOwnPositions() >= activeMaxPositions)
     { statusText = "Max positions";            statusColor = UiAmber(); }
   else
     { statusText = "TRADING ACTIVE";           statusColor = UiGood(); }
   HudSetText(HUD_PREFIX + "str_cV", statusText, statusColor);

   HudSetText(HUD_PREFIX + "acc_sym", activeTradeSymbol + " | M" + IntegerToString(Period()), UiDim());
   HudSetText(HUD_PREFIX + "acc_eq",  DoubleToString(equity, 2), UiGood());
   double startBal = balance - g_totalClosedPL;
   double gainPct  = (startBal > 0.0) ? (totalPL / startBal) * 100.0 : 0.0;
   HudSetText(HUD_PREFIX + "acc_pct", (gainPct >= 0.0 ? "+" : "") + DoubleToString(gainPct, 2) + "%", (gainPct >= 0.0) ? UiGood() : UiBad());
   HudSetText(HUD_PREFIX + "acc_V0", DoubleToString(balance, 2), UiInk());
   HudSetText(HUD_PREFIX + "acc_V1", DoubleToString(equity, 2), UiAmber());
   HudSetText(HUD_PREFIX + "acc_V2", DoubleToString(AccountMargin(), 2), UiInk());
   HudSetText(HUD_PREFIX + "acc_V3", DoubleToString(AccountFreeMargin(), 2), UiInk());
   double ml = (AccountMargin() > 0.0) ? AccountEquity() / AccountMargin() * 100.0 : 0.0;
   HudSetText(HUD_PREFIX + "acc_V4", (ml <= 0.0) ? "0%" : DoubleToString(ml, 0) + "%", (ml <= 0.0) ? UiBad() : UiInk());
   HudSetText(HUD_PREFIX + "acc_W0", (openProfit >= 0.0 ? "+" : "") + DoubleToString(openProfit, 2), (openProfit >= 0.0) ? UiGood() : UiBad());
   HudSetText(HUD_PREFIX + "acc_W1", "-" + DoubleToString(openComm, 2), UiBad());
   HudSetText(HUD_PREFIX + "acc_W2", (openSwap >= 0.0 ? "+" : "") + DoubleToString(openSwap, 2), (openSwap >= 0.0) ? UiGood() : UiBad());
   HudSetText(HUD_PREFIX + "acc_W3", (g_openPL >= 0.0 ? "+" : "") + DoubleToString(g_openPL, 2), (g_openPL >= 0.0) ? UiGood() : UiBad());
   HudSetText(HUD_PREFIX + "acc_tV", IntegerToString(nTrades) + " | " + DoubleToString(winRate, 1) + "% | " + DoubleToString(pf, 2), UiAmber());
   HudSetText(HUD_PREFIX + "acc_nV", (totalPL >= 0.0 ? "+" : "") + DoubleToString(totalPL, 2), (totalPL >= 0.0) ? UiGood() : UiBad());
   color ddClr = (g_currentDD >= maxAllowedDrawdownPct) ? UiBad() : (g_currentDD >= maxAllowedDrawdownPct / 2.0) ? UiAmber() : UiInk();
   HudSetText(HUD_PREFIX + "acc_dV", DoubleToString(g_currentDD, 1) + "% / " + DoubleToString(maxAllowedDrawdownPct, 1) + "%", ddClr);
   if(maxAllowedDrawdownPct > 0.0)
     {
      int bw = (int)MathMax(2.0, (ACC_W - 24) * MathMin(1.0, g_currentDD / maxAllowedDrawdownPct));
      ObjectSetInteger(0, HUD_PREFIX + "acc_bar", OBJPROP_XSIZE, bw);
      ObjectSetInteger(0, HUD_PREFIX + "acc_bar", OBJPROP_COLOR, (g_currentDD >= maxAllowedDrawdownPct) ? UiBad() : UiGood());
      ObjectSetInteger(0, HUD_PREFIX + "acc_bar", OBJPROP_BGCOLOR, (g_currentDD >= maxAllowedDrawdownPct) ? UiBad() : UiGood());
     }

   string info[10];
   info[0]=IntegerToString(openCount)+" (B"+IntegerToString(buyCount)+" S"+IntegerToString(sellCount)+")";
   info[1]=IntegerToString(pendingBuy+pendingSell)+" (B"+IntegerToString(pendingBuy)+" S"+IntegerToString(pendingSell)+")";
   info[2]=DoubleToString(openLots,2);
   info[3]=IntegerToString((int)MarketInfo(activeTradeSymbol,MODE_SPREAD));
   info[4]=DoubleToString(g_currentDD,1)+"%";
   info[5]=StringFormat("%dh %02dm",(int)g_avgHoldSec/3600,((int)g_avgHoldSec%3600)/60);
   info[6]=IntegerToString(nTrades);
   info[7]=DoubleToString(winRate,1)+"%";
   info[8]=IntegerToString(statTrades[9]+statOpenTrades[9]);
   info[9]=(totalPL>=0?"+":"")+DoubleToString(totalPL,2);
   for(int ir=0;ir<10;ir++)
      HudSetText(HUD_PREFIX+"str_infoV"+IntegerToString(ir),info[ir],
         (ir==9)?((totalPL>=0)?UiGood():UiBad()):UiInk());

   if(showSpreadTag)
     {
      int spreadPoints = (int)MarketInfo(activeTradeSymbol, MODE_SPREAD);
      int periodSec = PeriodSeconds(0);
      if(periodSec < 1) periodSec = 60;
      int remain = periodSec - (int)(TimeCurrent() % periodSec);
      string cd;
      if(remain >= 3600) cd = StringFormat("%02d:%02d:%02d", remain / 3600, (remain % 3600) / 60, remain % 60);
      else cd = StringFormat("%02d:%02d", remain / 60, remain % 60);

      HudSetText(HUD_PREFIX + "liv_V0", IntegerToString(spreadPoints), UiAmber());
      HudSetText(HUD_PREFIX + "liv_V1", (g_openPL >= 0.0 ? "+" : "") + DoubleToString(g_openPL, 2), (g_openPL >= 0.0) ? UiGood() : UiBad());
      HudSetText(HUD_PREFIX + "liv_V2", DoubleToString(openPips, 1), (openPips >= 0.0) ? UiGood() : UiBad());
      HudSetText(HUD_PREFIX + "liv_V3", DoubleToString(openLots, 2), UiInk());
      HudSetText(HUD_PREFIX + "liv_V4", IntegerToString(openCount) + "/" + IntegerToString(activeMaxPositions), UiInk());
      HudSetText(HUD_PREFIX + "liv_V5", cd, UiAmber());
     }

   for(int r=0;r<5;r++)
     {
      n=IntegerToString(r);
      // Reserve one row for ALL matching live positions, including carryovers.
      // Realized daily rows remain grouped by close date, never entry date.
      int historyRow = r - ((openCount > 0) ? 1 : 0);
      if(openCount > 0 && r == 0)
        {
         color liveColor = (g_openPL >= 0.0) ? UiGood() : UiBad();
         double liveGain = g_openPL / MathMax(1.0, balance) * 100.0;
         HudSetText(HUD_PREFIX+"trk_R"+n+"_0","OPEN (LIVE)",UiAmber());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_1",IntegerToString(openCount),UiInk());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_2",DoubleToString(openLots,2),UiInk());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_3",DoubleToString(liveGain,2)+"%",liveColor);
         HudSetText(HUD_PREFIX+"trk_R"+n+"_4",DoubleToString(openComm,2),UiAmber());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_5",DoubleToString(openProfit+openSwap,2),liveColor);
         HudSetText(HUD_PREFIX+"trk_R"+n+"_6",DoubleToString(g_openPL,2),liveColor);
        }
      else if(historyRow<g_tN)
        {
         color nc=(g_tNet[historyRow]>=0.0)?UiGood():UiBad();
         HudSetText(HUD_PREFIX+"trk_R"+n+"_0",TimeToString(g_tD[historyRow],TIME_DATE),UiInk());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_1",IntegerToString(g_tSide[historyRow]),UiInk());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_2",DoubleToString(g_tLot[historyRow],2),UiInk());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_3",(g_tGain[historyRow]>=0.0?"+":"")+DoubleToString(g_tGain[historyRow],2)+"%",nc);
         HudSetText(HUD_PREFIX+"trk_R"+n+"_4",DoubleToString(g_tComm[historyRow],2),UiAmber());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_5",(g_tProf[historyRow]>=0.0?"+":"")+DoubleToString(g_tProf[historyRow],2),(g_tProf[historyRow]>=0.0)?UiGood():UiBad());
         HudSetText(HUD_PREFIX+"trk_R"+n+"_6",(g_tNet[historyRow]>=0.0?"+":"")+DoubleToString(g_tNet[historyRow],2),nc);
        }
      else
        {
         for(int c=0;c<7;c++) HudSetText(HUD_PREFIX+"trk_R"+n+"_"+IntegerToString(c),"-",UiDim());
        }
     }
   HudSetText(HUD_PREFIX+"trk_SV0",DoubleToString(winRate,1)+"%",UiInk());
   HudSetText(HUD_PREFIX+"trk_SV1",DoubleToString(pf,2),(pf>=1.0)?UiGood():UiBad());
   double expc=(nTrades>0)?g_totalClosedPL/(double)nTrades:0.0;
   HudSetText(HUD_PREFIX+"trk_SV2",(expc>=0.0?"+":"")+DoubleToString(expc,2),(expc>=0.0)?UiGood():UiBad());
   double drag=(g_grossWin>0.0)?g_totalCommClosed/g_grossWin*100.0:0.0;
   HudSetText(HUD_PREFIX+"trk_SV3",DoubleToString(drag,1)+"%",(drag>5.0)?UiBad():UiInk());
   HudSetText(HUD_PREFIX+"trk_SV4",(g_bestNet>=0.0?"+":"")+DoubleToString(g_bestNet,2)+" / "+(g_worstNet>=0.0?"+":"")+DoubleToString(g_worstNet,2),UiInk());

   int spreadPoints=(int)MarketInfo(activeTradeSymbol,MODE_SPREAD);
   int periodSec=PeriodSeconds(0); if(periodSec<1)periodSec=60;
   int remain=periodSec-(int)(TimeCurrent()%periodSec);
   string cd=(remain>=3600)?StringFormat("%02d:%02d:%02d",remain/3600,(remain%3600)/60,remain%60):StringFormat("%02d:%02d",remain/60,remain%60);
   HudSetText(HUD_PREFIX+"top_eq",DoubleToString(equity,2),UiInk());
   HudSetText(HUD_PREFIX+"top_net",(totalPL>=0.0?"+":"")+DoubleToString(totalPL,2),(totalPL>=0.0)?UiGood():UiBad());
   HudSetText(HUD_PREFIX+"top_dd",DoubleToString(g_currentDD,1)+"%",ddClr);
   ObjectSetString(0,HUD_PREFIX+"top_dd",OBJPROP_TOOLTIP,"Live DD / limit: "+DoubleToString(g_currentDD,1)+"% / "+DoubleToString(maxAllowedDrawdownPct,1)+"%");
   HudSetText(HUD_PREFIX+"top_balance",DoubleToString(balance,2),UiInk());
   HudSetText(HUD_PREFIX+"top_pending",IntegerToString(pendingBuy+pendingSell),UiAmber());
   ObjectSetString(0,HUD_PREFIX+"top_pending",OBJPROP_TOOLTIP,info[1]);

   HudSetText(HUD_PREFIX+"top_spread",IntegerToString(spreadPoints),UiInk());
   HudSetText(HUD_PREFIX+"top_pos",IntegerToString(openCount)+"/"+IntegerToString(activeMaxPositions),UiInk());
   HudSetText(HUD_PREFIX+"top_next",cd,UiInk());
   HudSetText(HUD_PREFIX+"market_info","SP "+IntegerToString(spreadPoints)+"  |  NEXT "+cd,UiDim());
   ObjectSetString(0,HUD_PREFIX+"top_pos",OBJPROP_TOOLTIP,info[0]+" | Managed limit "+IntegerToString(activeMaxPositions));
   ObjectSetString(0,HUD_PREFIX+"top_balance",OBJPROP_TOOLTIP,"Currency "+AccountCurrency()+" | Free margin "+DoubleToString(AccountFreeMargin(),2)+" | Used margin "+DoubleToString(AccountMargin(),2));
   HudSetText(HUD_PREFIX+"top_status",statusText,statusColor);
   color sbg=(statusColor==UiGood())?UiGood():((statusColor==UiBad())?UiBad():UiAmber());
   ObjectSetInteger(0,HUD_PREFIX+"top_status_bg",OBJPROP_BGCOLOR,sbg);
   ObjectSetInteger(0,HUD_PREFIX+"top_status_bg",OBJPROP_COLOR,sbg);

   if(showEquityCurve)
     {
      // Rebuild only when matching CLOSED history changes, never from floating equity.
      SeedEquityHistory();
      int kept = EqCount();
      int nUse = (int)MathMin(kept,MathMax(2,MathMin(96,eqCurveSamples)));
      if(nUse > 96) nUse = 96;
      double peak = -1e18, trough = 1e18, maxDD = 0.0, firstV = 0.0, lastV = 0.0, runPeak = -1e18;
      double v; datetime t;
      for(int k = kept - nUse; k < kept; k++)
        {
         EqItem(k, v, t);
         if(k == kept - nUse) firstV = v;
         lastV = v;
         if(v > peak) peak = v;
         if(v < trough) trough = v;
         if(v > runPeak) runPeak = v;
         if(runPeak > 0.0)
           {
            double d = (runPeak - v) / runPeak * 100.0;
            if(d > maxDD) maxDD = d;
           }
        }
      if(kept == 0) { peak = g_eqClosedBase; trough = g_eqClosedBase; }
      double netRet = (firstV > 0.0) ? (lastV - firstV) / firstV * 100.0 : 0.0;
      HudSetText(HUD_PREFIX + "eq_n", IntegerToString(nUse) + " | CLOSED RESULTS", UiDim());
      HudSetText(HUD_PREFIX + "eq_V0", DoubleToString(peak, 2), UiInk());
      HudSetText(HUD_PREFIX + "eq_V1", DoubleToString(trough, 2), UiInk());
      HudSetText(HUD_PREFIX + "eq_V2", DoubleToString(maxDD, 1) + "%", (maxDD > 0.0) ? UiBad() : UiGood());
      HudSetText(HUD_PREFIX + "eq_V3", (netRet >= 0.0 ? "+" : "") + DoubleToString(netRet, 1) + "%", (netRet >= 0.0) ? UiGood() : UiBad());
      EqDraw();
     }

   ChartRedraw(0);
  }
