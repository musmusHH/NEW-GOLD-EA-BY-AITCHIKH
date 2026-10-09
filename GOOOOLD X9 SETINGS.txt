//+------------------------------------------------------------------+
//|                                                 gold_x9_FIXED.mq4 |
//|                                  Copyright 2026, Mr. CapFree     |
//|                                             https://example.com  |
//+------------------------------------------------------------------+
//|  MQL4 port of "gold x9 v6.3" - Base Strategy #9                  |
//|  Source video: "My Most Profitable Gold Trading Bot | Full Build |
//|  From Scratch, Step by Step" - Mr. CapFree (youtu.be/5HkZD7BGuYo)|
//|                                                                  |
//|  HUD v2 (CARBON GRID) - interface rebuilt to the approved        |
//|  product mockup:                                                 |
//|   * 6-panel dashboard: ACCOUNT / STRATEGY MATRIX / THEME /       |
//|     LIVE / TRADE TRACKER / EQUITY CURVE                          |
//|   * C2 closed-trade RESULT TAGS drawn directly at trade close    |
//|     (Simple Result & Points Label: BUY/SELL + Profit + Points)   |
//|   * EQUITY CURVE drawn as a smooth Catmull-Rom spline on a       |
//|     resource bitmap ARGB (curvy line, not bars)                |
//|  All trading logic (fractals, lot sizing, BE/trail/salvage,      |
//|  M1-M4, DD guard) is unchanged from the proven LAB build.        |
//+------------------------------------------------------------------+
#property copyright   "Mr. CapFree"
#property link        "https://example.com"
#property version     "6.570"   // Broker-data chart panel + carryover performance
#property description "gold x9 MQL4 + LAB M1-M4 + live broker-data chart panel"
#property strict
#include <Canvas\Canvas.mqh>

//--- Six embedded professional HUD themes --------------------------
#resource "\\Images\\GX9\\L\\top.bmp"
#resource "\\Images\\GX9\\L\\account.bmp"
#resource "\\Images\\GX9\\L\\strategy.bmp"
#resource "\\Images\\GX9\\L\\equity.bmp"
#resource "\\Images\\GX9\\L\\tracker.bmp"
#resource "\\Images\\GX9\\L\\bottom.bmp"
#resource "\\Images\\GX9\\L\\gauge.bmp"
#resource "\\Images\\GX9\\T\\top.bmp"
#resource "\\Images\\GX9\\T\\account.bmp"
#resource "\\Images\\GX9\\T\\strategy.bmp"
#resource "\\Images\\GX9\\T\\equity.bmp"
#resource "\\Images\\GX9\\T\\tracker.bmp"
#resource "\\Images\\GX9\\T\\bottom.bmp"
#resource "\\Images\\GX9\\T\\gauge.bmp"
#resource "\\Images\\GX9\\G\\top.bmp"
#resource "\\Images\\GX9\\G\\account.bmp"
#resource "\\Images\\GX9\\G\\strategy.bmp"
#resource "\\Images\\GX9\\G\\equity.bmp"
#resource "\\Images\\GX9\\G\\tracker.bmp"
#resource "\\Images\\GX9\\G\\bottom.bmp"
#resource "\\Images\\GX9\\G\\gauge.bmp"
#resource "\\Images\\GX9\\S\\top.bmp"
#resource "\\Images\\GX9\\S\\account.bmp"
#resource "\\Images\\GX9\\S\\strategy.bmp"
#resource "\\Images\\GX9\\S\\equity.bmp"
#resource "\\Images\\GX9\\S\\tracker.bmp"
#resource "\\Images\\GX9\\S\\bottom.bmp"
#resource "\\Images\\GX9\\S\\gauge.bmp"
#resource "\\Images\\GX9\\E\\top.bmp"
#resource "\\Images\\GX9\\E\\account.bmp"
#resource "\\Images\\GX9\\E\\strategy.bmp"
#resource "\\Images\\GX9\\E\\equity.bmp"
#resource "\\Images\\GX9\\E\\tracker.bmp"
#resource "\\Images\\GX9\\E\\bottom.bmp"
#resource "\\Images\\GX9\\E\\gauge.bmp"
#resource "\\Images\\GX9\\A\\top.bmp"
#resource "\\Images\\GX9\\A\\account.bmp"
#resource "\\Images\\GX9\\A\\strategy.bmp"
#resource "\\Images\\GX9\\A\\equity.bmp"
#resource "\\Images\\GX9\\A\\tracker.bmp"
#resource "\\Images\\GX9\\A\\bottom.bmp"
#resource "\\Images\\GX9\\A\\gauge.bmp"

//--- Clickable theme button bitmap states -------------------------
#resource "\\Images\\GX9\\B\\0n.bmp"
#resource "\\Images\\GX9\\B\\0s.bmp"
#resource "\\Images\\GX9\\B\\1n.bmp"
#resource "\\Images\\GX9\\B\\1s.bmp"
#resource "\\Images\\GX9\\B\\2n.bmp"
#resource "\\Images\\GX9\\B\\2s.bmp"
#resource "\\Images\\GX9\\B\\3n.bmp"
#resource "\\Images\\GX9\\B\\3s.bmp"
#resource "\\Images\\GX9\\B\\4n.bmp"
#resource "\\Images\\GX9\\B\\4s.bmp"
#resource "\\Images\\GX9\\B\\5n.bmp"
#resource "\\Images\\GX9\\B\\5s.bmp"

// Enum for Lot Sizing Methods
enum enumLotSizing
  {
   MANUAL_LOTS       = 0, // Manual/Fixed Lots
   TIERED_LOTS       = 1, // Tiered Lot Sizing
   RISK_SCALE_FACTOR = 2  // Risk Scale Factor
  };

// Asset-based professional panel themes
enum enumHudTheme
  {
   HUD_LIGHT_SPORT=0,
   HUD_DARK_TITANIUM=1,
   HUD_GOLD_EXECUTIVE=2,
   HUD_SLATE_PRO=3,
   HUD_EMERALD_CARBON=4,
   HUD_ARCTIC_BLUE=5
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
input enumHudTheme hudTheme = HUD_DARK_TITANIUM;             // Dashboard + chart professional theme
input bool   applyChartStyle       = true;             // Apply Dark Theme + Candlesticks On Start
input color  chartBgColor          = C'255,255,255';        // Chart Background
input color  bullBodyColor         = C'255,255,255';    // Bull Candle Body
input color  bullWickColor         = C'176,137,30';    // Bull Candle Wick
input color  bearBodyColor         = C'219,181,65';     // Bear Candle Body
input color  bearWickColor         = C'176,137,30';     // Bear Candle Wick
input bool   showLiveChartPanel   = true;             // Real broker candles + order overlay in middle panel
input bool   showDashboardPanel    = true;             // Show The 6-Panel CARBON GRID HUD
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

//=== C2 === CLOSED-TRADE RESULT TAGS (visual only) ======================
input bool   drawResultTags        = true;             // C2: Draw A Result Tag Where A Trade Closed
input bool   tagDrawOnInitHistory  = true;             // C2: Also Tag History At EA Start
input int    tagLookbackTrades     = 0;                // C2: How Many Past Trades To Tag At Start (0 = ALL history)
input int    tagMaxOnChart         = 0;                // C2: Keep Newest N Tags (0 = keep all on chart)
input int    tagMaxAgeHours        = 0;                // C2: Delete Tags Older Than N Hours (0 = keep)
input int    tagScanSeconds        = 2;                // C2: History Poll Interval (seconds)
input bool   tagDrawInTester       = false;            // C2: Draw In Blind (non-visual) Tester Runs
input bool   tagDebug              = true;             // C2: Log Object Errors + Scan Counts
input bool   tagHidden             = true;             // C2: Hide Tags From The Object List
input bool   tagKeepOnExit         = false;            // C2: Keep Tags On Chart After EA Is Removed
input bool   tagOnlyMyMagic        = true;             // C2: Filter History Tags (true = use filterMatchMode)
input enumMatchMode filterMatchMode = MATCH_MAGIC_OR_COMMENT; // C2: History Filter Mode (0=Magic OR Comment, 1=Magic, 2=Comment, 3=All Symbol)
input bool   tagBehindChart        = true;             // C2: Tags Behind Candles+Panels
input int    tagFontSize           = 9;                // C2: Tag Font Size
input string tagFontName           = "Consolas";       // C2: Tag Font
input color  tagWinColor           = C'34,214,127';    // C2: Winning Tag Colour (green)
input color  tagLossColor          = C'255,77,90';     // C2: Losing Tag Colour (red)
input bool   showEquityCurve       = true;             // C2: Smooth Equity Curve In EQUITY Panel
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

//=== C2: simple closed-trade result-tag state ==========================
#define TAG_PREFIX "GX9T_"
#define TAG_MAX    512
string        g_tagBase[TAG_MAX];          // object-name base per drawn tag
datetime      g_tagTime[TAG_MAX];          // close time per tag
datetime      g_tagOpen[TAG_MAX];          // open time
double        g_tagPrice[TAG_MAX];         // close price
double        g_tagProfit[TAG_MAX];        // net profit
int           g_tagPoints[TAG_MAX];        // profit points
string        g_tagText[TAG_MAX];          // label text ("BUY +12.50 (+125 pts)")
color         g_tagClr [TAG_MAX];          // win/loss colour
bool          g_tagIsBuy[TAG_MAX];         // trade direction (true = buy, false = sell)
int           g_tagN         = 0;          // count of tracked tags
int           g_tagSeenTkt[TAG_MAX];       // processed key: ticket
datetime      g_tagSeenTm [TAG_MAX];       // processed key: close time
int           g_tagSeenN    = 0;
int           g_tagHistTotal = 0;
uint          g_lastTagMs   = 0;
int           g_tagMade     = 0;
int           g_tagFail     = 0;

//=== C2: equity-curve sample ring ===
#define EQ_MAX 512
double        g_eqVal[EQ_MAX];
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
void   TagScan(bool force);
void   TagInitHistory();
bool   IsMatchingOrder();
bool   TagDrawOne(int ticket);
void   TagTrim();
void   TagDeleteAll();
void   TagRelayout();

//=== HUD v2 prototypes ===
void   HudCreate();
void   HudLayout();
void   HudMoveAll();
void   HudTick(bool force);
void   RefreshStats();
void   EqPush(double v, datetime t);
void   EqCellSet(string name, int x, int y, int w, int h, color clr, bool used);
void   EqDraw();

//=== Broker-data chart panel (display only; never sends/modifies orders) ===
#define PC_NAME "GX9PC_chart"
#define PC_BUTTON "GX9PC_btn_"
CCanvas g_pc;
bool g_pcReady=false, g_pcSaved=false;
long g_pcOldLevels=0, g_pcOldForeground=0;
int g_pcX=0, g_pcY=0, g_pcW=0, g_pcH=0;
int g_pcBars=64, g_pcOffset=0, g_pcPage=0, g_pcTradePage=0;
bool g_pcFitOrders=true;
datetime g_pcLatest=0;
double g_pcLow=0, g_pcHigh=1;
int g_pcTop=42, g_pcBottom=0, g_pcRight=0;
uint g_pcLastMs=0, g_pcQuoteSeenMs=0;
datetime g_pcQuoteTime=0;
struct PanelLevel
  {
   double price;
   string text;
   color ink;
  };

bool PanelEnabled()
  {
   return showDashboardPanel && showLiveChartPanel && (!IsTesting() || IsVisualMode());
  }

void PanelRestore()
  {
   if(!g_pcSaved) return;
   ChartSetInteger(0,CHART_SHOW_TRADE_LEVELS,g_pcOldLevels);
   ChartSetInteger(0,CHART_FOREGROUND,g_pcOldForeground);
   g_pcSaved=false;
  }

void PanelDestroy()
  {
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
   return 12+(int)MathRound((count-1-index+0.5)*(g_pcRight-20)/(double)count);
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
   ObjectSetInteger(0,name,OBJPROP_BGCOLOR,C'34,47,60');
   ObjectSetInteger(0,name,OBJPROP_COLOR,clrWhite);
   ObjectSetInteger(0,name,OBJPROP_BORDER_COLOR,C'58,78,96');
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,8);
   ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,name,OBJPROP_ZORDER,50);
   ObjectSetInteger(0,name,OBJPROP_STATE,false);
   ObjectSetString(0,name,OBJPROP_TEXT,caption);
  }

void PanelAddLevel(PanelLevel &levels[],double price,string text,color ink)
  {
   if(price<=0) return;
   int n=ArraySize(levels);
   if(ArrayResize(levels,n+1)!=n+1) return;
   levels[n].price=price;
   levels[n].text=text;
   levels[n].ink=ink;
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
   int tickets[];
   for(int i=0;i<OrdersTotal();i++)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderCloseTime()!=0 || !IsMatchingOrderIdentity()) continue;
      if(OrderType()<OP_BUY || OrderType()>OP_SELLSTOP) continue;
      int n=ArraySize(tickets);
      if(ArrayResize(tickets,n+1)==n+1) tickets[n]=OrderTicket();
     }
   // Stable pagination even when the terminal reorders its trade pool.
   ArraySort(tickets);
   int pageRows=(g_pcH>=360)?4:((g_pcH>=290)?2:1);
   int pages=(int)MathMax(1,(ArraySize(tickets)+pageRows-1)/pageRows);
   g_pcTradePage=g_pcTradePage%pages;
   int tableTop=g_pcH-52-(36+pageRows*20);
   g_pcBottom=tableTop-26;
   g_pc.FillRectangle(8,tableTop,g_pcW-8,g_pcH-51,ColorToARGB(C'20,30,40'));
   string currency=AccountCurrency();
   string unit=(currency=="USD")?"$":currency;
   PanelText(12,tableTop+2,"TRADES "+currency+" | TP/SL ~ estimated net",C'58,181,255');
   int cols[6];
   cols[0]=12;
   cols[1]=12+(g_pcW-24)*22/100;
   cols[2]=12+(g_pcW-24)*44/100;
   cols[3]=12+(g_pcW-24)*63/100;
   cols[4]=12+(g_pcW-24)*82/100;
   cols[5]=g_pcW-12;
   string heads[5];
   heads[0]="TICKET"; heads[1]="TYPE"; heads[2]="LIVE "+unit;
   heads[3]="TP~ "+unit; heads[4]="SL~ "+unit;
   for(int h=0;h<5;h++) PanelCell(cols[h],tableTop+18,cols[h+1]-cols[h],heads[h],clrSilver);
   if(ArraySize(tickets)==0) PanelText(12,tableTop+36,"No matching trades",clrSilver);
   for(int row=0;row<pageRows;row++)
     {
      int index=g_pcTradePage*pageRows+row;
      if(index>=ArraySize(tickets)) break;
      if(!OrderSelect(tickets[index],SELECT_BY_TICKET,MODE_TRADES) || OrderCloseTime()!=0) continue;
      string values[5];
      values[0]=IntegerToString(OrderTicket()); values[1]=PanelOrderName(OrderType());
      values[2]=PanelLiveMoney(); values[3]=PanelExitMoney(OrderTakeProfit()); values[4]=PanelExitMoney(OrderStopLoss());
      for(int c=0;c<5;c++)
        {
         color ink=clrSilver;
         if(c>=2 && StringFind(values[c],"+")==0) ink=C'49,214,154';
         if(c>=2 && StringFind(values[c],"-")==0) ink=C'245,100,100';
         PanelCell(cols[c],tableTop+36+row*20,cols[c+1]-cols[c],values[c],ink);
        }
     }
   PanelButton("trades","TRADES "+IntegerToString(g_pcTradePage+1)+"/"+IntegerToString(pages),
               g_pcX+g_pcW-104,g_pcY+g_pcH-26,96);
  }

void PanelDraw(bool force)
  {
   if(!PanelEnabled())
     {
      bool wasReady=g_pcReady;
      PanelDestroy();
      if(wasReady && drawResultTags) TagRelayout();
      return;
     }
   uint nowMs=GetTickCount();
   if(!force && g_pcReady && nowMs-g_pcLastMs<200) return;
   g_pcLastMs=nowMs;
   // Use actual window size, not the HUD's minimum-size assumptions.
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int ch=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS);
   int x=g_px[0]+g_pw[0]+8, y=96;
   int w=cw-281-8-x, h=ch-152-8-y;
   // Fall back to native chart if there is not enough room for a readable panel.
   if(w<400 || h<240)
     {
      bool hadPanel=g_pcReady;
      PanelDestroy();
      if(hadPanel && drawResultTags) TagRelayout();
      return;
     }
   if(!g_pcReady || w!=g_pcW || h!=g_pcH || x!=g_pcX || y!=g_pcY)
     {
      if(g_pcReady) g_pc.Destroy();
      ObjectsDeleteAll(0,PC_BUTTON); // Recreate controls above the new bitmap.
      g_pcReady=false;
      if(!g_pc.CreateBitmapLabel(0,0,PC_NAME,x,y,w,h,COLOR_FORMAT_ARGB_NORMALIZE))
        {
         Print("gold_x9: custom chart allocation failed: ",GetLastError());
         g_pc.Destroy(); // Also release partially allocated resources.
         PanelDestroy();
         if(drawResultTags) TagRelayout();
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
         g_pcSaved=true;
        }
      ChartSetInteger(0,CHART_SHOW_TRADE_LEVELS,false);
      ChartSetInteger(0,CHART_FOREGROUND,false);
      // Replace native result objects, keeping their history state intact.
      ObjectsDeleteAll(0,TAG_PREFIX);
     }
   g_pc.Erase(ColorToARGB(C'12,18,26'));
   g_pcRight=w-83; g_pcBottom=h-52;
   PanelText(10,9,activeTradeSymbol+" M"+IntegerToString(Period()),C'58,181,255');
   PanelButton("in","+",x+w-240,y+5,24);
   PanelButton("out","-",x+w-214,y+5,24);
   PanelButton("older","<",x+w-188,y+5,24);
   PanelButton("newer",">",x+w-162,y+5,24);
   PanelButton("live","LIVE",x+w-136,y+5,40);
   PanelButton("range",g_pcFitOrders?"ALL":"BARS",x+w-94,y+5,40);
   PanelButton("page","TAG>",x+w-52,y+5,44);

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
      PanelText(15,65,"Waiting for broker candle history...",clrSilver);
      g_pc.Update(); return;
     }
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
      double net=OrderProfit()+OrderSwap()-CommissionCost(OrderLots());
      string ticket="#"+IntegerToString(OrderTicket());
      string text=ticket+" "+PanelOrderName(type)+" "+DoubleToString(OrderLots(),2);
      text+=" LIVE "+PanelLiveMoney();
      color ink=market ? (net>=0 ? C'49,214,154' : C'245,100,100') : C'240,178,65';
      PanelAddLevel(levels,OrderOpenPrice(),text,ink);
      PanelAddLevel(levels,OrderStopLoss(),ticket+" SL~ "+PanelExitMoney(OrderStopLoss()),C'245,100,100');
      PanelAddLevel(levels,OrderTakeProfit(),ticket+" TP~ "+PanelExitMoney(OrderTakeProfit()),C'49,214,154');
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
   for(int grid=0;grid<=4;grid++)
     {
      double price=g_pcLow+(g_pcHigh-g_pcLow)*grid/4.0;
      int gy=PanelPriceY(price);
      g_pc.Line(10,gy,g_pcRight,gy,ColorToARGB(C'33,46,59'));
      PanelText(g_pcRight+5,gy-6,DoubleToString(price,activeSymbolDigits),clrSilver);
     }
   int body=(int)MathMax(1,MathMin(9,(g_pcRight-20)/count-2));
   for(int bar=count-1;bar>=0;bar--)
     {
      int bx=PanelBarX(bar,count);
      uint ink=ColorToARGB(rates[bar].close>=rates[bar].open ? C'0,190,170' : C'235,82,82');
      g_pc.Line(bx,PanelPriceY(rates[bar].high),bx,PanelPriceY(rates[bar].low),ink);
      int top=PanelPriceY(MathMax(rates[bar].open,rates[bar].close));
      int bottom=(int)MathMin(g_pcBottom,MathMax(top+1,PanelPriceY(MathMin(rates[bar].open,rates[bar].close))));
      g_pc.FillRectangle(bx-body/2,top,bx+body/2,bottom,ink);
     }
   // Every level remains at its true price; labels use separate stacked rows
   // with connector lines, so nearby entries never overwrite each other.
   for(int a=1;a<ArraySize(levels);a++)
     {
      PanelLevel v=levels[a]; int b=a-1;
      while(b>=0)
        {
         if(levels[b].price>=v.price) break;
         levels[b+1]=levels[b]; b--;
        }
      levels[b+1]=v;
     }
   int rows=(int)MathMax(1,(g_pcBottom-g_pcTop-8)/18);
   int pages=(int)MathMax(1,(ArraySize(levels)+rows-1)/rows);
   g_pcPage=g_pcPage%pages;
   for(int line=0;line<ArraySize(levels);line++)
     {
      bool inRange=(levels[line].price>=g_pcLow && levels[line].price<=g_pcHigh);
      int ly=PanelPriceY(levels[line].price);
      if(inRange) PanelDash(ly,levels[line].ink);
      if(line/rows!=g_pcPage) continue;
      int labelY=g_pcTop+4+(line%rows)*18;
      string label=levels[line].text+" @"+DoubleToString(levels[line].price,activeSymbolDigits);
      if(!inRange) label+=(levels[line].price>g_pcHigh?" ^":" v");
      // Width bounds keep labels and connectors inside the plot at any zoom.
      int labelW=(int)MathMin(g_pcRight-125,g_pc.TextWidth(label)+8);
      if(g_pc.TextWidth(label)>labelW-8)
        {
         while(g_pc.TextWidth(label+"...")>labelW-8 && StringLen(label)>4)
            label=StringSubstr(label,0,StringLen(label)-1);
         label+="..."; // Full ticket/price details are available in the panel tooltip.
        }
      if(inRange) g_pc.Line(labelW+16,labelY+7,g_pcRight-2,ly,ColorToARGB(levels[line].ink,120));
      g_pc.FillRectangle(12,labelY,16+labelW,labelY+15,ColorToARGB(C'20,30,40',235));
      PanelText(16,labelY,label,levels[line].ink);
     }
   // A few time-anchored realized results from the existing tag cache.
   int marked=0; int lastX[4]; int lastY[4];
   if(drawResultTags)
      for(int k=g_tagN-1;k>=MathMax(0,g_tagN-TAG_MAX) && marked<4;k--)
        {
         int slot=k%TAG_MAX;
         if(g_tagTime[slot]<rates[count-1].time) continue;
         int shift=iBarShift(activeTradeSymbol,Period(),g_tagTime[slot],false)-g_pcOffset;
         if(shift<0 || shift>=count) continue;
         if(g_tagPrice[slot]<g_pcLow || g_tagPrice[slot]>g_pcHigh) continue;
         int mx=PanelBarX(shift,count), my=PanelPriceY(g_tagPrice[slot]);
         // Keep result badges out of the occupied order-label region.
         int usedRows=(int)MathMin(rows,ArraySize(levels)-g_pcPage*rows);
         if(ArraySize(levels)>0 && mx<g_pcRight-100 && my<g_pcTop+4+usedRows*18) continue;
         if(my<g_pcTop+12 || my>g_pcBottom-18) continue;
         bool collision=false;
         for(int c=0;c<marked;c++)
            if(MathAbs(mx-lastX[c])<80 && MathAbs(my-lastY[c])<22) collision=true;
         if(collision) continue;
         string result=(g_tagProfit[slot]>=0?"+":"")+DoubleToString(g_tagProfit[slot],2);
         int rw=g_pc.TextWidth(result)+8;
         int rx=(int)MathMin(mx,g_pcRight-rw);
         g_pc.FillRectangle(rx,my,rx+rw,my+14,ColorToARGB(C'20,30,40'));
         PanelText(rx+4,my,result,g_tagClr[slot]);
         lastX[marked]=mx; lastY[marked]=my; marked++;
        }
   if(quoted && tick.bid>=g_pcLow && tick.bid<=g_pcHigh)
     {
      int by=PanelPriceY(tick.bid);
      PanelDash(by,C'58,181,255');
      g_pc.FillRectangle(g_pcRight+1,by-7,w-2,by+8,ColorToARGB(C'18,90,130'));
      PanelText(g_pcRight+4,by-6,DoubleToString(tick.bid,activeSymbolDigits),clrWhite);
     }
   PanelText(12,g_pcBottom+9,TimeToString(rates[count-1].time,TIME_DATE|TIME_MINUTES),clrSilver);
   PanelText((int)MathMax(165,g_pcRight-110),g_pcBottom+9,TimeToString(rates[0].time,TIME_MINUTES),clrSilver);
   string feed=quoted ? "Tick "+TimeToString(tick.time,TIME_SECONDS) : "No quote";
   if(quoted && (TimeCurrent()-tick.time>60 || nowMs-g_pcQuoteSeenMs>60000)) feed+=" (STALE)";
   string footer=(g_pcOffset==0?"LIVE | ":"HISTORY | ")+feed+" | Tags "+IntegerToString(g_pcPage+1)+"/"+IntegerToString(pages);
   PanelCell(12,h-20,w-124,footer,C'58,181,255');
   g_pc.Update();
  }

bool PanelClick(string name)
  {
   if(StringFind(name,PC_BUTTON)!=0) return false;
   string key=StringSubstr(name,StringLen(PC_BUTTON));
   if(key=="in") g_pcBars=(int)MathMax(16,g_pcBars-16);
   if(key=="out") g_pcBars=(int)MathMin(240,g_pcBars+16);
   if(key=="older") g_pcOffset+=g_pcBars/2;
   if(key=="newer") g_pcOffset=(int)MathMax(0,g_pcOffset-g_pcBars/2);
   if(key=="live") g_pcOffset=0;
   if(key=="range") g_pcFitOrders=!g_pcFitOrders;
   if(key=="page") g_pcPage++;
   if(key=="trades") g_pcTradePage++;
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

bool TagSeen(int ticket, datetime ct)
  {
   int lim = (g_tagSeenN < TAG_MAX) ? g_tagSeenN : TAG_MAX;
   for(int i = 0; i < lim; i++)
      if(g_tagSeenTkt[i] == ticket && g_tagSeenTm[i] == ct) return true;
   return false;
  }

void TagMark(int ticket, datetime ct)
  {
   int slot = g_tagSeenN % TAG_MAX;
   g_tagSeenTkt[slot] = ticket;
   g_tagSeenTm [slot] = ct;
   g_tagSeenN++;
  }

//=== C2: SOLID RAISED BOX CARD & MERGED TRADE RESULT DRAWING ===============
void TagBoxCardDraw(string name, datetime t, double p, string text, color borderClr, bool isBuy, int count)
  {
   string bgName   = name + "card_bg";
   string textName = name + "card_txt";

   // 1. Calculate screen coordinates for GUI label card
   int subWin = 0;
   int xPixels = 0;
   int yPixels = 0;
   bool isVisible = ChartTimePriceToXY(0, subWin, t, p, xPixels, yPixels);

   color bgPlateClr = C'20,25,32'; // Solid dark titanium plate
   color textClr    = clrWhite;

   //--- Screen Pixel Raised 3D Card (Primary) ---
   if(isVisible && xPixels > 0 && yPixels > 0)
     {
      // Clean up fallback objects if existing
      ObjectDelete(0, name + "fb_bg");
      ObjectDelete(0, name + "fb_txt");

      int charWidth = (tagFontSize > 0) ? (tagFontSize - 1) : 7;
      int textLen   = StringLen(text);
      int cardWidth = textLen * charWidth + 18;
      if(cardWidth < 70) cardWidth = 70;
      int cardHeight = 22;

      // Adjust Y anchor relative to price candle
      int cardX = xPixels + 10;
      int cardY = isBuy ? (yPixels - 28) : (yPixels + 8);
      if(cardY < 10) cardY = 10;

      // Create or update solid raised rectangle label
      if(ObjectFind(0, bgName) < 0)
        {
         ResetLastError();
         if(!ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0))
           {
            g_tagFail++;
            return;
           }
         g_tagMade++;
        }
      ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, cardX);
      ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, cardY);
      ObjectSetInteger(0, bgName, OBJPROP_XSIZE,     cardWidth);
      ObjectSetInteger(0, bgName, OBJPROP_YSIZE,     cardHeight);
      ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR,   bgPlateClr);
      ObjectSetInteger(0, bgName, OBJPROP_COLOR,     borderClr);
      ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_RAISED);
      ObjectSetInteger(0, bgName, OBJPROP_BACK,      false);
      ObjectSetInteger(0, bgName, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, bgName, OBJPROP_SELECTED,   false);
      ObjectSetInteger(0, bgName, OBJPROP_HIDDEN,     tagHidden);

      // Create or update text inside the card
      if(ObjectFind(0, textName) < 0)
        {
         ResetLastError();
         if(!ObjectCreate(0, textName, OBJ_LABEL, 0, 0, 0))
           {
            g_tagFail++;
            return;
           }
         g_tagMade++;
        }
      ObjectSetInteger(0, textName, OBJPROP_XDISTANCE, cardX + 6);
      ObjectSetInteger(0, textName, OBJPROP_YDISTANCE, cardY + 3);
      ObjectSetString (0, textName, OBJPROP_TEXT,      text);
      ObjectSetInteger(0, textName, OBJPROP_COLOR,     textClr);
      ObjectSetInteger(0, textName, OBJPROP_FONTSIZE,  tagFontSize);
      ObjectSetString (0, textName, OBJPROP_FONT,      tagFontName);
      ObjectSetInteger(0, textName, OBJPROP_BACK,      false);
      ObjectSetInteger(0, textName, OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0, textName, OBJPROP_SELECTED,  false);
      ObjectSetInteger(0, textName, OBJPROP_HIDDEN,    tagHidden);
     }
   else
     {
      //--- Fallback Chart Object (For Off-Screen or Tester Mode) ---
      ObjectDelete(0, bgName);
      ObjectDelete(0, textName);

      string fbTxt = name + "fb_txt";
      if(ObjectFind(0, fbTxt) < 0)
        {
         ResetLastError();
         if(!ObjectCreate(0, fbTxt, OBJ_TEXT, 0, t, p))
           {
            g_tagFail++;
            return;
           }
         g_tagMade++;
        }
      ObjectMove(0, fbTxt, 0, t, p);
      ObjectSetString (0, fbTxt, OBJPROP_TEXT,      text);
      ObjectSetInteger(0, fbTxt, OBJPROP_COLOR,     borderClr);
      ObjectSetInteger(0, fbTxt, OBJPROP_FONTSIZE,  tagFontSize);
      ObjectSetString (0, fbTxt, OBJPROP_FONT,      tagFontName);
      ObjectSetInteger(0, fbTxt, OBJPROP_ANCHOR,    isBuy ? ANCHOR_LEFT_LOWER : ANCHOR_LEFT_UPPER);
      ObjectSetInteger(0, fbTxt, OBJPROP_BACK,      tagBehindChart);
      ObjectSetInteger(0, fbTxt, OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0, fbTxt, OBJPROP_SELECTED,  false);
      ObjectSetInteger(0, fbTxt, OBJPROP_HIDDEN,    tagHidden);
     }
  }

void TagRelayout()
  {
   if(g_pcReady) return; // Custom panel draws its own clipped result badges.
   // Array tracking which slot indices have been merged/processed
   bool processed[TAG_MAX];
   ArrayInitialize(processed, false);

   int activeIndices[TAG_MAX];
   ArrayInitialize(activeIndices, -1);

   for(int i = 0; i < TAG_MAX; i++)
     {
      if(g_tagBase[i] == "") continue;
      if(processed[i]) continue;

      // Group trades closing at the same time and price
      int    groupCount   = 0;
      double sumProfit    = 0.0;
      double sumPoints    = 0.0;
      bool   groupIsBuy   = g_tagIsBuy[i];
      datetime groupTime  = g_tagTime[i];
      double groupPrice   = g_tagPrice[i];

      ArrayInitialize(activeIndices, -1);

      for(int j = i; j < TAG_MAX; j++)
        {
         if(g_tagBase[j] == "") continue;
         if(processed[j]) continue;

         // Match trades closed within 3 seconds, at same price & type
         if(g_tagIsBuy[j] == groupIsBuy && 
            MathAbs((long)(g_tagTime[j] - groupTime)) <= 3 && 
            MathAbs(g_tagPrice[j] - groupPrice) < (activeSymbolPoint * 2.0))
           {
            processed[j] = true;
            activeIndices[groupCount] = j;
            sumProfit += g_tagProfit[j];
            sumPoints += g_tagPoints[j];
            groupCount++;
           }
        }

      if(groupCount <= 0) continue;

      // Calculate averages and format output text
      double avgPts    = sumPoints / (double)groupCount;
      int    intAvgPts = (int)MathRound(avgPts);

      string dir    = groupIsBuy ? "BUY " : "SELL ";
      string countPrefix = (groupCount > 1) ? (IntegerToString(groupCount) + "x ") : "";
      string plText = (sumProfit >= 0.0 ? "+" : "") + DoubleToString(sumProfit, 2);
      string ptText = (intAvgPts >= 0 ? "+" : "") + IntegerToString(intAvgPts) + " pts";
      string cardText = countPrefix + dir + plText + " (" + ptText + ")";
      color  cardClr  = (sumProfit >= 0.0) ? tagWinColor : tagLossColor;

      // Primary slot base object name
      string primaryName = g_tagBase[i];

      // Delete secondary card objects for merged trades
      for(int k = 1; k < groupCount; k++)
        {
         int secIdx = activeIndices[k];
         if(secIdx >= 0 && g_tagBase[secIdx] != "")
           {
            ObjectsDeleteAll(0, g_tagBase[secIdx]);
           }
        }

      // Draw single solid raised box card for the merged group
      TagBoxCardDraw(primaryName, groupTime, groupPrice, cardText, cardClr, groupIsBuy, groupCount);
     }
  }

bool TagDrawOne(int ticket)
  {
   if(ticket <= 0) return false;
   if(!OrderSelect(ticket, SELECT_BY_TICKET, MODE_HISTORY)) return false;

   if(!IsMatchingOrder()) return false;

   datetime ct = OrderCloseTime();
   if(ct <= 0) return false;
   if(TagSeen(ticket, ct)) return false;
   TagMark(ticket, ct);

   int    t     = OrderType();
   bool   isBuy = (t == OP_BUY);
   double op    = OrderOpenPrice();
   double cp    = OrderClosePrice();
   double pl    = OrderProfit() + OrderSwap() - CommissionCost(OrderLots());
   if(cp <= 0.0) return false;

   // Points calculation
   double pDiff  = isBuy ? (cp - op) : (op - cp);
   int    points = (int)MathRound(pDiff / activeSymbolPoint);

   // Slot in ring buffer
   int slot = g_tagN % TAG_MAX;
   if(g_tagBase[slot] != "")
     {
      ObjectsDeleteAll(0, g_tagBase[slot]);
     }

   g_tagBase  [slot] = TAG_PREFIX + IntegerToString(ticket) + " *" + IntegerToString((int)ct) + "* ";
   g_tagTime  [slot] = ct;
   g_tagOpen  [slot] = OrderOpenTime();
   g_tagPrice [slot] = cp;
   g_tagProfit[slot] = pl;
   g_tagPoints[slot] = points;
   g_tagIsBuy [slot] = isBuy;

   // Pre-format text & color
   string dir    = isBuy ? "BUY " : "SELL ";
   string plText = (pl >= 0.0 ? "+" : "") + DoubleToString(pl, 2);
   string ptText = (points >= 0 ? "+" : "") + IntegerToString(points) + " pts";
   g_tagText  [slot] = dir + plText + " (" + ptText + ")";
   g_tagClr   [slot] = (pl >= 0.0) ? tagWinColor : tagLossColor;
   g_tagN++;

   TagRelayout();
   ChartRedraw(0);

   if(tagDebug)
      Print("gold_x9 C2: box card result tag drawn. Ticket=", ticket, " ", dir, " P/L ", plText, " (", ptText, ") at ", TimeToString(ct));
   return true;
  }

void TagScan(bool force)
  {
   if(!drawResultTags) return;
   if(IsTesting() && !IsVisualMode() && !tagDrawInTester) return;

   if(!force)
     {
      uint ms   = GetTickCount();
      uint wait = (uint)(tagScanSeconds * 1000);
      if(wait < 200) wait = 200;
      if(g_lastTagMs != 0 && (ms - g_lastTagMs) < wait) return;
      g_lastTagMs = ms;
     }

   int total = OrdersHistoryTotal();
   int start = 0;
   if(!force)
     {
      if(total == g_tagHistTotal) return;
      if(g_tagHistTotal > 0 && total > g_tagHistTotal)
        {
         start = g_tagHistTotal - 20;
         if(start < 0) start = 0;
        }
     }

   int drawn = 0;
   for(int i = total - 1; i >= start; i--)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(TagDrawOne(OrderTicket())) drawn++;
     }

   g_tagHistTotal = total;
   TagTrim();
  }

void TagInitHistory()
  {
   if(!drawResultTags) return;
   if(IsTesting() && !IsVisualMode() && !tagDrawInTester) return;

   int total = OrdersHistoryTotal();
   int want  = tagLookbackTrades;
   if(want < 0) want = 0;

   int drawn   = 0;
   int matched = 0;
   for(int i = total - 1; i >= 0; i--)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(!IsMatchingOrder()) continue;
      matched++;

      int      tk = OrderTicket();
      datetime ct = OrderCloseTime();
      if(ct <= 0 || TagSeen(tk, ct)) continue;

      if(!tagDrawOnInitHistory || (want > 0 && matched > want))
        { TagMark(tk, ct); continue; }
      if(TagDrawOne(tk)) drawn++;
     }

   g_tagHistTotal = total;
   TagTrim();
   if(tagDebug) Print("gold_x9 C2: history scan - ", drawn, " tag(s) drawn (lookback=", want, ").");
   if(drawn > 0) ChartRedraw(0);
  }

void TagTrim()
  {
   if(!drawResultTags) return;
   int lim = (g_tagN < TAG_MAX) ? g_tagN : TAG_MAX;
   if(tagMaxAgeHours > 0)
     {
      datetime cutoff = TimeCurrent() - (datetime)(tagMaxAgeHours * 3600);
      for(int i = 0; i < lim; i++)
        {
         if(g_tagBase[i] == "") continue;
         if(g_tagTime[i] < cutoff)
           {
            ObjectsDeleteAll(0, g_tagBase[i]);
            g_tagBase[i] = "";
            g_tagTime[i] = 0;
           }
        }
     }

   if(tagMaxOnChart <= 0) return;
   int live = 0;
   for(int i = 0; i < lim; i++) if(g_tagBase[i] != "") live++;

   while(live > tagMaxOnChart)
     {
      int      oldest = -1;
      datetime ot     = 0;
      for(int i = 0; i < lim; i++)
        {
         if(g_tagBase[i] == "") continue;
         if(oldest < 0 || g_tagTime[i] < ot)
           { oldest = i; ot = g_tagTime[i]; }
        }
      if(oldest < 0) break;
      ObjectsDeleteAll(0, g_tagBase[oldest]);
      g_tagBase[oldest] = "";
      g_tagTime[oldest] = 0;
      live--;
     }
  }

void TagDeleteAll()
  {
   ObjectsDeleteAll(0, TAG_PREFIX);
   for(int i = 0; i < TAG_MAX; i++)
     {
      g_tagBase[i]    = "";
      g_tagTime[i]    = 0;
      g_tagSeenTkt[i] = 0;
      g_tagSeenTm[i]  = 0;
     }
   g_tagN         = 0;
   g_tagSeenN     = 0;
   g_tagHistTotal = 0;
  }

//=== C2: smooth equity curve ===
#define EQ_PLOT_W 249
#define EQ_PLOT_H 85

void EqPush(double v, datetime t)
  {
   int idx = g_eqN % EQ_MAX;
   g_eqVal[idx] = v;
   g_eqT[idx]   = t;
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

#define EQ_COL_MAX 72

void EqCellSet(string name, int x, int y, int w, int h, color clr, bool used)
  {
   if(!used) { ObjectDelete(0, name); return; }
   if(ObjectFind(0, name) < 0)
     {
      ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_CORNER,      CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_ANCHOR,      ANCHOR_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE,  false);
      ObjectSetInteger(0, name, OBJPROP_HIDDEN,      true);
      ObjectSetInteger(0, name, OBJPROP_BACK,        false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER,      1);
     }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE,     w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE,     h);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR,   clr);
   ObjectSetInteger(0, name, OBJPROP_COLOR,     clr);
   ObjectSetInteger(0, name, OBJPROP_FILL,      true);
  }

void EqDraw()
  {
   if(!showEquityCurve || !showDashboardPanel) return;
   if(g_pw[4] <= 0) return;
   int ox = g_px[4] + 14;
   int oy = g_py[4] + 35;
   int kept = EqCount();
   int nUse = (kept < eqCurveSamples) ? kept : eqCurveSamples;
   if(nUse > 96) nUse = 96;

   if(nUse < 2)
     {
      for(int d = 0; d < EQ_COL_MAX; d++)
        {
         EqCellSet(HUD_PREFIX + "eql" + IntegerToString(d), 0, 0, 0, 0, clrBlack, false);
         EqCellSet(HUD_PREFIX + "eqf" + IntegerToString(d), 0, 0, 0, 0, clrBlack, false);
        }
      return;
     }

   double ptsX[96], ptsY[96];
   ArrayInitialize(ptsX, 0.0); ArrayInitialize(ptsY, 0.0);
   double mn = 1e18, mx = -1e18;
   double v; datetime t;
   int first = kept - nUse;
   for(int i = 0; i < nUse; i++)
     {
      EqItem(first + i, v, t);
      if(v < mn) mn = v;
      if(v > mx) mx = v;
     }
   if(mx - mn < 1e-9) { mx += 1.0; mn -= 1.0; }
   for(int i2 = 0; i2 < nUse; i2++)
     {
      EqItem(first + i2, v, t);
      ptsX[i2] = 4.0 + (double)i2 * (EQ_PLOT_W - 8.0) / (double)(nUse - 1);
      ptsY[i2] = EQ_PLOT_H - 6.0 - (v - mn) / (mx - mn) * (EQ_PLOT_H - 14.0);
     }

   color lineC = UiCurve();
   color fillC = C'14,34,24';
   int   plotBottom = oy + EQ_PLOT_H - 2;

   for(int j = 0; j < EQ_COL_MAX; j++)
     {
      double tt = (double)j * (double)(nUse - 1) / (double)(EQ_COL_MAX - 1);
      int    s  = (int)MathFloor(tt);
      if(s > nUse - 2) s = nUse - 2;
      double u  = tt - s, u2 = u * u, u3 = u2 * u;
      int i0 = (s > 0) ? s - 1 : 0;
      int i3 = (s + 2 < nUse) ? s + 2 : nUse - 1;
      double xx = 0.5 * ((2 * ptsX[s]) + (-ptsX[i0] + ptsX[s + 1]) * u + (2 * ptsX[i0] - 5 * ptsX[s] + 4 * ptsX[s + 1] - ptsX[i3]) * u2 + (-ptsX[i0] + 3 * ptsX[s] - 3 * ptsX[s + 1] + ptsX[i3]) * u3);
      double yy = 0.5 * ((2 * ptsY[s]) + (-ptsY[i0] + ptsY[s + 1]) * u + (2 * ptsY[i0] - 5 * ptsY[s] + 4 * ptsY[s + 1] - ptsY[i3]) * u2 + (-ptsY[i0] + 3 * ptsY[s] - 3 * ptsY[s + 1] + ptsY[i3]) * u3);

      int cx = ox + (int)xx;
      int cy = oy + (int)yy;
      string idj = IntegerToString(j);
      EqCellSet(HUD_PREFIX + "eqf" + idj, 0, 0, 0, 0, fillC, false);
      EqCellSet(HUD_PREFIX + "eql" + idj, cx - 2, cy - 1, 5, 3, lineC, true);
     }
  }

void SeedEquityHistory()
  {
   g_eqN = 0;
   double start = AccountBalance() - g_totalClosedPL;
   EqPush(start, TimeCurrent());
   int total = OrdersHistoryTotal();
   double cum = start;
   for(int i = 0; i < total; i++)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(!IsMatchingOrder()) continue;
      cum += OrderProfit() + OrderSwap() - CommissionCost(OrderLots());
      EqPush(cum, OrderCloseTime());
     }
  }

int OnInit()
  {
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
   if(g_activeTheme<0||g_activeTheme>5)g_activeTheme=0;
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

   g_lastTagMs = 0;
   g_tagMade   = 0;
   g_tagFail   = 0;
   if(drawResultTags)
     {
      if(!tagKeepOnExit) TagDeleteAll();
      ChartSetInteger(0, CHART_SHOW_OBJECT_DESCR, true);
      SeedEquityHistory();
      TagInitHistory();
      TagRelayout();
     }

   HudTick(true);
   EqDraw();
   PanelDraw(true);
   if(PanelEnabled()) EventSetTimer(1);

   Print("gold_x9 v6.57 (MQL4) initialised on ", activeTradeSymbol, " digits=", activeSymbolDigits, " point=", DoubleToString(activeSymbolPoint, activeSymbolDigits), " tags=", (drawResultTags ? "on" : "off"), " hud=", (showDashboardPanel ? "on" : "off"));
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   PanelDestroy();
   ObjectsDeleteAll(0, HUD_PREFIX);
   if(!tagKeepOnExit) TagDeleteAll();
   else if(drawResultTags) TagRelayout(); // Recreate native tags when keeping them on exit.
   ChartRedraw(0);
  }

void OnTimer()
  {
   // Display-only refresh: no order-management calls from the timer.
   PanelDraw(false);
  }

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
  {
   if(id==CHARTEVENT_OBJECT_CLICK && PanelClick(sparam)) return;
   if(id==CHARTEVENT_OBJECT_CLICK && StringFind(sparam,HUD_PREFIX+"theme_")==0)
     {
      int nt=(int)StringToInteger(StringSubstr(sparam,StringLen(HUD_PREFIX+"theme_")));
      if(nt>=0 && nt<=5 && nt!=g_activeTheme)
        {
         g_activeTheme=nt;
         ObjectsDeleteAll(0,HUD_PREFIX);
         g_hN=0;
         ApplyChartStyle();
         HudLayout();
         HudCreate();
         HudLayout();
         HudTick(true);
         EqDraw();
         if(drawResultTags) TagRelayout();
         PanelDraw(true);
         ChartRedraw(0);
        }
      return;
     }
   if(id!=CHARTEVENT_CHART_CHANGE)return;
   uint ms=GetTickCount();
   if(ms-g_lastChartChgMs<200)return;
   g_lastChartChgMs=ms;
   if(showDashboardPanel){HudLayout();EqDraw();}
   if(drawResultTags)TagRelayout();
   PanelDraw(true);
  }

void OnTick()
  {
   activateStrategyContext();
   TrackEquityAndDD();
   HudTick(false);
   TagScan(false);
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

         if(isBuy  && trSL > newSL) { newSL = trSL; changed = true; }
         if(!isBuy && (newSL <= 0.0 || trSL < newSL)) { newSL = trSL; changed = true; }
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
         Print("gold_x9: position ", selTicket, " managed. fav=", DoubleToString(favorablePct, 3), "% loss=", DoubleToString(lossPct, 3), "% SL ", DoubleToString(curSL, activeSymbolDigits), " -> ", DoubleToString(newSL, activeSymbolDigits), " TP ", DoubleToString(curTP, activeSymbolDigits), " -> ", DoubleToString(newTP, activeSymbolDigits));
        }

      Sleep(200);
     }
  }

void ApplyChartStyle()
  {
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

uint g_lastEqLiveMs = 0;

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

string ThemeCode()
  {
   switch(g_activeTheme)
     {
      case HUD_DARK_TITANIUM: return "T";
      case HUD_GOLD_EXECUTIVE: return "G";
      case HUD_SLATE_PRO: return "S";
      case HUD_EMERALD_CARBON: return "E";
      case HUD_ARCTIC_BLUE: return "A";
      default: return "L";
     }
  }

color UiInk(){if(g_activeTheme==HUD_DARK_TITANIUM||g_activeTheme==HUD_EMERALD_CARBON)return C'235,240,244'; return C'5,10,16';}
color UiDim(){if(g_activeTheme==HUD_DARK_TITANIUM||g_activeTheme==HUD_EMERALD_CARBON)return C'155,166,176'; return C'72,82,91';}
color UiPanel(){switch(g_activeTheme){case HUD_DARK_TITANIUM:return C'31,38,46';case HUD_GOLD_EXECUTIVE:return C'248,244,232';case HUD_SLATE_PRO:return C'226,233,239';case HUD_EMERALD_CARBON:return C'18,31,29';case HUD_ARCTIC_BLUE:return C'235,246,252';default:return C'241,245,247';}}
color UiBand(){switch(g_activeTheme){case HUD_DARK_TITANIUM:return C'44,53,63';case HUD_GOLD_EXECUTIVE:return C'235,226,201';case HUD_SLATE_PRO:return C'207,218,227';case HUD_EMERALD_CARBON:return C'27,46,42';case HUD_ARCTIC_BLUE:return C'216,235,246';default:return C'222,230,235';}}
color UiAccent(){switch(g_activeTheme){case HUD_DARK_TITANIUM:return C'58,181,255';case HUD_GOLD_EXECUTIVE:return C'166,119,24';case HUD_SLATE_PRO:return C'30,91,139';case HUD_EMERALD_CARBON:return C'25,205,141';case HUD_ARCTIC_BLUE:return C'0,119,190';default:return C'8,101,195';}}
color UiGood(){return (g_activeTheme==HUD_GOLD_EXECUTIVE)?C'25,132,73':C'0,155,83';}
color UiBad(){return C'220,45,45';}
color UiAmber(){return (g_activeTheme==HUD_GOLD_EXECUTIVE)?C'184,112,0':C'232,126,0';}
color UiCurve(){return UiAccent();}
color UiChartBg(){switch(g_activeTheme){case HUD_DARK_TITANIUM:return C'12,18,26';case HUD_GOLD_EXECUTIVE:return C'29,32,38';case HUD_SLATE_PRO:return C'21,32,44';case HUD_EMERALD_CARBON:return C'8,20,18';case HUD_ARCTIC_BLUE:return C'226,240,248';default:return C'236,241,245';}}
color UiChartFg(){return (g_activeTheme==HUD_ARCTIC_BLUE||g_activeTheme==HUD_LIGHT_SPORT)?C'34,45,55':C'191,201,210';}
color UiBull(){switch(g_activeTheme){case HUD_GOLD_EXECUTIVE:return C'32,176,112';case HUD_EMERALD_CARBON:return C'49,214,154';default:return C'0,151,167';}}
color UiBear(){return (g_activeTheme==HUD_GOLD_EXECUTIVE)?C'225,162,45':C'235,82,82';}

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

void HudBitmapObj(string name, int panel, int dx, int dy, string resourceName)
  {
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_BITMAP_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
   ObjectSetString (0, name, OBJPROP_BMPFILE, resourceName);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   if(g_hN < HUD_MAXO)
     {
      g_hName[g_hN]=name; g_hPanel[g_hN]=panel; g_hDx[g_hN]=dx; g_hDy[g_hN]=dy; g_hRA[g_hN]=0; g_hSize[g_hN]=0; g_hRect[g_hN]=2; g_hW[g_hN]=0; g_hH[g_hN]=0; g_hN++;
     }
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
   return (int)MathCeil(StringLen(s) * size * 0.62) + 2;
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
   ObjectSetString (0, name, OBJPROP_TEXT,  text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, c);
   if(g_hRA[i] == 1)
     {
      int p = g_hPanel[i];
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, g_px[p] + g_pw[p] - 15 - TextW(text, g_hSize[i]));
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, g_py[p] + g_hDy[i]);
     }
  }

void HudLayout()
  {
   g_chartW=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   g_chartH=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS);
   if(g_chartW<980) g_chartW=980;
   if(g_chartH<560) g_chartH=560;

   g_pw[0]=ACC_W; g_ph[0]=ACC_H; g_px[0]=1; g_py[0]=96;
   g_pw[1]=STR_W; g_ph[1]=STR_H; g_px[1]=g_chartW-281; g_py[1]=96;
   g_pw[2]=THM_W; g_ph[2]=THM_H; g_px[2]=1; g_py[2]=2;
   g_pw[3]=1; g_ph[3]=1; g_px[3]=0; g_py[3]=0;
   g_pw[4]=EQP_W; g_ph[4]=EQP_H; g_px[4]=g_chartW-281; g_py[4]=314;
   g_trkW=TRK_W; g_trkScale=1.0; g_pw[5]=TRK_W; g_ph[5]=TRK_H; g_px[5]=1; g_py[5]=g_chartH-152;
   HudMoveAll();
  }

void HudCreate()
  {
   g_hN=0;
   string td="::Images\\GX9\\"+ThemeCode()+"\\";
   HudBitmapObj(HUD_PREFIX+"top_bmp",2,0,0,td+"top.bmp");
   HudBitmapObj(HUD_PREFIX+"acc_bmp",0,0,0,td+"account.bmp");
   HudBitmapObj(HUD_PREFIX+"str_bmp",1,0,0,td+"strategy.bmp");
   HudBitmapObj(HUD_PREFIX+"eq_bmp",4,0,0,td+"equity.bmp");
   HudBitmapObj(HUD_PREFIX+"trk_bmp",5,0,0,td+"tracker.bmp");
   HudBitmapObj(HUD_PREFIX+"bottom_rail",5,0,150,td+"bottom.bmp");

   color paper=UiPanel(), stripe=UiBand(), ink=UiInk();
   HudRectObj(HUD_PREFIX+"top_m0",2,13,35,213,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_m1",2,246,35,169,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_m2",2,433,35,195,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_m3",2,738,35,74,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_m4",2,841,35,99,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_m5",2,959,35,108,49,paper,paper);
   HudRectObj(HUD_PREFIX+"top_ms",2,1077,45,168,31,paper,paper);
   HudRectObj(HUD_PREFIX+"dd_clear",2,626,8,90,72,paper,paper);
   HudBitmapObj(HUD_PREFIX+"dd_face",2,628,10,td+"gauge.bmp");
   for(int dn=0;dn<15;dn++) HudRectObj(HUD_PREFIX+"ddn"+IntegerToString(dn),2,671,52,3,3,UiInk(),UiInk());
   HudLabelObj(HUD_PREFIX+"top_eq",2,15,33,"0.00",ink,26,false,true);
   HudLabelObj(HUD_PREFIX+"top_net",2,247,33,"+0.00",UiGood(),26,false,true);
   HudLabelObj(HUD_PREFIX+"top_dd",2,435,36,"0.0% / 30.0%",ink,21,false,true);
   HudLabelObj(HUD_PREFIX+"top_spread",2,751,36,"0",ink,24,false,true);
   HudLabelObj(HUD_PREFIX+"top_pos",2,843,36,"0/10",ink,24,false,true);
   HudLabelObj(HUD_PREFIX+"top_next",2,960,36,"00:00",ink,24,false,true);
   HudRectObj(HUD_PREFIX+"top_status_bg",2,1079,47,164,27,UiGood(),C'0,95,52');
   HudLabelObj(HUD_PREFIX+"top_status",2,1092,50,"TRADING ACTIVE",clrWhite,11,false,true);

   for(int tb=0;tb<6;tb++)
     {
      string bn=HUD_PREFIX+"theme_"+IntegerToString(tb);
      string bf="::Images\\GX9\\B\\"+IntegerToString(tb)+((tb==g_activeTheme)?"s.bmp":"n.bmp");
      HudBitmapObj(bn,2,1077+tb*28,10,bf);
      ObjectSetInteger(0,bn,OBJPROP_SELECTABLE,true);
      ObjectSetInteger(0,bn,OBJPROP_SELECTED,false);
      ObjectSetInteger(0,bn,OBJPROP_ZORDER,30);
     }

   for(int a=0;a<9;a++) HudRectObj(HUD_PREFIX+"acc_mask"+IntegerToString(a),0,166,36+a*30,101,23,(a%2==0)?paper:stripe,(a%2==0)?paper:stripe);
   for(int av=0;av<5;av++) HudLabelObj(HUD_PREFIX+"acc_V"+IntegerToString(av),0,0,39+av*30,"-",ink,13,true,true);
   for(int aw=0;aw<4;aw++) HudLabelObj(HUD_PREFIX+"acc_W"+IntegerToString(aw),0,0,39+(aw+5)*30,"-",ink,13,true,true);

   for(int sr=0;sr<10;sr++) HudRectObj(HUD_PREFIX+"str_mask"+IntegerToString(sr),1,78,36+sr*16,190,15,(sr%2==0)?paper:stripe,(sr%2==0)?paper:stripe);
   for(int ss=1;ss<=9;ss++) HudLabelObj(HUD_PREFIX+"str_S"+IntegerToString(ss)+"_3",1,82,37+(ss-1)*16,"- / - / -",ink,9,false,true);
   HudLabelObj(HUD_PREFIX+"str_T3",1,82,181,"0 / 0.0% / +0.00",ink,9,false,true);

   HudRectObj(HUD_PREFIX+"eq_plotmask",4,12,34,256,96,paper,paper);

   HudRectObj(HUD_PREFIX+"trk_tablemask",5,8,32,1244,110,paper,paper);
   for(int rr=0;rr<5;rr++) HudRectObj(HUD_PREFIX+"trk_band"+IntegerToString(rr),5,8,50+rr*18,1244,18,(rr%2==0)?paper:stripe,(rr%2==0)?paper:stripe);
   int cx[7]; cx[0]=17; cx[1]=165; cx[2]=236; cx[3]=307; cx[4]=400; cx[5]=520; cx[6]=710;
   string hh[7]; hh[0]="DATE"; hh[1]="TRADES"; hh[2]="LOTS"; hh[3]="GAIN%"; hh[4]="COMM"; hh[5]="GROSS P/L"; hh[6]="NET";
   for(int h=0;h<7;h++) HudLabelObj(HUD_PREFIX+"trk_H"+IntegerToString(h),5,cx[h],33,hh[h],(h==3)?UiGood():ink,10,false,true);
   for(int r=0;r<5;r++) for(int c=0;c<7;c++) HudLabelObj(HUD_PREFIX+"trk_R"+IntegerToString(r)+"_"+IntegerToString(c),5,cx[c],51+r*18,"-",ink,9,false,true);
   string ml[5]; ml[0]="WIN RATE"; ml[1]="PROFIT FACTOR"; ml[2]="EXPECTANCY"; ml[3]="COST DRAG"; ml[4]="BEST / WORST";
   for(int m=0;m<5;m++)
     {
      HudLabelObj(HUD_PREFIX+"trk_SL"+IntegerToString(m),5,808,33+m*22,ml[m],ink,10,false,true);
      HudLabelObj(HUD_PREFIX+"trk_SV"+IntegerToString(m),5,0,33+m*22,"-",ink,10,true,true);
     }
   HudMoveAll();
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

void DrawLiveDDGauge()
  {
   double lim=maxAllowedDrawdownPct; if(lim<=0.0)lim=30.0;
   double ratio=MathMax(0.0,MathMin(1.0,g_currentDD/lim));
   double ang=3.141592653589793*(1.0-ratio);
   int cx=g_px[2]+671, cy=g_py[2]+57;
   color nc=(ratio>=0.85)?UiBad():((ratio>=0.55)?UiAmber():UiInk());
   for(int i=0;i<15;i++)
     {
      double rr=(double)i*2.15;
      int x=cx+(int)MathRound(MathCos(ang)*rr);
      int y=cy-(int)MathRound(MathSin(ang)*rr);
      string nm=HUD_PREFIX+"ddn"+IntegerToString(i);
      ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
      ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,nc);
      ObjectSetInteger(0,nm,OBJPROP_COLOR,nc);
     }
  }

void HudTick(bool force)
  {
   if(!showDashboardPanel) return;
   uint ms = GetTickCount();
   if(!force && (ms - g_lastPanelMs) < 1000) return;
   g_lastPanelMs = ms;

   if(applyChartStyle) ApplyChartStyle();

   // Reporting uses the same filter for live and closed trades. Do not use
   // SelectOwnPosition here: that strict selector is for trade management.
   g_openPL = 0.0;
   int openCount = 0;
   ArrayInitialize(statOpenTrades, 0);
   ArrayInitialize(statOpenPL, 0.0);
   double openLots = 0.0, openPips = 0.0, openProfit = 0.0, openComm = 0.0, openSwap = 0.0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(!IsMatchingOrder() || OrderCloseTime() != 0) continue;
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

   for(int s = 1; s <= 9; s++)
     {
      n = IntegerToString(s);
      bool built = (s == 9);
      color rc = built ? UiInk() : HudDim2();
      HudSetText(HUD_PREFIX + "str_S" + n + "_0", "S" + n, built ? UiAmber() : HudDim2());
      HudSetText(HUD_PREFIX + "str_S" + n + "_1", built ? IntegerToString(statTrades[s]) : "-", rc);
      HudSetText(HUD_PREFIX + "str_S" + n + "_2", built ? DoubleToString(winRate, 1) : "-", rc);
      HudSetText(HUD_PREFIX + "str_S" + n + "_3", built ? ((statClosed[s] >= 0.0 ? "+" : "") + DoubleToString(statClosed[s], 2)) : "-", built ? ((statClosed[s] >= 0.0) ? UiGood() : UiBad()) : rc);
      HudSetText(HUD_PREFIX + "str_S" + n + "_4", built ? DoubleToString(strategyLots, 2) : "-", rc);
     }
   HudSetText(HUD_PREFIX + "str_T1", IntegerToString(statTrades[9]), UiAccent());
   HudSetText(HUD_PREFIX + "str_T2", DoubleToString(winRate, 1), UiAccent());
   HudSetText(HUD_PREFIX + "str_T3", (statClosed[9] >= 0.0 ? "+" : "") + DoubleToString(statClosed[9], 2), (statClosed[9] >= 0.0) ? UiGood() : UiBad());
   HudSetText(HUD_PREFIX + "str_T4", DoubleToString(strategyLots, 2), UiAccent());
   HudSetText(HUD_PREFIX + "str_eV", (statPerTrade[9] >= 0.0 ? "+" : "") + DoubleToString(statPerTrade[9], 2), (statPerTrade[9] >= 0.0) ? UiGood() : UiBad());
   int ah = (int)g_avgHoldSec;
   HudSetText(HUD_PREFIX + "str_hV", StringFormat("%dh %02dm", ah / 3600, (ah % 3600) / 60), UiInk());
   HudSetText(HUD_PREFIX + "str_kV", IntegerToString(g_streak) + " | " + IntegerToString(g_salvage) + " / " + IntegerToString(g_cuts), UiInk());

   for(int sx=1;sx<=9;sx++)
     {
      string sn=IntegerToString(sx);
      double strategyPL = statClosed[sx] + statOpenPL[sx];
      string sv=(sx==9)?(IntegerToString(statTrades[sx]+statOpenTrades[sx])+" / "+DoubleToString(winRate,1)+"% / "+(strategyPL>=0.0?"+":"")+DoubleToString(strategyPL,2)):"- / - / -";
      HudSetText(HUD_PREFIX+"str_S"+sn+"_3",sv,(sx==9)?((strategyPL>=0.0)?UiGood():UiBad()):UiInk());
      ObjectSetString(0,HUD_PREFIX+"str_S"+sn+"_3",OBJPROP_TOOLTIP,
         "Trades: closed + open | Win rate: closed only | P/L: realized + floating");
     }
   HudSetText(HUD_PREFIX+"str_T3",IntegerToString(nTrades+openCount)+" / "+DoubleToString(winRate,1)+"% / "+(totalPL>=0.0?"+":"")+DoubleToString(totalPL,2),(totalPL>=0.0)?UiGood():UiBad());
   ObjectSetString(0,HUD_PREFIX+"str_T3",OBJPROP_TOOLTIP,
      "Trades: closed + open | Win rate: closed only | P/L: realized + floating");

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
   HudSetText(HUD_PREFIX+"top_dd",DoubleToString(g_currentDD,1)+"% / "+DoubleToString(maxAllowedDrawdownPct,1)+"%",ddClr);
   DrawLiveDDGauge();
   HudSetText(HUD_PREFIX+"top_spread",IntegerToString(spreadPoints),UiInk());
   HudSetText(HUD_PREFIX+"top_pos",IntegerToString(openCount)+"/"+IntegerToString(activeMaxPositions),UiInk());
   HudSetText(HUD_PREFIX+"top_next",cd,UiInk());
   HudSetText(HUD_PREFIX+"top_status",statusText,clrWhite);
   color sbg=(statusColor==UiGood())?UiGood():((statusColor==UiBad())?UiBad():UiAmber());
   ObjectSetInteger(0,HUD_PREFIX+"top_status_bg",OBJPROP_BGCOLOR,sbg);
   ObjectSetInteger(0,HUD_PREFIX+"top_status_bg",OBJPROP_COLOR,sbg);

   if(showEquityCurve)
     {
      if(ms - g_lastEqLiveMs > 60000)
        {
         g_lastEqLiveMs = ms;
         EqPush(equity, TimeCurrent());
        }
      int kept = EqCount();
      int nUse = (kept < eqCurveSamples) ? kept : eqCurveSamples;
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
      if(kept == 0) { peak = equity; trough = equity; }
      double netRet = (firstV > 0.0) ? (lastV - firstV) / firstV * 100.0 : 0.0;
      HudSetText(HUD_PREFIX + "eq_n", IntegerToString(nUse) + " | TRACKED", UiDim());
      HudSetText(HUD_PREFIX + "eq_V0", DoubleToString(peak, 2), UiInk());
      HudSetText(HUD_PREFIX + "eq_V1", DoubleToString(trough, 2), UiInk());
      HudSetText(HUD_PREFIX + "eq_V2", DoubleToString(maxDD, 1) + "%", (maxDD > 0.0) ? UiBad() : UiGood());
      HudSetText(HUD_PREFIX + "eq_V3", (netRet >= 0.0 ? "+" : "") + DoubleToString(netRet, 1) + "%", (netRet >= 0.0) ? UiGood() : UiBad());
      EqDraw();
     }

   ChartRedraw(0);
  }
