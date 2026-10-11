"""Execute the independent MT4 reconstruction engine with terminal stubs.
Not native MQL compilation; the MT4 terminal still needs demo acceptance.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'gold_x9_Rebuild_Raised.mq4').read_text()
INPUTS=(ROOT/'rebuild/RebuildInputs.mqh').read_text()
ENGINE=(ROOT/'rebuild/RebuildEngine.mqh').read_text()

class RebuildRaisedTests(unittest.TestCase):
    def test_reproducible_modes_and_display_contract(self):
        subprocess.run(['python',str(ROOT/'tools/build_rebuild_mt4.py'),'--check'],check=True)
        self.assertNotIn('void runStrategyTick(',SOURCE)
        self.assertNotIn('bool placeEntry(',SOURCE)
        self.assertIn('iFractals(g_symbol,Period(),mode,shift)',SOURCE)
        self.assertIn('if(UseBreakEven && favorablePct >= beTrigger)',SOURCE)
        self.assertIn('if(UseTrailingStop && favorablePct >= trTrigger',SOURCE)
        self.assertIn('IntegerToString(pendingBuy+pendingSell)+"/"+IntegerToString(MaxPendingOrders)',SOURCE)
        self.assertIn('IntegerToString(openCount)+"/"+IntegerToString(activeMaxPositions)',SOURCE)
        self.assertIn('BORDER_RAISED',SOURCE)
        self.assertIn('expiration=(datetime)((long)TimeCurrent()+(long)PendingExpiryMinutes*60);',SOURCE)
        self.assertNotIn('datetime expiration=PendingExpiryMinutes>0?',SOURCE)
        self.assertIn('filterMatchMode = MATCH_MAGIC_ONLY',SOURCE)
        timer=SOURCE.split('void OnTimer()')[1].split('void OnChartEvent')[0]
        for name in ['OrderSend','OrderModify','OrderDelete','RebuildTick','manageOpenPositions']:
            self.assertNotIn(name,timer)

    def test_tester_gate_is_display_only(self):
        gate=ENGINE.split('void RebuildRefreshDisplay(')[1].split('void UpdateStatus()')[0]
        self.assertIn('if(RebuildSuppressTesterDisplay())return;',gate)
        for op in ('OrderSend(', 'OrderModify(', 'OrderDelete(', 'ManageOpenTrades(', 'manageOpenPositions('):
            self.assertNotIn(op,gate)
        tick=ENGINE.split('void RebuildTick()')[1]
        self.assertNotIn('if(RebuildSuppressTesterDisplay())return;',tick)
        self.assertIn('RebuildExpirePendingOrders()',tick)

    def test_table_sorts_only_nontrivial_arrays(self):
        for array in ('tickets','pendingTickets'):
            self.assertIn('if(ArraySize('+array+')>1) ArraySort('+array+');',SOURCE)
        self.assertEqual(len(re.findall(r'\bArraySort\(',SOURCE)),2)

    def test_reused_chart_and_four_theme_layout(self):
        import test_chart_panel
        import test_focus_design
        for module,cls,method in [(test_chart_panel,test_chart_panel.ChartPanelTests,'test_renderer_and_controls'),
                                  (test_focus_design,test_focus_design.FocusDesignTests,'test_layout_objects_and_four_theme_cycle')]:
            original=module.SOURCE
            try:
                module.SOURCE=SOURCE
                if module is test_chart_panel:getattr(cls(),method)(strict_sort=True)
                else:getattr(cls(),method)()
            finally:module.SOURCE=original

    def test_engine_entries_limits_oco_management_and_risk(self):
        stub=r'''
#include <string>
#include <vector>
#include <map>
#include <cmath>
#include <algorithm>
#include <cassert>
using namespace std;using datetime=long;using color=int;using ENUM_TIMEFRAMES=int;
const int PERIOD_M1=1,OP_BUY=0,OP_SELL=1,OP_BUYLIMIT=2,OP_SELLLIMIT=3,OP_BUYSTOP=4,OP_SELLSTOP=5;
enum {SELECT_BY_POS,SELECT_BY_TICKET,MODE_TRADES,MODE_POINT,MODE_ASK,MODE_BID,MODE_DIGITS,MODE_SPREAD,
 MODE_MINLOT,MODE_MAXLOT,MODE_LOTSTEP,MODE_TICKVALUE,MODE_STOPLEVEL,MODE_FREEZELEVEL,MODE_UPPER,MODE_LOWER,
 SYMBOL_TRADE_TICK_SIZE,clrDodgerBlue,clrTomato,clrGold,clrRed,clrAqua,OBJPROP_TOOLTIP,INIT_SUCCEEDED,INIT_FAILED,INIT_PARAMETERS_INCORRECT};
const double EMPTY_VALUE=2147483647;
string HUD_PREFIX="GX9H_";
string activeTradeSymbol,activeComment;int activeMagicNumber,activeSymbolDigits,activeMaxPositions,activeMaxPending,activeExitTimeFrame;
double activeSymbolPoint,activePipFactor,activeStopLevel,activeFreezeLevel,activeBreakEvenLockPct;
int g_pcBars,g_pcOffset,g_activeTheme,g_dayKey;bool g_pcFitOrders,g_ddHalted,g_equityHalted,g_probationWeek;
double g_peakEquityLab,g_lotMultiplier;datetime lastExitManageTime=0;
int selTicket,selType,selMagic;double selPrice;string selSymbol;
string g_partialKeys[200];int chartStartBars=64,chartStartOffset=0,hudTheme=0;
bool chartStartFitOrders=false,applyChartStyle=false,showDashboardPanel=true,showEquityCurve=true;
struct Order {int ticket,type,magic;string symbol;double entry,sl,tp,lots;datetime opened=100,expires=0;};vector<Order> orders;
int selected=0,nextTicket=100,sendCalls=0,modifyCalls=0,trailCalls=0,percentCalls=0,deleted=0;
bool testing=false,symbolOK=true,sendOK=true,modifyOK=true,marginOK=true,deleteOK=true,denyExpiration=false;
datetime lastExpiration=0;
double bid=2000,ask=2000.20,point=.01,tick=.01,lotStep=.01,minLot=.01,maxLot=100,balance=10000;
bool useLevels=false;map<int,double> upperLevels,lowerLevels;
int uiCalls=0;unsigned int uiClock=1000;bool visual=true;
int availableBars=200;datetime now=1000,barTime=900;double upper=2010,lower=1990;int lastError=0;
int OrdersTotal(){return orders.size();}
bool OrderSelect(int v,int mode,int){if(mode==SELECT_BY_TICKET){for(int i=0;i<int(orders.size());i++)if(orders[i].ticket==v){selected=i;return true;}return false;}if(v<0||v>=int(orders.size()))return false;selected=v;return true;}
int OrderType(){return orders[selected].type;}int OrderTicket(){return orders[selected].ticket;}int OrderMagicNumber(){return orders[selected].magic;}
string OrderSymbol(){return orders[selected].symbol;}int OrderCloseTime(){return 0;}
datetime OrderOpenTime(){return orders[selected].opened;}datetime OrderExpiration(){return orders[selected].expires;}
double OrderProfit(){return 0;}double OrderSwap(){return 0;}double OrderCommission(){return 0;}
double OrderLots(){return orders[selected].lots;}
double OrderOpenPrice(){return orders[selected].entry;}double OrderStopLoss(){return orders[selected].sl;}double OrderTakeProfit(){return orders[selected].tp;}
int OrderSend(string symbol,int type,double lots,double price,int,double sl,double tp,string,int magic,datetime expiry,int){sendCalls++;lastExpiration=expiry;if(denyExpiration&&expiry>0){lastError=147;return -1;}if(!sendOK){lastError=128;return -1;}int t=nextTicket++;orders.push_back({t,type,magic,symbol,price,sl,tp,lots,now,expiry});return t;}
bool OrderModify(int ticket,double,double sl,double tp,int,int){modifyCalls++;if(!modifyOK)return false;for(auto &o:orders)if(o.ticket==ticket){o.sl=sl;o.tp=tp;return true;}return false;}
bool OrderClose(int ticket,double lots,double,int,int){for(auto &o:orders)if(o.ticket==ticket){o.lots-=lots;return true;}return false;}
bool OrderDelete(int ticket){if(!deleteOK)return false;for(int i=0;i<int(orders.size());i++)if(orders[i].ticket==ticket){orders.erase(orders.begin()+i);deleted++;return true;}return false;}
double MarketInfo(string,int key){switch(key){case MODE_POINT:return point;case MODE_ASK:return ask;case MODE_BID:return bid;
 case MODE_DIGITS:return 2;case MODE_MINLOT:return minLot;case MODE_MAXLOT:return maxLot;case MODE_LOTSTEP:return lotStep;
 case MODE_TICKVALUE:return 1;case MODE_STOPLEVEL:return 50;case MODE_FREEZELEVEL:return 30;}return 0;}
double SymbolInfoDouble(string,int){return tick;}
double AccountBalance(){return balance;}
double AccountFreeMarginCheck(string,int,double){return marginOK?1000:-1;}
string ErrorDescription(int){return "error";}
void Sleep(int){}string DoubleToString(double v,int){return to_string(v);}
void RefreshRates(){}void ResetLastError(){lastError=0;}int GetLastError(){return lastError;}
template<class... T>void Print(T... args){}template<class... T>void Comment(T... args){}
template<class A,class B>double MathMax(A a,B b){return max(double(a),double(b));}
template<class A,class B>double MathMin(A a,B b){return min(double(a),double(b));}
double MathAbs(double v){return abs(v);}double MathFloor(double v){return floor(v);}double MathCeil(double v){return ceil(v);}
double NormalizeDouble(double v,int n){double k=pow(10,n);return round(v*k)/k;}
int StringLen(string s){return s.size();}string IntegerToString(int v){return to_string(v);}
int Period(){return 5;}int PeriodSeconds(int){return 60;}datetime TimeCurrent(){return now;}
datetime iTime(string,int,int){return barTime;}int iBars(string,int){return availableBars;}
double iFractals(string,int,int mode,int shift){if(useLevels)return mode==MODE_UPPER?upperLevels[shift]:lowerLevels[shift];return shift==2?(mode==MODE_UPPER?upper:lower):0;}
string Symbol(){return "XAUUSD";}unsigned int GetTickCount(){return uiClock;}bool IsVisualMode(){return visual;}bool IsTesting(){return testing;}bool SymbolSelect(string,bool){return symbolOK;}
double SymbolAsk(){return ask;}double SymbolBid(){return bid;}
double SymbolPoint(){return point;}int SymbolDigits(){return 2;}double SymbolStopsLevel(){return point*50;}double SymbolFreezeLevel(){return point*30;}
void PanelRememberTrail(int,double){trailCalls++;}void manageOpenPositions();
void ApplyChartStyle(){}void TagDeleteAll(){}void TrackEquityAndDD(){}void RefreshStats(){}
void ObjectsDeleteAll(int,string){}void HudLayout(){}void HudCreate(){}void SeedEquityHistory(){}
void EqDraw(){}void PanelDraw(bool){uiCalls++;}bool PanelEnabled(){return true;}void EventSetTimer(int){}
void HudTick(bool){uiCalls++;}void ObjectSetString(int,string,int,string){}void HudSetText(string,string,int){}
int UiGood(){return 1;}int UiAmber(){return 2;}void UpdateStatus();
bool RebuildSuppressTesterDisplay();void RebuildRefreshDisplay(bool force=false);
'''
        main=r'''
void reset(){orders.clear();sendCalls=modifyCalls=trailCalls=percentCalls=deleted=0;sendOK=modifyOK=marginOK=true;
 g_symbol="XAUUSD";g_lastBarTime=0;lastExitManageTime=0;ManagementMode=MANAGEMENT_POINTS;UseRiskPercent=false;
 PendingExpiryMinutes=60;MaxPendingPerSide=5;denyExpiration=false;deleteOK=true;lastExpiration=0;
 testing=false;visual=true;TesterFastMode=true;TesterDashboardFrom=0;uiCalls=0;uiClock=1000;g_rebuildDisplayStarted=false;g_rebuildDisplayMs=0;
 MaxMarketPositions=10;MaxPendingOrders=10;DeleteOppositePending=true;OneEntryPerBar=true;EnableBuy=EnableSell=true;
 UseBreakEven=UseTrailingStop=true;enablePartialPay=false;enableAgedLossCut=true;for(auto &k:g_partialKeys)k="";bid=2000;ask=2000.20;point=tick=.01;lotStep=minLot=.01;maxLot=100;
 useLevels=false;upperLevels.clear();lowerLevels.clear();
 availableBars=200;upper=2010;lower=1990;barTime=900;now=1000;
}
int main(){
 reset();assert(RebuildParametersValid());assert(RebuildInit()==INIT_SUCCEEDED);
 assert(activeMaxPositions==10&&activeMaxPending==10&&activeMagicNumber==630063);
 double sl,tp;
 assert(RebuildStops(OP_BUYSTOP,2000,sl,tp));assert(sl==1950&&tp==2100);
 assert(RebuildStops(OP_SELLSTOP,2000,sl,tp));assert(sl==2050&&tp==1900);
 ManagementMode=MANAGEMENT_PERCENT;assert(RebuildStops(OP_BUYSTOP,2000,sl,tp));assert(sl==1960&&tp==2014);
 assert(RebuildStops(OP_SELLSTOP,2000,sl,tp));assert(sl==2040&&tp==1986);
 UseRiskPercent=true;assert(abs(CalculateLots(2000,1950)-.02)<1e-9);
 assert(CalculateLots(2000,1000)==0); // below minimum: don't increase risk
 lotStep=minLot=.001;assert(RebuildLotDigits(lotStep)==3);assert(CalculateLots(2000,1950)==.02);
 reset();MaxPendingOrders=1;RebuildTick();assert(orders.size()==1&&orders[0].type==OP_BUYSTOP&&sendCalls==1);
 orders.clear();RebuildTick();assert(sendCalls==1); // same bar cannot evaluate again
 barTime+=300;RebuildTick();assert(sendCalls==2);
 reset();MaxPendingOrders=0;RebuildTick();assert(sendCalls==0);
 reset();MaxMarketPositions=0;RebuildTick();assert(sendCalls==0);
 reset();orders={{1,OP_BUY,MagicNumber,"XAUUSD",1900,1850,2100,.01},
                 {2,OP_SELLSTOP,MagicNumber,"XAUUSD",1990,2050,1900,.01},
                 {3,OP_SELLSTOP,999,"XAUUSD",1990,2050,1900,.01}};
 RebuildTick();assert(deleted==1&&!RebuildDirectionAllowed(OP_SELLSTOP));
 for(auto o:orders)assert(!(o.magic==MagicNumber&&o.type==OP_SELLSTOP));
 assert(orders[1].magic==999); // unrelated pending order left intact
 assert(trailCalls==1&&orders[0].sl==1992);
 reset();orders={{1,OP_BUY,MagicNumber,"XAUUSD",2000,1950,2100,.01},
                 {2,OP_SELL,MagicNumber,"XAUUSD",2000,2050,1900,.01},
                 {3,OP_BUYSTOP,MagicNumber,"XAUUSD",2010,1950,2100,.01},
                 {4,OP_SELLSTOP,MagicNumber,"XAUUSD",1990,2050,1900,.01}};
 RebuildTick();assert(orders.size()==2&&sendCalls==0&&deleted==2); // mixed directions block both new sides
 reset();orders={{1,OP_BUY,MagicNumber,"XAUUSD",1900,1850,2100,.01}};
 ask=2002;RebuildTick();assert(modifyCalls==1&&trailCalls==1&&sendCalls==0); // manage before spread filter
 reset();orders={{1,OP_BUY,MagicNumber,"XAUUSD",1900,1850,2100,.01}};modifyOK=false;
 RebuildTick();assert(modifyCalls==1&&trailCalls==0&&orders[0].sl==1850);
 reset();ManagementMode=MANAGEMENT_PERCENT;RebuildTick();assert(percentCalls==1&&modifyCalls==0);
 now++;RebuildTick();assert(percentCalls==1);now+=60;RebuildTick();assert(percentCalls==2);
 reset();UseBreakEven=false;UseTrailingStop=false;orders={{1,OP_BUY,MagicNumber,"XAUUSD",1900,1850,2100,.01}};
 ManageOpenTrades();assert(modifyCalls==0);
 reset();marginOK=false;PlacePending(OP_BUYSTOP,2010);assert(sendCalls==0);
 reset();availableBars=3;RebuildTick();assert(sendCalls==0&&g_lastBarTime==0);
 availableBars=200;RebuildTick();assert(sendCalls==2);
 // Actual legacy percentage manager: percent trailing differs from points thresholds.
 reset();ManagementMode=MANAGEMENT_PERCENT;
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",1990,1950,2050,.01}};RebuildTick();
 assert(percentCalls==1&&modifyCalls==1&&trailCalls==1&&orders[0].sl==1997);
 reset();orders={{1,OP_BUY,MagicNumber,"XAUUSD",1990,1950,2050,.01}};ManageOpenTrades();assert(modifyCalls==0);
 reset();ManagementMode=MANAGEMENT_PERCENT;orders={{1,OP_BUY,MagicNumber,"XAUUSD",1990,1950,2050,.01}};
 modifyOK=false;RebuildTick();assert(modifyCalls==1&&trailCalls==0&&orders[0].sl==1950);
 reset();ManagementMode=MANAGEMENT_PERCENT;UseBreakEven=UseTrailingStop=false;
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",1990,1950,2050,.01}};RebuildTick();assert(modifyCalls==0);
 reset();ManagementMode=MANAGEMENT_PERCENT;enablePartialPay=true;
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",1990,1950,2050,.02}};RebuildTick();assert(orders[0].lots==.01);
 now+=60;RebuildTick();assert(orders[0].lots==.01);
 // Multi-level entry populates 10 unique orders, both sides, and ignores stale OCO=true.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;useLevels=true;DeleteOppositePending=true;
 for(int i=2;i<12;i++){upperLevels[i]=2010+i;lowerLevels[i]=1990-i;}
 RebuildTick();assert(sendCalls==10&&CountPendingOrders()==10&&deleted==0);
 int buys=0,sells=0;for(auto a:orders){buys+=a.type==OP_BUYSTOP;sells+=a.type==OP_SELLSTOP;
   assert(abs(abs(a.entry-a.sl)-50)<1e-6);for(auto b:orders)if(a.ticket!=b.ticket)assert(abs(a.entry-b.entry)>.005);}
 assert(buys==5&&sells==5);barTime+=300;RebuildTick();assert(sendCalls==10);
 // Repeated prices, including distinct raw levels rounding to one tick, are deduplicated.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;useLevels=true;
 upperLevels[2]=2010.001;upperLevels[3]=2010.003;upperLevels[4]=2010.001;
 lowerLevels[2]=1990;lowerLevels[3]=1990;RebuildTick();assert(sendCalls==2);
 barTime+=300;RebuildTick();assert(sendCalls==2);
 // Existing owned market entries occupy levels, while both directions remain allowed.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;useLevels=true;
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",2010.30,1900,2100,.01}};
 upperLevels[2]=2010;upperLevels[3]=2011;lowerLevels[2]=1990;
 RebuildTick();assert(sendCalls==2&&HasPendingType(OP_SELLSTOP)&&deleted==0);
 assert(RebuildDirectionAllowed(OP_BUYSTOP)&&RebuildDirectionAllowed(OP_SELLSTOP));
 // Multi percent uses the same level scanner but percentage initial stops and manager.
 reset();ManagementMode=MANAGEMENT_MULTI_PERCENT;useLevels=true;MaxPendingOrders=3;
 for(int i=2;i<6;i++){upperLevels[i]=2010+i;lowerLevels[i]=1990-i;}
 RebuildTick();assert(sendCalls==3&&percentCalls==1&&CountPendingOrders()==3);
 for(auto a:orders)assert(abs(abs(a.entry-a.sl)-a.entry*.02)<.011);
 // A single enabled side does not require an opposite fractal in multi mode.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;useLevels=true;EnableSell=false;
 for(int i=2;i<12;i++)upperLevels[i]=2010+i;
 RebuildTick();assert(sendCalls==5);for(auto a:orders)assert(a.type==OP_BUYSTOP);
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;MaxPendingOrders=1;RebuildTick();assert(sendCalls==1);
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;MaxMarketPositions=1;
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",2010,1900,2100,.01}};RebuildTick();assert(sendCalls==0);
 reset();ManagementMode=MANAGEMENT_MULTI_PERCENT;StopLossPoints=0;assert(RebuildParametersValid());
 StopLossPoints=5000;ManagementMode=(RebuildManagementMode)99;assert(!RebuildParametersValid());
 // One-sided levels cannot consume the other side's quota, but both sides may fill their own slots.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;useLevels=true;MaxPendingPerSide=2;
 for(int i=2;i<15;i++)lowerLevels[i]=1990-i;
 RebuildTick();assert(sendCalls==2&&CountPendingSide(false)==2&&CountPendingSide(true)==0);
 for(int i=2;i<15;i++)upperLevels[i]=2010+i;barTime+=300;RebuildTick();
 assert(sendCalls==4&&CountPendingSide(true)==2&&CountPendingSide(false)==2);
 // Existing LIMIT orders consume side capacity; other magics do not.
 reset();ManagementMode=MANAGEMENT_MULTI_POINTS;MaxPendingPerSide=1;
 orders={{1,OP_BUYLIMIT,MagicNumber,"XAUUSD",1950,1900,2100,.01}};
 PlacePending(OP_BUYSTOP,2010);assert(sendCalls==0);PlacePending(OP_SELLSTOP,1990);assert(sendCalls==1);
 reset();PlacePending(OP_BUYSTOP,2010);assert(lastExpiration==now+3600&&orders[0].expires==now+3600);
 now+=3600;ask=2002;RebuildTick();assert(deleted==1&&orders.empty()&&sendCalls==1); // expiry before spread, no same-cycle refill
 reset();denyExpiration=true;PlacePending(OP_BUYSTOP,2010);
 assert(sendCalls==2&&orders.size()==1&&orders[0].expires==0); // explicit 147 -> GTC fallback only
 now+=3600;assert(RebuildExpirePendingOrders()&&orders.empty());
 reset();sendOK=false;PlacePending(OP_BUYSTOP,2010);assert(sendCalls==1); // timeout is NOT retried as expiry fallback
 reset();PendingExpiryMinutes=0;PlacePending(OP_BUYSTOP,2010);assert(lastExpiration==0);
 now+=100000;assert(!RebuildExpirePendingOrders()&&orders.size()==1);
 reset();now=5000;
 orders={{1,OP_BUYSTOP,MagicNumber,"XAUUSD",2010,1900,2100,.01,100,0},
         {2,OP_SELLSTOP,999,"XAUUSD",1990,2100,1900,.01,100,0},
         {3,OP_BUY,MagicNumber,"XAUUSD",1900,1800,2100,.01,100,0},
         {4,OP_BUYLIMIT,MagicNumber,"OTHER",1950,1900,2100,.01,100,0}};
 deleteOK=false;assert(!RebuildExpirePendingOrders()&&orders.size()==4);
 deleteOK=true;assert(RebuildExpirePendingOrders()&&orders.size()==3&&deleted==1);
 reset();PendingExpiryMinutes=-1;assert(!RebuildParametersValid());PendingExpiryMinutes=60;
 MaxPendingPerSide=-1;assert(!RebuildParametersValid());MaxPendingPerSide=5;
 // Fast tester rendering must not suppress trading, stop management or expiry.
 reset();testing=true;TesterFastMode=true;assert(RebuildInit()==INIT_SUCCEEDED&&uiCalls==0);
 orders={{1,OP_BUY,MagicNumber,"XAUUSD",1900,1850,2100,.01}};
 RebuildTick();assert(modifyCalls==1&&sendCalls==1&&uiCalls==0);
 now+=3600;RebuildTick();assert(deleted==1&&uiCalls==0);
 TesterDashboardFrom=now+100;RebuildRefreshDisplay();assert(uiCalls==0);
 now+=100;RebuildRefreshDisplay();assert(uiCalls>0&&g_rebuildDisplayStarted);
 int previousUI=uiCalls;RebuildRefreshDisplay();assert(uiCalls==previousUI);
 uiClock+=250;RebuildRefreshDisplay();assert(uiCalls>previousUI);
 reset();testing=true;TesterFastMode=false;RebuildRefreshDisplay();assert(uiCalls>0);
 reset();testing=true;visual=false;TesterFastMode=false;RebuildRefreshDisplay();assert(uiCalls==0);
 reset();TesterFastMode=true;RebuildRefreshDisplay();assert(uiCalls>0); // live/demo UI unaffected
 reset();TradeSymbol="OTHER";testing=true;assert(RebuildInit()==INIT_FAILED);testing=false;TradeSymbol="";
 ManagementMode=MANAGEMENT_PERCENT;StopLossPoints=0;assert(RebuildParametersValid()); // inactive points settings ignored
 ManagementMode=MANAGEMENT_POINTS;assert(!RebuildParametersValid());StopLossPoints=5000;
}
'''
        def function(name):
            m=re.search(r'^(?:void|bool) '+name+r'\([^\n]*\)\s*\{',SOURCE,re.M)
            i=m.end();depth=1
            while depth:
                depth+=(SOURCE[i]=='{')-(SOURCE[i]=='}');i+=1
            return SOURCE[m.start():i]
        manager='\n'.join(function(n) for n in ['SelectOwnPosition','FixStops','PartialKeyExists','PartialKeyAdd','manageOpenPositions'])
        manager=manager.replace('void manageOpenPositions()\n  {','void manageOpenPositions()\n  {\n   percentCalls++;')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/'engine.cpp').write_text(stub+INPUTS.replace('input ','')+ENGINE.replace('void RebuildRefreshDisplay(bool force=false)', 'void RebuildRefreshDisplay(bool force)')+manager+main)
            subprocess.run(['g++','-std=c++17',str(path/'engine.cpp'),'-o',str(path/'engine')],check=True)
            subprocess.run([str(path/'engine')],check=True)

if __name__=='__main__':unittest.main()
