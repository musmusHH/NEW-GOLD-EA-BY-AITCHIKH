// Independent Fractals reconstruction: common entry and sizing inputs.
enum RebuildManagementMode
  {
   MANAGEMENT_POINTS=0,   // Original reconstruction: SL/TP/BE/trailing in broker points
   MANAGEMENT_PERCENT=1,  // Single-level entry + percentage management
   MANAGEMENT_MULTI_POINTS=2, // Multiple distinct Fractals + points management
   MANAGEMENT_MULTI_PERCENT=3 // Multiple distinct Fractals + percentage management
  };
input RebuildManagementMode ManagementMode=MANAGEMENT_MULTI_POINTS;
input string TradeSymbol="";              // Blank = chart/tester symbol
input int MagicNumber=630063;
input double FixedLots=0.01;
input bool UseRiskPercent=false;
input double RiskPercent=1.0;              // % of account balance; both modes
input int MaxMarketPositions=10;           // Owned open positions: new-entry limit
input int MaxPendingOrders=10;             // Owned pending orders: combined limit
input int MaxPendingPerSide=5;             // Separate BUY / SELL pending cap; no borrowing unused slots
input int PendingExpiryMinutes=60;         // 0 disables expiry; native expiry with local fallback
input int SlippagePoints=30;
input int MaxSpreadPoints=100;             // Broker points, not pips; 0 disables filter
input bool EnableBuy=true;
input bool EnableSell=true;
input int FractalLookbackBars=100;
input int EntryBufferPoints=30;
input bool DeleteOppositePending=false;    // Single-level modes only; MULTI always allows both sides
input bool OneEntryPerBar=true;
input bool TesterFastMode=true;           // Tester only: suspend dashboard rendering, not trading
input datetime TesterDashboardFrom=0;     // Server/test time to show UI again; 0 = hidden throughout
input bool ShowStatusComment=false;        // Optional native text; dashboard replaces it by default
input bool UseBreakEven=true;              // Applies in either management mode
input bool UseTrailingStop=true;           // Applies in either management mode

// POINTS mode only (defaults from the supplied reconstruction).
input int StopLossPoints=5000;
input int TakeProfitPoints=10000;
input int BreakEvenTriggerPoints=4000;
input int BreakEvenLockPoints=200;
input int TrailingStartPoints=1200;
input int TrailingDistancePoints=800;
input int TrailingStepPoints=200;

// PERCENT mode only (defaults from the previous MT4 EA).
input double stopLossPct=2.0;              // Initial SL: % of pending entry price
input double takeProfitPct=0.7;            // Initial TP: % of pending entry price
input double breakEvenTriggerPct=0.1;
input double breakEvenLockPct=0.025;
input double trailTriggerPct=0.2;
input double trailDistancePct=0.2;
input double maxTrailPct=1.0;
input double salvageTriggerPct=1.0;        // 0 disables salvage trigger
input double salvagePct=0.15;
input ENUM_TIMEFRAMES exitTimeFrame=PERIOD_M1; // PERCENT management interval
input bool enableAgedLossCut=true;
input double agedLossHours=4.0;
input double agedLossMinLossPct=0.05;
input bool enableMidTargetTrail=true;
input double midTargetPct=0.35;
input double trailDistanceWidePct=0.30;
input double trailDistanceAfterMidPct=0.15;
input bool enablePartialPay=false;

// Shared dashboard identity; strict magic reporting is the default below.
const string tradeComment="GoldX9_MT4_Rebuild";
// No old X9 entry offsets or risk gates: entry rules remain the supplied Fractals rules.
const double trailAdjustment=0.0,breakEvenAdjustment=0.0,salvageAdjustment=0.0;
const bool enableDDHalt=false,enableDeadWindow=false,enableEquityCurveHalt=false;
const double maxAllowedDrawdownPct=30.0,equityCurveHaltPct=10.0;
const int deadWindowFromHour=0,deadWindowToHour=5,equityHaltMode=0;
