// Fractals entry: single-level or multi-level, each with points/percentage management.
string g_symbol;
datetime g_lastBarTime=0;
string g_rebuildStatus="READY";
bool g_rebuildDisplayStarted=false;
uint g_rebuildDisplayMs=0;

bool RebuildMultiMode()
  {
   return ManagementMode==MANAGEMENT_MULTI_POINTS || ManagementMode==MANAGEMENT_MULTI_PERCENT;
  }
bool RebuildPointsMode()
  {
   return ManagementMode==MANAGEMENT_POINTS || ManagementMode==MANAGEMENT_MULTI_POINTS;
  }
bool RebuildOCOEnabled()
  {
   return DeleteOppositePending && !RebuildMultiMode();
  }
string RebuildModeLabel()
  {
   if(RebuildMultiMode())return RebuildPointsMode()?"MULTI POINTS":"MULTI PERCENT";
   return RebuildPointsMode()?"SINGLE POINTS":"SINGLE PERCENT";
  }

bool RebuildOwnOrder()
  {
   return OrderSymbol()==g_symbol && OrderMagicNumber()==MagicNumber && OrderCloseTime()==0;
  }
int CountMarketPositions()
  {
   int count=0;
   for(int i=OrdersTotal()-1;i>=0;i--)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && RebuildOwnOrder() &&
         (OrderType()==OP_BUY || OrderType()==OP_SELL)) count++;
   return count;
  }
int CountPendingOrders()
  {
   int count=0;
   for(int i=OrdersTotal()-1;i>=0;i--)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && RebuildOwnOrder() &&
         OrderType()>=OP_BUYLIMIT && OrderType()<=OP_SELLSTOP)count++;
   return count;
  }
int CountPendingSide(bool buy)
  {
   int count=0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || !RebuildOwnOrder())continue;
      int type=OrderType();
      if((buy && (type==OP_BUYSTOP || type==OP_BUYLIMIT)) ||
         (!buy && (type==OP_SELLSTOP || type==OP_SELLLIMIT)))count++;
     }
   return count;
  }

bool RebuildExpirePendingOrders()
  {
   if(PendingExpiryMinutes<=0)return false;
   bool removed=false;
   datetime now=TimeCurrent();
   long lifetime=(long)PendingExpiryMinutes*60;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || !RebuildOwnOrder())continue;
      if(OrderType()<OP_BUYLIMIT || OrderType()>OP_SELLSTOP)continue;
      // Also expire pre-existing GTC orders by age under the current setting.
      datetime opened=OrderOpenTime(),expires=OrderExpiration();
      bool due=(opened>0 && now-opened>=lifetime) || (expires>0 && now>=expires);
      if(!due)continue;
      int ticket=OrderTicket();ResetLastError();
      if(OrderDelete(ticket)) {removed=true;Print("Rebuild pending expired #",ticket);}
      else Print("Rebuild expiry delete failed #",ticket," error=",GetLastError());
     }
   return removed;
  }

bool HasPendingType(int type)
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && RebuildOwnOrder() && OrderType()==type)return true;
   return false;
  }
bool RebuildHasMarketSide(int type)
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && RebuildOwnOrder() && OrderType()==type)return true;
   return false;
  }
bool RebuildDirectionAllowed(int type)
  {
   if(type!=OP_BUYSTOP && type!=OP_SELLSTOP)return false;
   if(type==OP_BUYSTOP && !EnableBuy)return false;
   if(type==OP_SELLSTOP && !EnableSell)return false;
   if(!RebuildOCOEnabled())return true;
   return !RebuildHasMarketSide(type==OP_BUYSTOP?OP_SELL:OP_BUY);
  }
void DeleteOppositePendingOrders()
  {
   // Check BOTH sides, not an arbitrary first market position.
   bool buy=RebuildHasMarketSide(OP_BUY),sell=RebuildHasMarketSide(OP_SELL);
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || !RebuildOwnOrder())continue;
      bool opposite=(buy && (OrderType()==OP_SELLSTOP || OrderType()==OP_SELLLIMIT)) ||
                    (sell && (OrderType()==OP_BUYSTOP || OrderType()==OP_BUYLIMIT));
      if(!opposite)continue;
      int ticket=OrderTicket();ResetLastError();
      if(!OrderDelete(ticket))Print("Rebuild OCO delete failed #",ticket," error=",GetLastError());
     }
  }
double FindFractal(int mode)
  {
   int available=iBars(g_symbol,Period());
   int last=(int)MathMin(FractalLookbackBars,available-3);
   for(int shift=2;shift<=last;shift++)
     {
      double value=iFractals(g_symbol,Period(),mode,shift);
      if(value>0 && value!=EMPTY_VALUE)return value;
     }
   return 0;
  }
double RebuildTickSize()
  {
   double tick=SymbolInfoDouble(g_symbol,SYMBOL_TRADE_TICK_SIZE);
   return tick>0?tick:MarketInfo(g_symbol,MODE_POINT);
  }
double RebuildPrice(double price,bool roundUp)
  {
   double tick=RebuildTickSize();if(tick<=0)return 0;
   double units=price/tick;
   double result=(roundUp?MathCeil(units-1e-8):MathFloor(units+1e-8))*tick;
   return NormalizeDouble(result,(int)MarketInfo(g_symbol,MODE_DIGITS));
  }
int RebuildLotDigits(double step)
  {
   for(int n=0;n<=8;n++)if(MathAbs(step-NormalizeDouble(step,n))<1e-9)return n;
   return 8;
  }
double CalculateLots(double entry,double stop)
  {
   double lots=FixedLots;
   if(UseRiskPercent)
     {
      double tick=RebuildTickSize(),value=MarketInfo(g_symbol,MODE_TICKVALUE);
      double distance=MathAbs(entry-stop);
      if(tick<=0 || value<=0 || distance<=0)return 0;
      lots=(AccountBalance()*RiskPercent/100.0)/(distance/tick*value);
     }
   double minimum=MarketInfo(g_symbol,MODE_MINLOT),maximum=MarketInfo(g_symbol,MODE_MAXLOT);
   double step=MarketInfo(g_symbol,MODE_LOTSTEP);
   if(minimum<=0 || maximum<minimum || step<=0)return 0;
   lots=MathFloor(MathMin(lots,maximum)/step+1e-9)*step;
   // Do not exceed the requested risk just to satisfy the broker's minimum lot.
   if(lots<minimum-1e-9){if(UseRiskPercent)return 0;lots=minimum;}
   return NormalizeDouble(lots,RebuildLotDigits(step));
  }
bool RebuildStops(int type,double entry,double &sl,double &tp)
  {
   double point=MarketInfo(g_symbol,MODE_POINT);
   if(entry<=0 || point<=0)return false;
   double loss=RebuildPointsMode()?StopLossPoints*point:entry*stopLossPct/100.0;
   double gain=RebuildPointsMode()?TakeProfitPoints*point:entry*takeProfitPct/100.0;
   bool buy=type==OP_BUYSTOP;
   sl=RebuildPrice(buy?entry-loss:entry+loss,!buy);
   tp=RebuildPrice(buy?entry+gain:entry-gain,buy);
   double minimum=MarketInfo(g_symbol,MODE_STOPLEVEL)*point;
   return sl>0 && tp>0 && loss>0 && gain>0 && MathAbs(entry-sl)+point*1e-6>=minimum && MathAbs(entry-tp)+point*1e-6>=minimum;
  }
// Compare broker-normalized entry levels against ALL owned live orders/positions.
// History is intentionally excluded: a closed/canceled level may be used again.
bool RebuildHasEntryPrice(double entry)
  {
   double tolerance=RebuildTickSize()*0.5+1e-9;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || !RebuildOwnOrder())continue;
      if(OrderType()<OP_BUY || OrderType()>OP_SELLSTOP)continue;
      if(MathAbs(OrderOpenPrice()-entry)<=tolerance)return true;
     }
   return false;
  }

void PlacePending(int type,double entry)
  {
   // Recheck for EACH send; a buy placed earlier this tick consumes a pending slot.
   if(!RebuildDirectionAllowed(type) || CountMarketPositions()>=MaxMarketPositions ||
      CountPendingOrders()>=MaxPendingOrders || (!RebuildMultiMode() && HasPendingType(type)))return;
   if(CountPendingSide(type==OP_BUYSTOP)>=MaxPendingPerSide)return;
   RefreshRates();
   double point=MarketInfo(g_symbol,MODE_POINT),ask=MarketInfo(g_symbol,MODE_ASK),bid=MarketInfo(g_symbol,MODE_BID);
   if(point<=0 || ask<=0 || bid<=0)return;
   if(MaxSpreadPoints>0 && (ask-bid)/point>MaxSpreadPoints+1e-6)return;
   entry=RebuildPrice(entry,type==OP_BUYSTOP);
   if(RebuildMultiMode() && RebuildHasEntryPrice(entry))return;
   double minimum=MarketInfo(g_symbol,MODE_STOPLEVEL)*point;
   if(type==OP_BUYSTOP && entry<=ask+minimum)return;
   if(type==OP_SELLSTOP && entry>=bid-minimum)return;
   double sl=0,tp=0;
   if(!RebuildStops(type,entry,sl,tp)){g_rebuildStatus="SL/TP BELOW BROKER MINIMUM";return;}
   double lots=CalculateLots(entry,sl);
   if(lots<=0){g_rebuildStatus="LOT/RISK BELOW BROKER MINIMUM";return;}
   ResetLastError();
   int side=type==OP_BUYSTOP?OP_BUY:OP_SELL;
   double free=AccountFreeMarginCheck(g_symbol,side,lots);
   if(free<=0 || GetLastError()==134){g_rebuildStatus="INSUFFICIENT MARGIN";return;}
   string comment=tradeComment+(RebuildPointsMode()?" PTS":" PCT");
   ResetLastError();
   datetime expiration=0;
   if(PendingExpiryMinutes>0)
      expiration=(datetime)((long)TimeCurrent()+(long)PendingExpiryMinutes*60);
   int ticket=OrderSend(g_symbol,type,lots,entry,SlippagePoints,sl,tp,comment,MagicNumber,expiration,
                        type==OP_BUYSTOP?clrDodgerBlue:clrTomato);
   // Error 147 is an explicit expiry rejection, not an uncertain execution result.
   if(ticket<0 && expiration>0 && GetLastError()==147)
     {
      // Recheck quotas/identity before the fallback send as well.
      if(!RebuildDirectionAllowed(type) || CountMarketPositions()>=MaxMarketPositions ||
         CountPendingOrders()>=MaxPendingOrders || CountPendingSide(type==OP_BUYSTOP)>=MaxPendingPerSide ||
         (RebuildMultiMode()?RebuildHasEntryPrice(entry):HasPendingType(type)))return;
      ResetLastError();
      ticket=OrderSend(g_symbol,type,lots,entry,SlippagePoints,sl,tp,comment,MagicNumber,0,
                       type==OP_BUYSTOP?clrDodgerBlue:clrTomato);
     }
   if(ticket<0){g_rebuildStatus="ORDER REJECTED";Print("Rebuild OrderSend failed: ",GetLastError());}
   else {g_rebuildStatus="PENDING PLACED";Print("Rebuild pending #",ticket," SL=",sl," TP=",tp);}
  }
void RebuildScanMultipleLevels()
  {
   int last=(int)MathMin(FractalLookbackBars,iBars(g_symbol,Period())-3);
   double point=MarketInfo(g_symbol,MODE_POINT);
   bool found=false;
   // Newest to oldest; try both sides at each shift instead of filling all slots with buys first.
   for(int shift=2;shift<=last;shift++)
     {
      if(CountPendingOrders()>=MaxPendingOrders || CountMarketPositions()>=MaxMarketPositions)break;
      double upper=iFractals(g_symbol,Period(),MODE_UPPER,shift);
      double lower=iFractals(g_symbol,Period(),MODE_LOWER,shift);
      if(upper>0 && upper!=EMPTY_VALUE && RebuildDirectionAllowed(OP_BUYSTOP))
        {found=true;PlacePending(OP_BUYSTOP,upper+EntryBufferPoints*point);}
      if(lower>0 && lower!=EMPTY_VALUE && RebuildDirectionAllowed(OP_SELLSTOP))
        {found=true;PlacePending(OP_SELLSTOP,lower-EntryBufferPoints*point);}
     }
   if(!found)g_rebuildStatus="WAITING FOR FRACTALS";
   else if(CountPendingOrders()>=MaxPendingOrders || CountMarketPositions()>=MaxMarketPositions)
      g_rebuildStatus="LIMIT REACHED";
   if(OneEntryPerBar && found)g_lastBarTime=iTime(g_symbol,Period(),0);
  }

void ManageOpenTrades()
  {
   double point=MarketInfo(g_symbol,MODE_POINT);
   double bid=MarketInfo(g_symbol,MODE_BID),ask=MarketInfo(g_symbol,MODE_ASK);
   if(point<=0 || bid<=0 || ask<=0)return;
   double minimum=MathMax(MarketInfo(g_symbol,MODE_STOPLEVEL),MarketInfo(g_symbol,MODE_FREEZELEVEL))*point;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || !RebuildOwnOrder())continue;
      int type=OrderType();if(type!=OP_BUY && type!=OP_SELL)continue;
      bool buy=type==OP_BUY;
      double oldSL=OrderStopLoss(),newSL=oldSL;
      double profit=(buy?bid-OrderOpenPrice():OrderOpenPrice()-ask)/point;
      bool changed=false,trailed=false;
      if(UseBreakEven && profit>=BreakEvenTriggerPoints)
        {
         double be=OrderOpenPrice()+(buy?1:-1)*BreakEvenLockPoints*point;
         if((buy && (newSL==0 || be>newSL+point)) || (!buy && (newSL==0 || be<newSL-point)))
           {newSL=be;changed=true;}
        }
      if(UseTrailingStop && profit>=TrailingStartPoints)
        {
         double trail=buy?bid-TrailingDistancePoints*point:ask+TrailingDistancePoints*point;
         if((buy && trail>newSL+TrailingStepPoints*point) || (!buy && (newSL==0 || trail<newSL-TrailingStepPoints*point)))
           {newSL=trail;changed=true;trailed=true;}
        }
      if(!changed)continue;
      newSL=RebuildPrice(newSL,!buy);
      if((buy && (newSL<=0 || bid-newSL<=minimum || (oldSL>0 && newSL<=oldSL))) ||
         (!buy && (newSL-ask<=minimum || (oldSL>0 && newSL>=oldSL))))continue;
      int ticket=OrderTicket();ResetLastError();
      if(OrderModify(ticket,OrderOpenPrice(),newSL,OrderTakeProfit(),0,clrGold))
        {if(trailed)PanelRememberTrail(ticket,newSL);}
      else Print("Rebuild modify failed #",ticket," error=",GetLastError());
     }
  }
bool RebuildParametersValid()
  {
   if(ManagementMode!=MANAGEMENT_POINTS && ManagementMode!=MANAGEMENT_PERCENT &&
      ManagementMode!=MANAGEMENT_MULTI_POINTS && ManagementMode!=MANAGEMENT_MULTI_PERCENT)return false;
   if(MagicNumber<=0 || MaxMarketPositions<0 || MaxPendingOrders<0 || MaxPendingPerSide<0 ||
      PendingExpiryMinutes<0 || PendingExpiryMinutes>5256000 || FractalLookbackBars<2 ||
      EntryBufferPoints<0 || SlippagePoints<0 || MaxSpreadPoints<0)return false;
   if((!UseRiskPercent && FixedLots<=0) || (UseRiskPercent && (RiskPercent<=0 || RiskPercent>100)))return false;
   if(RebuildPointsMode())
      return StopLossPoints>0 && TakeProfitPoints>0 &&
         (!UseBreakEven || (BreakEvenTriggerPoints>=0 && BreakEvenLockPoints>=0 && BreakEvenLockPoints<BreakEvenTriggerPoints)) &&
         (!UseTrailingStop || (TrailingStartPoints>=0 && TrailingDistancePoints>0 && TrailingStepPoints>=0));
   return stopLossPct>0 && stopLossPct<100 && takeProfitPct>0 && takeProfitPct<100 &&
      (!UseBreakEven || (breakEvenTriggerPct>0 && breakEvenLockPct>=0 && breakEvenLockPct<breakEvenTriggerPct)) &&
      (!UseTrailingStop || (trailTriggerPct>=0 && trailDistancePct>0 && maxTrailPct>=trailTriggerPct &&
        (!enableMidTargetTrail || (midTargetPct>0 && trailDistanceWidePct>0 && trailDistanceAfterMidPct>0)))) &&
      salvageTriggerPct>=0 && salvagePct>=0 && (!enableAgedLossCut || (agedLossHours>0 && agedLossMinLossPct>=0)) &&
      (!enablePartialPay || midTargetPct>0);
  }
int RebuildInit()
  {
   if(!RebuildParametersValid()){Print("Rebuild: invalid inputs for selected management mode.");return INIT_PARAMETERS_INCORRECT;}
   g_symbol=StringLen(TradeSymbol)==0?Symbol():TradeSymbol;
   if(g_symbol!=Symbol())
     {
      if(IsTesting()){Print("Rebuild: set TradeSymbol blank in tester.");return INIT_FAILED;}
      if(!SymbolSelect(g_symbol,true))return INIT_FAILED;
     }
   activeTradeSymbol=g_symbol;activeMagicNumber=MagicNumber;activeComment=tradeComment;
   activeSymbolPoint=SymbolPoint();activeSymbolDigits=SymbolDigits();activePipFactor=activeSymbolPoint;
   if(activeSymbolPoint<=0 || activeSymbolDigits<0)return INIT_FAILED;
   if(activeSymbolDigits==3 || activeSymbolDigits==5)activePipFactor*=10;
   activeMaxPositions=MaxMarketPositions;activeMaxPending=MaxPendingOrders;
   activeStopLevel=SymbolStopsLevel();activeFreezeLevel=SymbolFreezeLevel();
   activeBreakEvenLockPct=breakEvenLockPct;activeExitTimeFrame=exitTimeFrame;
   g_pcBars=(int)MathMax(16,MathMin(240,chartStartBars));
   g_pcOffset=(int)MathMax(0,chartStartOffset);g_pcFitOrders=chartStartFitOrders;
   g_activeTheme=(int)hudTheme;if(g_activeTheme<0 || g_activeTheme>3)g_activeTheme=0;
   g_lastBarTime=0;lastExitManageTime=0;g_dayKey=0;g_ddHalted=false;
   g_peakEquityLab=0;g_equityHalted=false;g_probationWeek=false;g_lotMultiplier=1;
   for(int i=0;i<200;i++)g_partialKeys[i]="";
   g_rebuildDisplayStarted=false;g_rebuildDisplayMs=0;
   TagDeleteAll();TrackEquityAndDD();
   RebuildRefreshDisplay(true);
   if(RebuildSuppressTesterDisplay())
      Print("Rebuild tester fast display mode: trading still runs on every tick. Dashboard resume time=",TesterDashboardFrom);
   Print("Gold X9 Rebuild Raised v1.123 | ",RebuildModeLabel()," | ",g_symbol);
   return INIT_SUCCEEDED;
  }
bool RebuildSuppressTesterDisplay()
  {
   if(!IsTesting())return false;
   if(!IsVisualMode())return true;
   return TesterFastMode && (TesterDashboardFrom==0 || TimeCurrent()<TesterDashboardFrom);
  }
void RebuildRefreshDisplay(bool force=false)
  {
   if(RebuildSuppressTesterDisplay())return;
   uint now=GetTickCount();
   if(!force && g_rebuildDisplayStarted && now-g_rebuildDisplayMs<250)return;
   g_rebuildDisplayMs=now;
   if(!g_rebuildDisplayStarted)
     {
      if(applyChartStyle)ApplyChartStyle();
      ObjectsDeleteAll(0,HUD_PREFIX);
      if(showDashboardPanel){HudLayout();HudCreate();HudLayout();}
      HudTick(true);
      g_rebuildDisplayStarted=true;
      if(PanelEnabled())EventSetTimer(1);
      force=true;
     }
   UpdateStatus();PanelDraw(force);
  }

void UpdateStatus()
  {
   HudTick(false);
   string mode=RebuildModeLabel();
   ObjectSetString(0,HUD_PREFIX+"top_pending",OBJPROP_TOOLTIP,"BUY "+IntegerToString(CountPendingSide(true))+"/"+IntegerToString(MaxPendingPerSide)+
      " | SELL "+IntegerToString(CountPendingSide(false))+"/"+IntegerToString(MaxPendingPerSide)+
      " | TOTAL LIMIT "+IntegerToString(MaxPendingOrders)+" | EXPIRY "+IntegerToString(PendingExpiryMinutes)+" min (0=off)");
   HudSetText(HUD_PREFIX+"top_status",mode+" | "+g_rebuildStatus,g_rebuildStatus=="READY"?UiGood():UiAmber());
   if(ShowStatusComment)
      Comment("Gold X9 Rebuild Raised | ",mode,"\n",g_symbol," | ",g_rebuildStatus,
              "\nOpen ",CountMarketPositions(),"/",MaxMarketPositions," | Pending ",CountPendingOrders(),"/",MaxPendingOrders);
  }
void RebuildTick()
  {
   RefreshRates();activeStopLevel=SymbolStopsLevel();activeFreezeLevel=SymbolFreezeLevel();
   if(RebuildPointsMode())ManageOpenTrades();
   else
     {
      datetime now=TimeCurrent();int interval=PeriodSeconds(exitTimeFrame);if(interval<1)interval=60;
      if(lastExitManageTime==0 || now-lastExitManageTime>=interval){lastExitManageTime=now;manageOpenPositions();}
     }
   // Management, expiry and OCO cleanup run even when spread blocks new entries.
   bool expired=RebuildExpirePendingOrders();
   if(RebuildOCOEnabled())DeleteOppositePendingOrders();
   TrackEquityAndDD();
   g_rebuildStatus="READY";
   if(expired)
     {
      // Do not immediately replace locally expired orders in this same evaluation.
      if(OneEntryPerBar)g_lastBarTime=iTime(g_symbol,Period(),0);
      g_rebuildStatus="PENDING EXPIRED";RebuildRefreshDisplay();return;
     }
   double point=MarketInfo(g_symbol,MODE_POINT),ask=MarketInfo(g_symbol,MODE_ASK),bid=MarketInfo(g_symbol,MODE_BID);
   if(point<=0 || ask<=0 || bid<=0){g_rebuildStatus="WAITING FOR QUOTE";RebuildRefreshDisplay();return;}
   if(MaxSpreadPoints>0 && (ask-bid)/point>MaxSpreadPoints+1e-6)
     {g_rebuildStatus="SPREAD FILTER";RebuildRefreshDisplay();return;}
   if(CountMarketPositions()>=MaxMarketPositions || CountPendingOrders()>=MaxPendingOrders)
     {g_rebuildStatus="LIMIT REACHED";RebuildRefreshDisplay();return;}
   datetime bar=iTime(g_symbol,Period(),0);
   if(bar<=0){g_rebuildStatus="WAITING FOR HISTORY";RebuildRefreshDisplay();return;}
   if(OneEntryPerBar && bar==g_lastBarTime){RebuildRefreshDisplay();return;}
   if(RebuildMultiMode())
     {RebuildScanMultipleLevels();RebuildRefreshDisplay();return;}
   double upper=FindFractal(MODE_UPPER),lower=FindFractal(MODE_LOWER);
   if(upper<=0 || lower<=0){g_rebuildStatus="WAITING FOR FRACTALS";RebuildRefreshDisplay();return;}
   if(OneEntryPerBar)g_lastBarTime=bar; // One evaluation per bar, not an account-wide fill guarantee.
   if(RebuildDirectionAllowed(OP_BUYSTOP))PlacePending(OP_BUYSTOP,upper+EntryBufferPoints*point);
   if(RebuildDirectionAllowed(OP_SELLSTOP))PlacePending(OP_SELLSTOP,lower-EntryBufferPoints*point);
   RebuildRefreshDisplay();
  }
