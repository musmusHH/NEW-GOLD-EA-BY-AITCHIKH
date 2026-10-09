"""Run the EA's actual live aggregation/filter code with a small C++ MT4 stub.
This is not a substitute for compiling the full EA in MetaEditor.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'GOOOOLD X9 SETINGS.txt').read_text()

class LiveReportingTest(unittest.TestCase):
    def test_actual_live_loop(self):
        helpers = SOURCE[SOURCE.index('int ParseSid('):SOURCE.index('bool TagSeen(')]
        hud = SOURCE[SOURCE.index('void HudTick(bool force)\n  {'):]
        loop = hud[hud.index('   g_openPL = 0.0;'):hud.index('   RefreshStats();')]
        stub = r'''
#include <string>
#include <vector>
#include <cassert>
#include <cmath>
using namespace std;
const int OP_BUY=0, OP_SELL=1, OP_BUYLIMIT=2, OP_SELLLIMIT=3, OP_BUYSTOP=4, OP_SELLSTOP=5;
const int SELECT_BY_POS=0, MODE_TRADES=0;
const int MATCH_MAGIC_OR_COMMENT=0, MATCH_MAGIC_ONLY=1, MATCH_COMMENT_ONLY=2, MATCH_ALL_SYMBOL=3;
int filterMatchMode=0, activeMagicNumber=123457;
bool tagOnlyMyMagic=true;
string activeTradeSymbol="XAUUSD", tradeComment="gold X9 LAB by Mr. CapFree";
struct Order {int type, magic; string symbol, comment; double profit, swap, lots; int closed=0;};
vector<Order> orders;
Order current;
int OrdersTotal(){return orders.size();}
bool OrderSelect(int i,int,int){current=orders[i];return true;}
int OrderType(){return current.type;}
int OrderMagicNumber(){return current.magic;}
int OrderCloseTime(){return current.closed;}
string OrderSymbol(){return current.symbol;}
string OrderComment(){return current.comment;}
double OrderProfit(){return current.profit;}
double OrderSwap(){return current.swap;}
double OrderLots(){return current.lots;}
double OrderOpenPrice(){return 2000;}
double SymbolBid(){return 2010;}
double SymbolAsk(){return 2011;}
double CommissionCost(double lots){return lots*7;}
int StringFind(string a,string b){auto i=a.find(b);return i==string::npos?-1:int(i);}
string IntegerToString(int n){return to_string(n);}
template<class T, size_t N, class V> void ArrayInitialize(T (&a)[N],V v){for(auto &x:a)x=v;}
int reportedOpen=0,reportedBuys=0,reportedSells=0,reportedPendingBuy=0,reportedPendingSell=0;
int statOpenTrades[10]; double statOpenPL[10],g_openPL,activePipFactor=0.1;
'''
        main = r'''
int main(){
 // Terminal snapshot after yesterday's stops triggered: no entry-date cutoff.
 orders={{OP_BUY,123457,"XAUUSD","broker",20,-2,1},
         {OP_SELL,123456,"XAUUSD","gold X9 original",30,-1,2},
         {OP_BUYSTOP,123457,"XAUUSD","gold X9",0,0,1},
         {OP_SELLSTOP,123457,"XAUUSD","gold X9",0,0,1},
         {OP_BUY,9,"XAUUSD","manual",100,0,1},
         {OP_BUY,123457,"EURUSD","gold X9",100,0,1}};
 report(); assert(statOpenTrades[9]==2); assert(abs(g_openPL-26)<1e-9);
 report(); assert(statOpenTrades[9]==2); assert(abs(g_openPL-26)<1e-9);
 filterMatchMode=MATCH_MAGIC_ONLY;
 report(); assert(statOpenTrades[9]==1); assert(abs(g_openPL-11)<1e-9);
 filterMatchMode=MATCH_MAGIC_OR_COMMENT;
 orders.erase(orders.begin()); // closed ticket leaves the live pool
 report(); assert(statOpenTrades[9]==1); assert(abs(g_openPL-15)<1e-9);
 orders.clear(); report(); assert(statOpenTrades[9]==0); assert(g_openPL==0);
 // Four actual positions, thirteen pending orders: never display 3/10 as a limit.
 orders.push_back({OP_BUY,123457,"XAUUSD","broker",1,0,0.01});
 for(int i=0;i<3;i++)orders.push_back({OP_SELL,123457,"XAUUSD","broker",1,0,0.01});
 for(int i=0;i<3;i++)orders.push_back({i%2?OP_BUYLIMIT:OP_BUYSTOP,123457,"XAUUSD","broker",0,0,0.01});
 for(int i=0;i<10;i++)orders.push_back({i%2?OP_SELLLIMIT:OP_SELLSTOP,123457,"XAUUSD","broker",0,0,0.01});
 report();assert(reportedOpen==4);assert(reportedBuys==1&&reportedSells==3);
 assert(reportedPendingBuy==3&&reportedPendingSell==10);
 orders[4].type=OP_BUY; report();assert(reportedOpen==5);assert(reportedPendingBuy==2);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'test.cpp').write_text(stub+helpers+'void report(){\n'+loop+'reportedOpen=openCount;reportedBuys=buyCount;reportedSells=sellCount;reportedPendingBuy=pendingBuy;reportedPendingSell=pendingSell;}\n'+main)
            subprocess.run(['g++','-std=c++17',str(path/'test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)

    def test_position_displays_use_reporting_count(self):
        for name in ('top_pos', 'liv_V4'):
            line = next(line for line in SOURCE.splitlines()
                        if 'HudSetText(' in line and '"' + name + '"' in line)
            self.assertIn('IntegerToString(openCount)', line)
            self.assertNotIn('countOwnPositions()', line)
        self.assertIn('info[0]=IntegerToString(openCount)', SOURCE)
        self.assertIn('info[1]=IntegerToString(pendingBuy+pendingSell)', SOURCE)
        self.assertIn('if(countOwnPositions() >= activeMaxPositions) return;', SOURCE)
        mq4 = Path(__file__).resolve().parents[1] / 'gold_x9_FIXED.mq4'
        self.assertEqual(mq4.read_text(), SOURCE)

    def test_history_and_management_contracts(self):
        self.assertIn('int keys[]; ArrayResize(keys,total);', SOURCE)
        self.assertNotIn('nk<128', SOURCE)
        self.assertIn('TimeToStruct(OrderCloseTime(),dd)', SOURCE)
        own = SOURCE.split('bool SelectOwnPosition(int index)\n  {')[1].split('bool IsOwnPending')[0]
        self.assertIn('OrderMagicNumber() != activeMagicNumber', own)
        self.assertIn('"OPEN (LIVE)"', SOURCE)
        self.assertIn('int historyRow = r - ((openCount > 0) ? 1 : 0);', SOURCE)

if __name__ == '__main__':
    unittest.main()
