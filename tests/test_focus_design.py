"""Compile actual Focus HUD/layout/palette code against bounded MT4 object stubs."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/'gold_x9_FIXED.mq4').read_text()

class FocusDesignTests(unittest.TestCase):
    def test_layout_objects_and_four_theme_cycle(self):
        enum=SOURCE[SOURCE.index('enum enumHudTheme'):SOURCE.index('//--- INPUT PARAMETERS')]
        palette=SOURCE[SOURCE.index('// Design 4: exactly four palettes'):SOURCE.index('color HudDim2()')]
        helpers=SOURCE[SOURCE.index('void HudRectObj('):SOURCE.index('void RefreshStats()\n  {')]
        palette=re.sub(r"C'(\d+),(\d+),(\d+)'",r'RGB(\1,\2,\3)',palette)
        stub=r'''
#include <map>
#include <string>
#include <cmath>
#include <cassert>
#include <algorithm>
using namespace std;
using color=unsigned int;using uint=unsigned int;
#define RGB(r,g,b) ((r<<16)|(g<<8)|b)
const string HUD_PREFIX="GX9H_";
const int HUD_MAXO=480,HUD_NP=6;
enum {OBJ_RECTANGLE_LABEL,OBJ_LABEL,OBJ_BUTTON,CORNER_LEFT_UPPER,BORDER_FLAT,ANCHOR_LEFT_UPPER,
OBJPROP_CORNER,OBJPROP_XSIZE,OBJPROP_YSIZE,OBJPROP_BGCOLOR,OBJPROP_BORDER_TYPE,OBJPROP_COLOR,
OBJPROP_FILL,OBJPROP_SELECTABLE,OBJPROP_HIDDEN,OBJPROP_BACK,OBJPROP_TEXT,OBJPROP_FONTSIZE,
OBJPROP_FONT,OBJPROP_ANCHOR,OBJPROP_XDISTANCE,OBJPROP_YDISTANCE,OBJPROP_TOOLTIP,OBJPROP_ZORDER,
OBJPROP_BORDER_COLOR,OBJPROP_STATE,CHART_WIDTH_IN_PIXELS,CHART_HEIGHT_IN_PIXELS};
string g_hName[HUD_MAXO];int g_hPanel[HUD_MAXO],g_hDx[HUD_MAXO],g_hDy[HUD_MAXO],g_hRA[HUD_MAXO];
int g_hSize[HUD_MAXO],g_hRect[HUD_MAXO],g_hW[HUD_MAXO],g_hH[HUD_MAXO];color g_hBg[HUD_MAXO];
int g_hN=0,g_px[6],g_py[6],g_pw[6],g_ph[6],g_chartW=0,g_chartH=0;
int g_focusRows=4,g_focusDockH=124,g_focusTableW=800,chartTradeRows=4,g_activeTheme=0;
bool g_focusReady=false,showEquityCurve=true,applyChartStyle=true;
int width=1280,height=800,destroyed=0,redraws=0;
// Trading/graph state must survive a theme switch.
int tradeState=77,zoom=80,offset=12;double riskPeak=501.25;
struct Node{int type;map<int,long> p;map<int,string> text;};map<string,Node> nodes;
int ObjectFind(int,string name){return nodes.count(name)?0:-1;}
bool ObjectCreate(int,string name,int type,int,int,int){nodes[name].type=type;return true;}
void ObjectSetInteger(int,string name,int prop,long value){if(nodes.count(name))nodes[name].p[prop]=value;}
void ObjectSetString(int,string name,int prop,string value){if(nodes.count(name))nodes[name].text[prop]=value;}
string ObjectGetString(int,string name,int prop){return nodes[name].text[prop];}
void ObjectsDeleteAll(int,string prefix){for(auto i=nodes.begin();i!=nodes.end();)if(i->first.find(prefix)==0)i=nodes.erase(i);else ++i;}
long ChartGetInteger(int,int prop){return prop==CHART_WIDTH_IN_PIXELS?width:height;}
void ChartRedraw(int){redraws++;}
void EqCanvasDestroy(){destroyed++;}void PanelDestroy(){destroyed++;}
void ApplyChartStyle(){}void HudTick(bool){}void PanelDraw(bool){}void EqDraw(){}
void HudCreate();void HudMoveAll();
string IntegerToString(int v){return to_string(v);}int StringToInteger(string s){return stoi(s);}
int StringLen(string s){return s.size();}string StringSubstr(string s,int start,int n=99999){return s.substr(start,n);}
int StringFind(string a,string b){auto pos=a.find(b);return pos==string::npos?-1:int(pos);}
string AccountCurrency(){return "USD";}
template<class A,class B> double MathMax(A a,B b){return max(double(a),double(b));}
template<class A,class B> double MathMin(A a,B b){return min(double(a),double(b));}
double MathCeil(double x){return ceil(x);}
'''
        main=r'''
int main(){
 for(int w:{800,900,1024,1280,1366,1920})for(int h:{560,600,720,800,1080}){
   width=w;height=h;HudLayout();
   for(int theme=0;theme<4;theme++){
     g_activeTheme=theme;nodes.clear();HudCreate();
     assert(g_hN<HUD_MAXO);assert(g_focusReady);
     assert(g_px[3]==8 && g_pw[3]==w-16);
     assert(g_py[2]+g_ph[2]<g_py[3]);
     assert(g_py[3]+g_ph[3]<g_py[5]);assert(g_py[5]+g_ph[5]<=h-8);
     assert(g_px[4]+g_pw[4]==w-8);
     assert(g_ph[3]-8-g_focusDockH-26-42>=100);
     for(auto &entry:nodes){auto &n=entry.second;
       int x=n.p[OBJPROP_XDISTANCE],y=n.p[OBJPROP_YDISTANCE];
       assert(x>=0&&x<w&&y>=0&&y<h);
       if(n.type!=OBJ_LABEL){assert(x+n.p[OBJPROP_XSIZE]<=w);assert(y+n.p[OBJPROP_YSIZE]<=h);}
     }
     assert(nodes.count(HUD_PREFIX+"theme_cycle"));
     assert(nodes.count(HUD_PREFIX+"trk_R4_6"));
     assert(nodes[HUD_PREFIX+"trk_title"].text[OBJPROP_TEXT]=="TRADE TRACKER");
     int start=g_activeTheme;for(int i=0;i<4;i++)HudCycleTheme();assert(g_activeTheme==start);
     assert(tradeState==77&&zoom==80&&offset==12&&riskPeak==501.25);
   }
 }
 width=1280;height=800;HudLayout();
 showEquityCurve=false;HudLayout();assert(g_focusTableW==g_pw[3]);
 chartTradeRows=40;showEquityCurve=true;HudLayout();assert(g_ph[3]-8-g_focusDockH-26-42>=100);
 HudSetText(HUD_PREFIX+"top_balance","123456789012345678901234567890.12",UiInk());
 assert(nodes[HUD_PREFIX+"top_balance"].text[OBJPROP_TEXT].find("...")!=string::npos);
 assert(nodes[HUD_PREFIX+"top_balance"].text[OBJPROP_TOOLTIP]=="123456789012345678901234567890.12");
 width=799;height=550;HudLayout();assert(!g_focusReady);assert(nodes.count(HUD_PREFIX+"small"));
 assert(nodes.count(HUD_PREFIX+"theme_cycle")==0);
}
'''
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/'focus.cpp').write_text(stub+enum+palette+helpers+main)
            subprocess.run(['g++','-std=c++17',str(path/'focus.cpp'),'-o',str(path/'focus')],check=True)
            subprocess.run([str(path/'focus')],check=True)

    def test_standalone_display_only_theme_switch(self):
        self.assertNotIn('#resource',SOURCE)
        switch=SOURCE.split('void HudCycleTheme()\n  {')[1].split('void RefreshStats()')[0]
        for operation in ('OrderSend(', 'OrderModify(', 'OrderClose(', 'OrderDelete(', 'OnInit('):
            self.assertNotIn(operation,switch)
        self.assertIn('(g_activeTheme+1)%4',switch)
        self.assertIn('sparam==HUD_PREFIX+"theme_cycle"',SOURCE)
        panel=SOURCE.split('//=== Broker-data chart panel')[1].split('double SymbolAsk()')[0]
        self.assertNotIn("C'12,18,26'",panel)
        self.assertIn('UiPanel()',panel)

if __name__=='__main__':unittest.main()
