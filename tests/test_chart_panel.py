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
using ENUM_TIMEFRAMES=int;
#define RGB(r,g,b) ((r<<16)|(g<<8)|b)
const color clrSilver=0xaaaaaa,clrWhite=0xffffff;
const int OP_BUY=0,OP_SELL=1,OP_BUYLIMIT=2,OP_SELLLIMIT=3,OP_BUYSTOP=4,OP_SELLSTOP=5;
const int CHART_SHOW_TRADE_LEVELS=1,CHART_FOREGROUND=2,CHART_WIDTH_IN_PIXELS=3,CHART_HEIGHT_IN_PIXELS=4;
const int OBJ_BUTTON=0,CORNER_LEFT_UPPER=0,OBJPROP_CORNER=0,OBJPROP_XDISTANCE=1,OBJPROP_YDISTANCE=2;
const int OBJPROP_XSIZE=3,OBJPROP_YSIZE=4,OBJPROP_BGCOLOR=5,OBJPROP_COLOR=6,OBJPROP_BORDER_COLOR=7;
const int OBJPROP_FONTSIZE=8,OBJPROP_HIDDEN=9,OBJPROP_SELECTABLE=10,OBJPROP_ZORDER=11,OBJPROP_STATE=12;
const int OBJPROP_TEXT=13,OBJPROP_BACK=14,OBJPROP_TOOLTIP=15,COLOR_FORMAT_ARGB_NORMALIZE=0;
const int SELECT_BY_TICKET=1,SELECT_BY_POS=0,MODE_TRADES=0,TIME_DATE=1,TIME_MINUTES=2,TIME_SECONDS=4;
const string TAG_PREFIX="GX9T_";
const int TAG_MAX=512;
int g_tagN=0; datetime g_tagTime[TAG_MAX]; double g_tagPrice[TAG_MAX],g_tagProfit[TAG_MAX]; color g_tagClr[TAG_MAX];
bool showDashboardPanel=true,showLiveChartPanel=true,drawResultTags=true,quoteOK=true;
string activeTradeSymbol="XAUUSD"; int activeSymbolDigits=2;
double activeSymbolPoint=0.01; int g_px[6]={1},g_pw[6]={280};
map<int,long> chart={{1,1},{2,1},{3,1366},{4,700}};
map<string,string> objects;
uint clockMs=1000; datetime latest=100000;
int barsAvailable=500,relayouts=0;
uint GetTickCount(){return clockMs;}
bool IsTesting(){return false;} bool IsVisualMode(){return false;}
long ChartGetInteger(int,int p){return chart[p];}
void ChartSetInteger(int,int p,long v){chart[p]=v;}
void ChartRedraw(int){}
int ObjectFind(int,string n){return objects.count(n)?0:-1;}
bool ObjectCreate(int,string n,int,int,int,int){objects[n]="";return true;}
void ObjectSetInteger(int,string,int,long){}
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
struct Order {int type;string symbol;int magic;double entry,sl,tp,profit;};
vector<Order> orders;Order selected;
int OrdersTotal(){return orders.size();}
bool OrderSelect(int i,int mode,int){if(mode==SELECT_BY_TICKET){for(auto o:orders)if(12345678+o.type==i){selected=o;return true;}return false;}selected=orders[i];return true;}
string OrderSymbol(){return selected.symbol;}
string accountCurrency="USD";
string AccountCurrency(){return accountCurrency;}
const int SYMBOL_TRADE_TICK_SIZE=1,SYMBOL_TRADE_TICK_VALUE=2;
double mockTickSize=0.01,mockTickValue=1;
double SymbolInfoDouble(string,int prop){return prop==1?mockTickSize:mockTickValue;}
int OrderCloseTime(){return 0;}
bool IsMatchingOrderIdentity(){return selected.symbol==activeTradeSymbol && selected.magic==123457;}
int OrderType(){return selected.type;}int OrderTicket(){return 12345678+selected.type;}
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
 PanelDraw(true);
 assert(contains("LIVE $"));assert(contains("TP~ $"));assert(contains("SL~ $"));
 assert(contains("+19.83"));assert(contains("-20.17"));assert(contains("Pending"));
 accountCurrency="EUR";PanelDraw(true);assert(contains("LIVE EUR"));accountCurrency="USD";
 assert(g_pcReady);assert(chart[1]==0 && chart[2]==0);
 // The table is bottom-anchored; the removed footer adds 44 pixels to candles.
 int oldBottom=g_pcH-52-(36+4*20)-26;
 assert(g_pcBottom==oldBottom+44);
 assert(g_pcBottom+26+36+4*20==g_pcH-PC_TABLE_BOTTOM_GAP);
 assert(g_pcLow<4140 && g_pcHigh>4200);
 assert(objects[PC_NAME].find("LIVE |")!=string::npos);assert(contains("BUY"));
 assert(objects[PC_NAME].find("SELL STOP")!=string::npos);
 assert(objects[PC_NAME].find("@1.10")==string::npos);
 assert(PanelPriceY(g_pcHigh)==g_pcTop);assert(PanelPriceY(g_pcLow)==g_pcBottom);
 assert(PanelPriceY(g_pcHigh+100)==g_pcTop);
 assert(PanelBarX(0,64)>PanelBarX(63,64));
 PanelClick(PC_BUTTON+"range"); assert(g_pcLow>4170);
 PanelClick(PC_BUTTON+"older");assert(g_pcOffset==32);assert(objects[PC_NAME].find("HISTORY |")!=string::npos);
 latest+=300;PanelDraw(true);assert(g_pcOffset==33);
 PanelClick(PC_BUTTON+"live");assert(g_pcOffset==0);
 for(int i=0;i<20;i++)PanelClick(PC_BUTTON+"in");assert(g_pcBars==16);
 for(int i=0;i<20;i++)PanelClick(PC_BUTTON+"out");assert(g_pcBars==240);
 clockMs+=61001;PanelDraw(true);assert(objects[PC_NAME].find("STALE")!=string::npos);
 quoteOK=false;PanelDraw(true);assert(objects[PC_NAME].find("No quote")!=string::npos);quoteOK=true;
 barsAvailable=0;PanelDraw(true);assert(contains("Waiting for broker"));barsAvailable=500;
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
   for(int height=500;height<=900;height+=83){chart[3]=width;chart[4]=height;PanelDraw(true);}
 chart[4]=700;
 chart[3]=1000;PanelDraw(true);assert(g_pcReady); // smallest supported center
 chart[3]=900;PanelDraw(true);assert(!g_pcReady);assert(chart[1]==1&&chart[2]==1);
 chart[3]=1366;PanelDraw(true);assert(g_pcReady);
 showLiveChartPanel=false;PanelDraw(true);assert(!g_pcReady);assert(relayouts>=2);
 showLiveChartPanel=true;g_pc.fail=true;PanelDraw(true);assert(!g_pcReady);assert(chart[1]==1);
 g_pc.fail=false;PanelDraw(true);PanelDestroy();assert(chart[1]==1&&chart[2]==1);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'test.cpp').write_text(stub+panel+main)
            subprocess.run(['g++','-std=c++17',str(path/'test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)

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
