// Shared Fractals entry engine; selecting management never selects a different entry strategy.
string g_symbol;
datetime g_lastBarTime=0;
string g_rebuildStatus="READY";

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
   if(!DeleteOppositePending)return true;
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
   double loss=ManagementMode==MANAGEMENT_POINTS?StopLossPoints*point:entry*stopLossPct/100.0;
   double gain=ManagementMode==MANAGEMENT_POINTS?TakeProfitPoints*point:entry*takeProfitPct/100.0;
   bool buy=type==OP_BUYSTOP;
   sl=RebuildPrice(buy?entry-loss:entry+loss,!buy);
   tp=RebuildPrice(buy?entry+gain:entry-gain,buy);
   double minimum=MarketInfo(g_symbol,MODE_STOPLEVEL)*point;
   return sl>0 && tp>0 && loss>0 && gain>0 && MathAbs(entry-sl)+point*1e-6>=minimum && MathAbs(entry-tp)+point*1e-6>=minimum;
  }
void PlacePending(int type,double entry)
  {
   // Recheck for EACH send; a buy placed earlier this tick consumes a pending slot.
   if(!RebuildDirectionAllowed(type) || CountMarketPositions()>=MaxMarketPositions ||
      CountPendingOrders()>=MaxPendingOrders || HasPendingType(type))return;
   RefreshRates();
   double point=MarketInfo(g_symbol,MODE_POINT),ask=MarketInfo(g_symbol,MODE_ASK),bid=MarketInfo(g_symbol,MODE_BID);
   if(point<=0 || ask<=0 || bid<=0)return;
   if(MaxSpreadPoints>0 && (ask-bid)/point>MaxSpreadPoints+1e-6)return;
   entry=RebuildPrice(entry,type==OP_BUYSTOP);
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
   string comment=tradeComment+(ManagementMode==MANAGEMENT_POINTS?" PTS":" PCT");
   ResetLastError();
   int ticket=OrderSend(g_symbol,type,lots,entry,SlippagePoints,sl,tp,comment,MagicNumber,0,
                        type==OP_BUYSTOP?clrDodgerBlue:clrTomato);
   if(ticket<0){g_rebuildStatus="ORDER REJECTED";Print("Rebuild OrderSend failed: ",GetLastError());}
   else {g_rebuildStatus="PENDING PLACED";Print("Rebuild pending #",ticket," SL=",sl," TP=",tp);}
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
   if(ManagementMode!=MANAGEMENT_POINTS && ManagementMode!=MANAGEMENT_PERCENT)return false;
   if(MagicNumber<=0 || MaxMarketPositions<0 || MaxPendingOrders<0 || FractalLookbackBars<2 ||
      EntryBufferPoints<0 || SlippagePoints<0 || MaxSpreadPoints<0)return false;
   if((!UseRiskPercent && FixedLots<=0) || (UseRiskPercent && (RiskPercent<=0 || RiskPercent>100)))return false;
   if(ManagementMode==MANAGEMENT_POINTS)
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
   if(applyChartStyle)ApplyChartStyle();
   TagDeleteAll();TrackEquityAndDD();RefreshStats();
   ObjectsDeleteAll(0,HUD_PREFIX);
   if(showDashboardPanel){HudLayout();HudCreate();HudLayout();}
   if(showEquityCurve)SeedEquityHistory();
   HudTick(true);UpdateStatus();EqDraw();PanelDraw(true);
   if(PanelEnabled())EventSetTimer(1);
   Print("Gold X9 Rebuild Raised v1.100 | ",ManagementMode==MANAGEMENT_POINTS?"POINTS":"PERCENT"," | ",g_symbol);
   return INIT_SUCCEEDED;
  }
void UpdateStatus()
  {
   HudTick(false);
   string mode=ManagementMode==MANAGEMENT_POINTS?"POINTS":"PERCENT";
   ObjectSetString(0,HUD_PREFIX+"top_pending",OBJPROP_TOOLTIP,"Owned pending limit: "+IntegerToString(MaxPendingOrders));
   HudSetText(HUD_PREFIX+"top_status",mode+" | "+g_rebuildStatus,g_rebuildStatus=="READY"?UiGood():UiAmber());
   if(ShowStatusComment)
      Comment("Gold X9 Rebuild Raised | ",mode,"\n",g_symbol," | ",g_rebuildStatus,
              "\nOpen ",CountMarketPositions(),"/",MaxMarketPositions," | Pending ",CountPendingOrders(),"/",MaxPendingOrders);
  }
void RebuildTick()
  {
   RefreshRates();activeStopLevel=SymbolStopsLevel();activeFreezeLevel=SymbolFreezeLevel();
   if(ManagementMode==MANAGEMENT_POINTS)ManageOpenTrades();
   else
     {
      datetime now=TimeCurrent();int interval=PeriodSeconds(exitTimeFrame);if(interval<1)interval=60;
      if(lastExitManageTime==0 || now-lastExitManageTime>=interval){lastExitManageTime=now;manageOpenPositions();}
     }
   // Management and OCO cleanup always run, even when the spread blocks new entries.
   if(DeleteOppositePending)DeleteOppositePendingOrders();
   TrackEquityAndDD();
   g_rebuildStatus="READY";
   double point=MarketInfo(g_symbol,MODE_POINT),ask=MarketInfo(g_symbol,MODE_ASK),bid=MarketInfo(g_symbol,MODE_BID);
   if(point<=0 || ask<=0 || bid<=0){g_rebuildStatus="WAITING FOR QUOTE";UpdateStatus();PanelDraw(false);return;}
   if(MaxSpreadPoints>0 && (ask-bid)/point>MaxSpreadPoints+1e-6)
     {g_rebuildStatus="SPREAD FILTER";UpdateStatus();PanelDraw(false);return;}
   if(CountMarketPositions()>=MaxMarketPositions || CountPendingOrders()>=MaxPendingOrders)
     {g_rebuildStatus="LIMIT REACHED";UpdateStatus();PanelDraw(false);return;}
   datetime bar=iTime(g_symbol,Period(),0);
   if(bar<=0){g_rebuildStatus="WAITING FOR HISTORY";UpdateStatus();PanelDraw(false);return;}
   if(OneEntryPerBar && bar==g_lastBarTime){UpdateStatus();PanelDraw(false);return;}
   double upper=FindFractal(MODE_UPPER),lower=FindFractal(MODE_LOWER);
   if(upper<=0 || lower<=0){g_rebuildStatus="WAITING FOR FRACTALS";UpdateStatus();PanelDraw(false);return;}
   if(OneEntryPerBar)g_lastBarTime=bar; // One evaluation per bar, not an account-wide fill guarantee.
   if(RebuildDirectionAllowed(OP_BUYSTOP))PlacePending(OP_BUYSTOP,upper+EntryBufferPoints*point);
   if(RebuildDirectionAllowed(OP_SELLSTOP))PlacePending(OP_SELLSTOP,lower-EntryBufferPoints*point);
   UpdateStatus();PanelDraw(false);
  }
