"""Execute the actual chart renderer against a bounded, recording C++ canvas.
MT4 APIs are mocked; MetaEditor compilation and demo checks remain necessary.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'gold_x9_FIXED.mq4').read_text()

class ChartPanelTests(unittest.TestCase):
    def test_renderer_and_controls(self):
        panel = SOURCE.split('//=== Broker-data chart panel')[1].split('double SymbolAsk()')[0]
        panel = '//=== Broker-data chart panel' + panel
        panel = re.sub(r"C'(\d+),(\d+),(\d+)'", r'RGB(\1,\2,\3)', panel)
        panel = panel.replace('PanelLevel &levels[]', 'vector<PanelLevel> &levels')
        panel = panel.replace('PanelLevel levels[];', 'vector<PanelLevel> levels;')
        panel = panel.replace('MqlRates rates[];', 'vector<MqlRates> rates;')
        # MQL string literals support concatenation directly; C++ needs std::string.
        panel = panel.replace('#define PC_BUTTON "GX9PC_btn_"', 'const string PC_BUTTON="GX9PC_btn_";')
        panel = panel.replace('text+=" "+', 'text+=string(" ")+')
        panel = panel.replace('int tickets[];', 'vector<int> tickets;')
        panel = panel.replace('int pendingTickets[];', 'vector<int> pendingTickets;')
        panel = panel.replace('string g_pcHiddenObjects[];', 'vector<string> g_pcHiddenObjects;')
        panel = panel.replace('long g_pcHiddenMasks[];', 'vector<long> g_pcHiddenMasks;')
        panel = panel.replace('PanelTrailState g_panelTrails[];', 'vector<PanelTrailState> g_panelTrails;')
        palette = SOURCE[SOURCE.index('// Design 4: exactly four palettes'):SOURCE.index('color HudDim2()')]
        palette = re.sub(r"C'(\d+),(\d+),(\d+)'", r'RGB(\1,\2,\3)', palette)
        geometry = SOURCE[SOURCE.index('void FocusGeometry(int width,int height)\n  {'):SOURCE.index('void HudLayout()\n  {')]
        stub = r'''
#include <string>
#include <vector>
#include <map>
#include <cmath>
#include <cassert>
#include <algorithm>
#include <sstream>
using namespace std;
using uint=unsigned int; using datetime=long long; using color=unsigned int;
using ENUM_TIMEFRAMES=int; using ENUM_CHART_PROPERTY_INTEGER=int;
const int CHART_COLOR_BACKGROUND=20,CHART_COLOR_FOREGROUND=21,CHART_COLOR_CHART_UP=22,
CHART_COLOR_CHART_DOWN=23,CHART_COLOR_CANDLE_BULL=24,CHART_COLOR_CANDLE_BEAR=25,
CHART_COLOR_CHART_LINE=26,CHART_COLOR_BID=27,CHART_COLOR_ASK=28,CHART_COLOR_STOP_LEVEL=29,
CHART_COLOR_VOLUME=30,CHART_COLOR_GRID=31,CHART_SHOW_PRICE_SCALE=32,CHART_SHOW_DATE_SCALE=33,CHART_SHOW_OHLC=34;
bool hideOriginalChart=true;
double chartRightSpacePct=20;
const int CHART_EVENT_MOUSE_MOVE=40,CHART_MOUSE_SCROLL=41;
double PanelBarSpacing(int count);
void PanelDraw(bool force);
int chartTradeRows=8;
const int HUD_GRAPHITE=0,HUD_LIGHT=1,HUD_MIDNIGHT=2,HUD_EMERALD=3;
int g_activeTheme=0;
#define RGB(r,g,b) ((r<<16)|(g<<8)|b)
const color clrSilver=0xaaaaaa,clrWhite=0xffffff;
const int OP_BUY=0,OP_SELL=1,OP_BUYLIMIT=2,OP_SELLLIMIT=3,OP_BUYSTOP=4,OP_SELLSTOP=5;
const int CHART_SHOW_TRADE_LEVELS=1,CHART_FOREGROUND=2,CHART_WIDTH_IN_PIXELS=3,CHART_HEIGHT_IN_PIXELS=4;
const int OBJ_BUTTON=0,CORNER_LEFT_UPPER=0,OBJPROP_CORNER=0,OBJPROP_XDISTANCE=1,OBJPROP_YDISTANCE=2;
const int OBJPROP_XSIZE=3,OBJPROP_YSIZE=4,OBJPROP_BGCOLOR=5,OBJPROP_COLOR=6,OBJPROP_BORDER_COLOR=7;
const int OBJPROP_FONTSIZE=8,OBJPROP_HIDDEN=9,OBJPROP_SELECTABLE=10,OBJPROP_ZORDER=11,OBJPROP_STATE=12;
const int OBJPROP_TEXT=13,OBJPROP_BACK=14,OBJPROP_TOOLTIP=15,COLOR_FORMAT_ARGB_NORMALIZE=0;
const int SELECT_BY_TICKET=1,SELECT_BY_POS=0,MODE_TRADES=0,TIME_DATE=1,TIME_MINUTES=2,TIME_SECONDS=4;
const string TAG_PREFIX="GX9T_",HUD_PREFIX="GX9H_";
const int OBJPROP_TIMEFRAMES=50,OBJ_NO_PERIODS=0;
const int TAG_MAX=512;
int g_tagN=0; datetime g_tagTime[TAG_MAX]; double g_tagPrice[TAG_MAX],g_tagProfit[TAG_MAX]; color g_tagClr[TAG_MAX];
bool showDashboardPanel=true,showLiveChartPanel=true,drawResultTags=true,quoteOK=true;
string activeTradeSymbol="XAUUSD"; int activeSymbolDigits=2;
double activeSymbolPoint=0.01,g_totalClosedPL=290.75; int g_px[6]={},g_pw[6]={},g_py[6]={},g_ph[6]={};
const int HUD_NP=6;
int g_chartW=0,g_chartH=0,g_focusRows=4,g_focusDockH=124,g_focusTableW=800;
bool g_focusReady=false,showEquityCurve=true;
void FocusGeometry(int width,int height);
void EqCanvasDestroy(){}void EqDraw(){}
map<int,long> chart={{1,1},{2,1},{3,1366},{4,700}};
map<string,string> objects;
map<string,long> masks;
map<string,map<int,long>> props;
uint clockMs=1000; datetime latest=100000;
int barsAvailable=500,relayouts=0;
uint GetTickCount(){return clockMs;}
bool IsTesting(){return false;} bool IsVisualMode(){return false;}
long ChartGetInteger(int,int p){return chart[p];}
void ChartSetInteger(int,int p,long v){chart[p]=v;}
void ChartRedraw(int){}
void HudLayout(){FocusGeometry(chart[CHART_WIDTH_IN_PIXELS],chart[CHART_HEIGHT_IN_PIXELS]);}
int ObjectFind(int,string n){return objects.count(n)?0:-1;}
bool ObjectCreate(int,string n,int,int,int,int){objects[n]="";return true;}
void ObjectSetInteger(int,string name,int prop,long value){props[name][prop]=value;if(prop==OBJPROP_TIMEFRAMES)masks[name]=value;}
long ObjectGetInteger(int,string name,int){return masks[name];}
int ObjectsTotal(int,int,int){return objects.size();}
string ObjectName(int,int index,int,int){auto it=objects.begin();advance(it,index);return it->first;}
void ObjectSetString(int,string n,int,string s){objects[n]=s;}
void ObjectsDeleteAll(int,string prefix){for(auto i=objects.begin();i!=objects.end();) if(i->first.find(prefix)==0)i=objects.erase(i);else ++i;}
int GetLastError(){return 0;} void Print(string,int){}
void TagRelayout(){relayouts++;}
uint ColorToARGB(color c,int a=255){return c | (uint(a)<<24);}
template<class A,class B> double MathMin(A a,B b){return min(double(a),double(b));}
template<class A,class B> double MathMax(A a,B b){return max(double(a),double(b));}
double MathRound(double v){return round(v);} double MathAbs(double v){return abs(v);}
int StringLen(string s){return s.size();} string StringSubstr(string s,int i,int n=999999){return s.substr(i,n);}
int StringFind(string s,string n){auto p=s.find(n);return p==string::npos?-1:int(p);}
string IntegerToString(int n){return to_string(n);}
string DoubleToString(double d,int n){ostringstream s;s.setf(ios::fixed);s.precision(n);s<<d;return s.str();}
string TimeToString(datetime t,int){return to_string(t);}
datetime TimeCurrent(){return latest;}
int Period(){return 5;}
template<class T> int ArraySize(vector<T>& v){return v.size();}
template<class T> int ArrayResize(vector<T>& v,int n){v.resize(n);return n;}
template<class T> void ArraySort(vector<T>& v){sort(v.begin(),v.end());}
template<class T,size_t N> void ArrayInitialize(T (&a)[N],T value){for(auto &v:a)v=value;}
template<class T> void ArraySetAsSeries(vector<T>&,bool){}
struct MqlRates {datetime time;double open,high,low,close;};
struct MqlTick {datetime time;double bid,ask;};
datetime iTime(string,int,int shift){return latest-shift*300;}
int iBars(string,int){return barsAvailable;}
int iBarShift(string,int,datetime time,bool){return int((latest-time)/300);}
int CopyRates(string,int,int offset,int n,vector<MqlRates>& r){n=min(n,max(0,barsAvailable-offset));r.resize(n);for(int i=0;i<n;i++)r[i]={latest-(offset+i)*300,4180,4185,4178,4183};return n;}
bool SymbolInfoTick(string,MqlTick &t){t={latest,4184,4184.8};return quoteOK;}
struct Order {int type;string symbol;int magic;double entry,sl,tp,profit;int ticket=0;};
vector<Order> orders;Order selected;
int OrdersTotal(){return orders.size();}
bool OrderSelect(int i,int mode,int){if(mode==SELECT_BY_TICKET){for(auto o:orders)if((o.ticket?o.ticket:12345678+o.type)==i){selected=o;return true;}return false;}selected=orders[i];return true;}
string OrderSymbol(){return selected.symbol;}
string accountCurrency="USD";
string AccountCurrency(){return accountCurrency;}
const int SYMBOL_TRADE_TICK_SIZE=1,SYMBOL_TRADE_TICK_VALUE=2;
double mockTickSize=0.01,mockTickValue=1;
double SymbolInfoDouble(string,int prop){return prop==1?mockTickSize:mockTickValue;}
int OrderCloseTime(){return 0;}
bool IsMatchingOrderIdentity(){return selected.symbol==activeTradeSymbol && selected.magic==123457;}
int OrderType(){return selected.type;}int OrderTicket(){return selected.ticket?selected.ticket:12345678+selected.type;}
double OrderProfit(){return selected.profit;}double OrderSwap(){return -0.1;}
double OrderLots(){return 0.01;}double CommissionCost(double lots){return lots*7;}
double OrderOpenPrice(){return selected.entry;}double OrderStopLoss(){return selected.sl;}double OrderTakeProfit(){return selected.tp;}
struct CCanvas {
 int w=0,h=0,updates=0;bool fail=false;vector<string> text;
 bool CreateBitmapLabel(int,int,string n,int,int,int W,int H,int){w=W;h=H;objects[n]="";return !fail;}
 void Destroy(){objects.erase("GX9PC_chart");}
 void FontSet(string,int){}
 void point(int x,int y){assert(x>=0&&x<w&&y>=0&&y<h);}
 void TextOut(int x,int y,string s,uint){point(x,y);text.push_back(s);}
 int TextWidth(string s){return s.size()*6;}
 void Line(int x,int y,int X,int Y,uint){point(x,y);point(X,Y);}
 void FillRectangle(int x,int y,int X,int Y,uint){point(x,y);point(X,Y);assert(X>=x&&Y>=y);}
 void Erase(uint){text.clear();}void Update(){updates++;}
};
'''
        main = r'''
bool contains(string s){for(auto t:g_pc.text)if(t.find(s)!=string::npos)return true;return false;}
int main(){
 objects["old_result_box"]="";masks["old_result_box"]=63;
 objects["manual_line"]="";masks["manual_line"]=7;
 objects[HUD_PREFIX+"title"]="";masks[HUD_PREFIX+"title"]=511;
 assert(!g_pcFitOrders); // BARS is now the default.
 g_pcFitOrders=true; // Exercise ALL scaling below as before.
 chart[CHART_MOUSE_SCROLL]=1;chart[CHART_EVENT_MOUSE_MOVE]=0;
 chart[CHART_SHOW_PRICE_SCALE]=1;chart[CHART_COLOR_CHART_UP]=123;
 orders={{OP_BUY,"XAUUSD",123457,4180,4160,4200,1.5},
         {OP_SELLSTOP,"XAUUSD",123457,4155,4190,4140,0},
         {OP_BUYSTOP,"EURUSD",123457,1.1,0,0,0}};
 selected=orders[0];
 assert(PanelLiveMoney()=="+1.33");
 assert(PanelExitMoney(4200)=="+19.83");
 assert(PanelExitMoney(4160)=="-20.17");
 assert(PanelExitMoney(0)=="Not set");
 // Non-point-sized ticks must use the broker's tick size, not pip assumptions.
 mockTickSize=0.25;mockTickValue=2;assert(PanelExitMoney(4200)=="+1.43");
 mockTickSize=0.01;mockTickValue=1;
 selected.type=OP_SELL;assert(PanelExitMoney(4160)=="+19.83");
 assert(PanelExitMoney(4200)=="-20.17");
 selected.type=OP_BUYSTOP;assert(PanelLiveMoney()=="Pending");
 selected.type=OP_SELLSTOP;assert(PanelExitMoney(4160)=="+19.83");
 mockTickValue=0;assert(PanelExitMoney(4200)=="N/A");mockTickValue=1;
 mockTickSize=0;assert(PanelExitMoney(4200)=="N/A");mockTickSize=0.01;
 selected=orders[0];assert(PanelTrailMoney()=="-");
 PanelRememberTrail(OrderTicket(),4160);assert(PanelTrailMoney()=="ON -20.17");
 orders[0].sl=4182;selected=orders[0];assert(PanelTrailMoney()=="-");
 PanelRememberTrail(OrderTicket(),4182);assert(PanelTrailMoney()=="ON +1.83");
 PanelDraw(true);assert(contains("TRAIL $"));assert(contains("ON +1.83"));
 selected=orders[1];PanelRememberTrail(OrderTicket(),4190);assert(PanelTrailMoney()=="-");
 selected=orders[0];selected.type=OP_SELL;selected.sl=4178;
 PanelRememberTrail(OrderTicket(),4178);assert(PanelTrailMoney()=="ON +1.83");
 selected.sl=0;assert(PanelTrailMoney()=="-");
 mockTickValue=0;selected=orders[0];assert(PanelTrailMoney()=="ON N/A");mockTickValue=1;
 orders[0].sl=4160;PanelDraw(true);assert(!contains("ON +1.83"));
 assert(contains("LIVE $"));assert(contains("TP~ $"));assert(contains("SL~ $"));
 assert(contains("+19.83"));assert(contains("-20.17"));assert(contains("Pending"));assert(contains("PAGE 1/1"));
 accountCurrency="EUR";PanelDraw(true);assert(contains("LIVE EUR"));accountCurrency="USD";
 assert(g_pcReady);assert(chart[1]==0 && chart[2]==0);
 assert(masks["old_result_box"]==0&&masks["manual_line"]==0);
 assert(masks[HUD_PREFIX+"title"]==511);
 objects["new_line"]="";masks["new_line"]=15;clockMs+=600;PanelDraw(true);
 assert(masks["new_line"]==0);
 assert(chart[CHART_SHOW_PRICE_SCALE]==0);
 assert(chart[CHART_COLOR_CHART_UP]==UiPanel());
 // Full-width chart, separate trade/equity cards aligned directly above tracker.
 assert(g_pcX==8 && g_pcW==chart[3]-16);
 assert(g_pcBottom-g_pcTop>=100);
 assert(g_focusTableW+12+g_pw[4]==g_pcW);
 assert(g_py[4]+g_ph[4]==g_py[5]-16);
 assert(g_pcLow<4140 && g_pcHigh>4200);
 assert(objects[PC_NAME].find("LIVE |")!=string::npos);assert(contains("BUY"));
 assert(objects[PC_NAME].find("SELL STOP")!=string::npos);
 assert(objects[PC_NAME].find("@1.10")==string::npos);
 assert(PanelPriceY(g_pcHigh)==g_pcTop);assert(PanelPriceY(g_pcLow)==g_pcBottom);
 assert(PanelPriceY(g_pcHigh+100)==g_pcTop);
 assert(PanelBarX(0,64)>PanelBarX(63,64));
 assert(PanelBarX(0,g_pcRenderedBars)<g_pcRight-(g_pcRight-20)*0.18);
 assert(g_pcTop==10); // No toolbar or symbol consuming plot space.
 for(auto key:{"in","out","older","newer","live","range","move","center","vplus","vminus"}){
   auto p=props[PC_BUTTON+key];
   assert(p[OBJPROP_YDISTANCE]<g_pcY);
   assert(p[OBJPROP_YDISTANCE]+p[OBJPROP_YSIZE]<=g_py[2]+36);
 }
 int barsBefore=g_pcBars;
 double spanBefore=g_pcHigh-g_pcLow;
 PanelClick(PC_BUTTON+"vplus");assert(g_pcHigh-g_pcLow<spanBefore);assert(g_pcBars==barsBefore);
 PanelClick(PC_BUTTON+"vminus");assert(abs((g_pcHigh-g_pcLow)-spanBefore)<1e-6);
 PanelClick(PC_BUTTON+"center");
 assert(abs(PanelBarX(0,g_pcRenderedBars)-(12+(g_pcRight-20)*0.5))<=1);
 assert(abs(PanelPriceY(g_pcLastVisiblePrice)-(g_pcTop+g_pcBottom)*0.5)<=1);
 PanelClick(PC_BUTTON+"move");assert(g_pcMoveMode);assert(chart[CHART_MOUSE_SCROLL]==0);
 int mx=g_pcX+g_pcRight/2,my=g_pcY+(g_pcTop+g_pcBottom)/2;
 assert(!PanelMouseMove(g_pcX+15,g_pcY+g_pcBottom+40,1)); // table cannot start a chart drag
 assert(PanelMouseMove(mx,my,1));double oldPan=g_pcPanX,oldCenter=g_pcViewCenter;
 clockMs+=50;PanelMouseMove(mx+50,my+25,1);
 assert(g_pcPanX>oldPan && g_pcViewCenter>oldCenter);
 PanelMouseMove(mx+50,my+25,0);assert(!g_pcDragging);
 int pageBefore=g_pcTradePage;
 PanelTableClick(g_pcX+20,g_pcY+g_pcBottom+30);assert(g_pcTradePage==pageBefore);
 // Large drags/zoom clip candles and tags to plot, never to the price gutter.
 g_tagN=2;g_tagTime[0]=latest;g_tagTime[1]=latest-3000;
 g_tagPrice[0]=4184;g_tagPrice[1]=4180;g_tagProfit[0]=1;g_tagProfit[1]=-1;
 for(int dir:{-1,1}){
   PanelMouseMove(mx,my,1);clockMs+=50;PanelMouseMove(mx+dir*5000,my+dir*5000,1);
   PanelMouseMove(mx,my,0);PanelDraw(true);
 }
 for(int i=0;i<25;i++)PanelClick(PC_BUTTON+"vplus");
 assert(g_pcViewSpan>0 && g_pcViewSpan>=(g_pcAutoHigh-g_pcAutoLow)*0.149);
 for(int i=0;i<35;i++)PanelClick(PC_BUTTON+"vminus");
 assert(g_pcViewSpan<=(g_pcAutoHigh-g_pcAutoLow)*8.001);
 g_tagN=0;
 PanelClick(PC_BUTTON+"live");assert(!g_pcManualY && g_pcPanX==0);
 PanelClick(PC_BUTTON+"move");assert(!g_pcMoveMode && chart[CHART_MOUSE_SCROLL]==1);
 clockMs+=500;
 PanelClick(PC_BUTTON+"range"); assert(g_pcLow>4170);
 PanelClick(PC_BUTTON+"older");assert(g_pcOffset==32);assert(objects[PC_NAME].find("HISTORY |")!=string::npos);
 latest+=300;PanelDraw(true);assert(g_pcOffset==33);
 PanelClick(PC_BUTTON+"live");assert(g_pcOffset==0);
 for(int i=0;i<20;i++)PanelClick(PC_BUTTON+"in");assert(g_pcBars==16);
 for(int i=0;i<20;i++)PanelClick(PC_BUTTON+"out");assert(g_pcBars==240);
 clockMs+=61001;PanelDraw(true);assert(objects[PC_NAME].find("STALE")!=string::npos);
 quoteOK=false;PanelDraw(true);assert(objects[PC_NAME].find("No quote")!=string::npos);quoteOK=true;
 barsAvailable=0;PanelDraw(true);assert(contains("Waiting for broker"));barsAvailable=500;
 // Older pending tickets must never displace the four active trades.
 auto savedOrders=orders;
 orders.clear();
 for(int i=0;i<13;i++)orders.push_back({OP_SELLSTOP,"XAUUSD",123457,4155,4190,4140,0,100+i});
 for(int i=0;i<4;i++)orders.push_back({i?OP_SELL:OP_BUY,"XAUUSD",123457,4180,4160,4200,1.5,1000+i});
 g_pcTradePage=0;PanelDraw(true);
 assert(contains("OPEN 4 | PENDING 13"));assert(contains("PAGE 1/3"));
 for(int i=0;i<4;i++)assert(contains(to_string(1000+i)));
 assert(contains("Pending"));
 // Check actual rendered row ordering, not just presence in a tooltip.
 vector<string> shownTickets;
 for(auto text:g_pc.text)
    if(text=="1000"||text=="1001"||text=="1002"||text=="1003"||text=="100"||text=="101"||text=="102"||text=="103") shownTickets.push_back(text);
 assert((shownTickets==vector<string>{"1000","1001","1002","1003","100","101","102","103"}));
 clockMs+=300;PanelTableClick(g_pcX+20,g_pcY+g_pcBottom+30);
 assert(contains("PAGE 2/3"));assert(contains("Pending"));
 PanelClick(PC_BUTTON+"live");assert(g_pcTradePage==0);assert(contains("PAGE 1/3"));
 // Pending-only and empty accounts must still have a usable first page.
 orders.resize(13);g_pcTradePage=0;PanelDraw(true);
 assert(contains("OPEN 0 | PENDING 13"));assert(contains("PAGE 1/2"));assert(contains("Pending"));
 orders.clear();g_pcTradePage=0;PanelDraw(true);assert(contains("No matching trades"));assert(g_panelTrails.empty());
 orders=savedOrders;clockMs+=300;
 chartTradeRows=4;HudLayout(); // Keep the existing smaller-row pagination checks.
 // Dense levels must paginate without exceeding the canvas bounds.
 for(int i=0;i<20;i++)orders.push_back(orders[0]);
 PanelDraw(true);
 assert(!contains("LIVE |"));assert(!contains("#12345678"));
 assert(objects.count(PC_BUTTON+"trades")==0);assert(objects.count(PC_BUTTON+"page")==0);
 assert(!PanelTableClick(g_pcX+20,g_pcY+60));
 assert(PanelTableClick(g_pcX+20,g_pcY+g_pcBottom+30));assert(g_pcTradePage==1);
 PanelTableClick(g_pcX+20,g_pcY+g_pcBottom+30);assert(g_pcTradePage==1);
 clockMs+=300;
 assert(PanelTableClick(g_pcX+20,g_pcY+g_pcH-15));assert(g_pcTradePage==2);
 assert(!PanelTableClick(g_pcX+20,g_pcY+g_pcH-2));
 // Exercise pixel bounds across normal/resized windows and zoom settings.
 for(int width=980;width<=1600;width+=71)
   for(int height=500;height<=900;height+=83){chart[3]=width;chart[4]=height;PanelDraw(true);
     if(g_pcReady)for(auto key:{"in","out","older","newer","live","range","move","center","vplus","vminus"}){
       auto p=props[PC_BUTTON+key];
       assert(p[OBJPROP_XDISTANCE]>=0&&p[OBJPROP_XDISTANCE]+p[OBJPROP_XSIZE]<width);
       assert(p[OBJPROP_YDISTANCE]+p[OBJPROP_YSIZE]<g_pcY);
     }
   }
 chart[4]=700;
 chart[3]=1000;PanelDraw(true);assert(g_pcReady); // smallest supported center
 chart[3]=799;PanelDraw(true);assert(!g_pcReady);assert(chart[1]==1&&chart[2]==1);
 chart[3]=1366;PanelDraw(true);assert(g_pcReady);
 showLiveChartPanel=false;PanelDraw(true);assert(!g_pcReady);assert(relayouts>=2);
 showLiveChartPanel=true;g_pc.fail=true;PanelDraw(true);assert(!g_pcReady);assert(chart[1]==1);
 g_pc.fail=false;PanelDraw(true);PanelDestroy();assert(chart[1]==1&&chart[2]==1);
 assert(masks["old_result_box"]==63&&masks["manual_line"]==7&&masks["new_line"]==15);
 assert(chart[CHART_MOUSE_SCROLL]==1 && chart[CHART_EVENT_MOUSE_MOVE]==0);
 assert(chart[CHART_SHOW_PRICE_SCALE]==1);assert(chart[CHART_COLOR_CHART_UP]==123);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'test.cpp').write_text(stub+palette+geometry+panel+main)
            subprocess.run(['g++','-std=c++17',str(path/'test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)

    def test_startup_and_strategy_layout(self):
        self.assertIn('chartStartFitOrders  = false', SOURCE)
        self.assertIn('g_pcFitOrders=chartStartFitOrders;', SOURCE)
        self.assertIn('MathMin(240,chartStartBars)', SOURCE)
        self.assertIn('MathMax(0,chartStartOffset)', SOURCE)
        self.assertNotIn('"str_S"', SOURCE)
        self.assertIn('"PENDING ORDERS"', SOURCE)
        self.assertIn('g_px[3]=8;g_py[3]=g_py[2]+g_ph[2]+8;', SOURCE)
        self.assertNotIn('#resource', SOURCE)

    def test_trailing_recorded_only_after_modify_success(self):
        management = SOURCE.split('void manageOpenPositions()\n  {')[1].split('void ApplyChartStyle()')[0]
        self.assertIn('bool   trailChanged = false;', management)
        self.assertIn('newSL = trSL; changed = true; trailChanged = true;', management)
        modify = management.index('if(!OrderModify(')
        success = management.index('else\n        {', modify)
        record = management.index('PanelRememberTrail(selTicket,newSL);')
        self.assertGreater(record, success)
        self.assertIn('if(trailChanged && newSL>0', management[success:record])

    def test_result_marker_arrays_initialized(self):
        panel = SOURCE.split('//=== Broker-data chart panel')[1].split('double SymbolAsk()')[0]
        for name in ('lastX', 'lastY'):
            initialization = panel.index('ArrayInitialize(' + name + ',0);')
            first_read = panel.index(name + '[c]')
            self.assertLess(initialization, first_read)

    def test_display_only_and_lifecycle(self):
        panel = SOURCE.split('//=== Broker-data chart panel')[1].split('double SymbolAsk()')[0]
        for api in ('OrderSend(', 'OrderModify(', 'OrderClose(', 'OrderDelete('):
            self.assertNotIn(api, panel)
        self.assertIn('CopyRates(', panel)
        self.assertIn('SymbolInfoTick(', panel)
        self.assertIn('if(id==CHARTEVENT_OBJECT_CLICK && PanelClick(sparam)) return;', SOURCE)
        self.assertIn('EventKillTimer();\n   PanelDestroy();', SOURCE)
        self.assertIn('if(g_pcReady) return; // Custom panel', SOURCE)

if __name__ == '__main__':
    unittest.main()
