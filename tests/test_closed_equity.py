"""Execute the actual closed-history curve builder with MT4 API stubs."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'gold_x9_FIXED.mq4').read_text()

class ClosedEquityTests(unittest.TestCase):
    def test_closed_history_only(self):
        code = SOURCE.split('// Closed-result curve:')[1].split('int OnInit()')[0]
        code = '// Closed-result curve:' + code
        code = code.replace('ClosedEquityDeal g_eqHistory[];', 'vector<ClosedEquityDeal> g_eqHistory;')
        code = code.replace('ClosedEquityDeal deals[];', 'vector<ClosedEquityDeal> deals;')
        ring = SOURCE[SOURCE.index('void EqPush(double v, datetime t)\n  {'):SOURCE.index('#define EQ_COL_MAX')]
        stub = r'''
#include <vector>
#include <cassert>
#include <cmath>
using namespace std;
using datetime=long long;
const int EQ_MAX=512, SELECT_BY_POS=0,MODE_HISTORY=1;
double g_eqVal[EQ_MAX];datetime g_eqT[EQ_MAX];int g_eqN=0;
struct Deal{int ticket,type;datetime close;double profit,swap,lots;bool match=true;};
vector<Deal> history;Deal current;
double balance=125, floatingEquity=999;
bool failSelect=false;
int OrdersHistoryTotal(){return history.size();}
bool OrderSelect(int i,int,int){if(failSelect)return false;current=history[i];return true;}
bool IsMatchingOrder(){return current.match && (current.type==0 || current.type==1);}
int OrderTicket(){return current.ticket;}
datetime OrderCloseTime(){return current.close;}
double OrderProfit(){return current.profit;}double OrderSwap(){return current.swap;}
double OrderLots(){return current.lots;}double CommissionCost(double lots){return lots*7;}
double AccountBalance(){return balance;}
datetime TimeCurrent(){return 1000;}
template<class T> int ArrayResize(vector<T>& a,int n){a.resize(n);return n;}
template<class T> int ArraySize(vector<T>& a){return a.size();}
'''
        main = r'''
int main(){
 history={{2,0,200,37,0,1},{1,1,100,2,0,1},
          {99,4,300,100,0,1},{100,0,400,100,0,1,false}};
 SeedEquityHistory();assert(g_eqN==3);assert(g_eqClosedBase==100);
 assert(g_eqVal[0]==100 && g_eqVal[1]==95 && g_eqVal[2]==125);
 assert(g_eqT[0]<100 && g_eqT[1]==100 && g_eqT[2]==200);
 floatingEquity=-500;balance=200;
 SeedEquityHistory();assert(g_eqN==3 && g_eqVal[2]==125);
 history.push_back({3,0,500,12,0,1});
 SeedEquityHistory();assert(g_eqN==4 && g_eqVal[3]==130);
 SeedEquityHistory();assert(g_eqN==4); // No duplicate samples on repeated refresh.
 history.push_back({4,1,600,0,0,0}); // Zero-net close still gets a point.
 SeedEquityHistory();assert(g_eqN==5 && g_eqVal[4]==130);
 history.push_back({5,0,700,5.07,0,0.01}); // Partial-close history record.
 SeedEquityHistory();assert(g_eqN==6 && abs(g_eqVal[5]-135)<1e-9);
 failSelect=true;history.push_back({6,0,800,1,0,0});
 SeedEquityHistory();assert(g_eqN==6);failSelect=false;
 SeedEquityHistory();assert(g_eqN==7);
 // Reordered terminal history must produce the same chronological curve.
 swap(history[0],history[1]);SeedEquityHistory();assert(g_eqN==7 && g_eqVal[1]==95);
 history.clear();g_eqHistory.clear();g_eqHistoryReady=false;balance=100;
 SeedEquityHistory();assert(g_eqN==1 && g_eqVal[0]==100);
 for(int i=0;i<600;i++)history.push_back({i+1,0,2000+i,1,0,0});
 SeedEquityHistory();assert(g_eqN==601 && EqCount()==512);
 double last;datetime t;EqItem(511,last,t);assert(last==700 && t==2599);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'test.cpp').write_text(stub+ring+code+main)
            subprocess.run(['g++','-std=c++17',str(path/'test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)

    def test_no_live_sampling_and_independent_of_tags(self):
        self.assertNotIn('EqPush(equity', SOURCE)
        self.assertNotIn('g_lastEqLiveMs', SOURCE)
        self.assertIn('if(showEquityCurve) SeedEquityHistory();', SOURCE)
        hud = SOURCE.split('void HudTick(bool force)\n  {')[1]
        self.assertIn('SeedEquityHistory();', hud)
        risk = SOURCE.split('void TrackEquityAndDD()\n  {')[1].split('void ',1)[0]
        self.assertIn('AccountEquity()', risk)

if __name__ == '__main__':
    unittest.main()
