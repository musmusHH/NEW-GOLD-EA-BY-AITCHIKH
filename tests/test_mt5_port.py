"""Native MT5 bridge behavior against C++ stubs, NOT a MetaEditor compile."""
from pathlib import Path
import importlib.util
import re
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=(ROOT/'mt5/MT5Bridge.mqh').read_text()
SOURCE=(ROOT/'gold_x9_MT5.mq5').read_text()

class MT5PortTests(unittest.TestCase):
    def test_reproducible_and_platform_contracts(self):
        subprocess.run(['python', str(ROOT/'tools/build_mt5.py'), '--check'],check=True)
        self.assertIn('ACCOUNT_MARGIN_MODE_RETAIL_HEDGING',SOURCE)
        self.assertIn('input bool mt5AllowLiveTrading=false',SOURCE)
        self.assertIsNone(re.search(r'\bMODE_[A-Z_]+\b',SOURCE))
        self.assertIn('X9_MODE_SPREAD',SOURCE)
        self.assertIn('long ticket;',SOURCE)
        self.assertIn('long tickets[];',SOURCE)
        self.assertNotIn('orderPriceMap',SOURCE)
        self.assertNotIn('int ticket;',SOURCE)
        self.assertIn('void OnTradeTransaction(',SOURCE)
        self.assertIn('BORDER_RAISED',SOURCE)
        self.assertIn('void PanelLevelLabels(',SOURCE)
        self.assertNotIn('TagBoxCardDraw',SOURCE)
        body=SOURCE.split('// END native MT5 adapter')[1]
        for name in ['OrderSelect','OrderSend','OrderModify','OrderDelete','OrderClose','MarketInfo','OrdersTotal','OrdersHistoryTotal']:
            self.assertIsNone(re.search(r'\b'+name+r'\(',body),name)
        self.assertEqual(body.count('if(total<0) return;'),2)

    def test_strategy_math_and_management_preserved(self):
        original=(ROOT/'gold_x9_FIXED.mq4').read_text()
        normalized=SOURCE.split('// END native MT5 adapter')[1]
        names=set(re.findall(r'\bX9((?:Order\w*|Orders\w*|Account\w*|MarketInfo|IsTesting|IsVisualMode|RefreshRates|GetLastError|ResetLastError))\(',BRIDGE))
        for name in names: normalized=normalized.replace('X9'+name+'(',name+'(')
        normalized=re.sub(r'\bX9_MODE_([A-Z_]+)\b', r'MODE_\1', normalized)
        def body(text,name):
            match=re.search(r'^(?:void|bool|double) '+name+r'\([^\n]*\)\s*\{',text,re.M)
            start=match.start();i=match.end();depth=1
            while depth:
                depth+=(text[i]=='{')-(text[i]=='}');i+=1
            return text[start:i]
        for name in ['calculateStrategyLots','findSwingPoints','manageOpenPositions',
                     'expireStalePendingOrders','runStrategyTick','TrackEquityAndDD']:
            self.assertEqual(body(original,name),body(normalized,name),name)

    def test_bridge_history_tickets_ownership_and_requests(self):
        code=BRIDGE.replace('input bool','bool')
        code=code.replace('X9Record x9Selected,x9History[],x9Entries[];', 'X9Record x9Selected;vector<X9Record> x9History,x9Entries;')
        code=code.replace('X9Record snapshot[];','vector<X9Record> snapshot;')
        constants=sorted({'ACCOUNT_TRADE_MODE_DEMO'} | set(re.findall(r'\b(?:ACCOUNT_|MQL_|SYMBOL_|DEAL_|POSITION_|ORDER_|TRADE_|TERMINAL_)[A-Z_]+\b',code)))
        # Flags are independent bit values; remaining enum constants need only unique values.
        flags={'SYMBOL_EXPIRATION_GTC':1,'SYMBOL_EXPIRATION_SPECIFIED':2,'SYMBOL_FILLING_FOK':1,'SYMBOL_FILLING_IOC':2}
        enum='enum { '+','.join(f'{name}={flags.get(name,100+i)}' for i,name in enumerate(constants))+' };\n'
        stub=r'''
#include <string>
#include <vector>
#include <map>
#include <cmath>
#include <cassert>
#include <iostream>
using namespace std;
using datetime=long;using color=unsigned;using uint=unsigned;
using ENUM_ORDER_TYPE=int;
// Emulate the actual MT5 built-in that originally exposed the collision.
enum ENUM_SERIESMODE { MODE_SPREAD=4 };
struct MqlTick{double ask=2001,bid=2000;};
struct MqlTradeRequest {int action=0,type=0,type_time=0,type_filling=0;string symbol,comment;ulong magic=0,position=0,order=0;double volume=0,price=0,sl=0,tp=0;int deviation=0;datetime expiration=0;};
struct MqlTradeResult {uint retcode=0;ulong order=0;string comment;};
struct MqlTradeCheckResult {uint retcode=0;string comment;};
struct Native {ulong ticket;map<int,long> ints;map<int,double> doubles;map<int,string> strings;};
vector<Native> deals,positions,pending;int selectedPos=0,selectedOrder=0;
string _Symbol="XAUUSD";
int marginMode,tradeMode,expirationMode,fillingMode,executionMode;
bool testing=false,tradeAllowed=true,historyOK=true,checkOK=true,sendOK=true;
uint serverCode=0;int checks=0,sends=0;MqlTradeRequest last;
template<class T>int ArraySize(vector<T> &v){return v.size();}
template<class T>int ArrayResize(vector<T> &v,int n){if(n<0)return -1;v.resize(n);return n;}
template<class T>void ZeroMemory(T &v){v=T{};}
void ResetLastError(){}int GetLastError(){return 777;}
double NormalizeDouble(double x,int n){double m=pow(10.,n);return round(x*m)/m;}
double MathRound(double x){return round(x);}
template<class... T>void Print(T... v){}
datetime TimeCurrent(){return 2000;}
'''+enum+r'''
long AccountInfoInteger(int p){return p==ACCOUNT_MARGIN_MODE?marginMode:tradeMode;}
double AccountInfoDouble(int){return 10000;}
string AccountInfoString(int){return "USD";}
long MQLInfoInteger(int p){if(p==MQL_TESTER)return testing;if(p==MQL_TRADE_ALLOWED)return tradeAllowed;return true;}
long TerminalInfoInteger(int){return tradeAllowed;}
bool SymbolInfoTick(string,MqlTick &t){t=MqlTick{};return true;}
double SymbolInfoDouble(string,int p){
 if(p==SYMBOL_ASK)return 2001;if(p==SYMBOL_BID)return 2000;
 if(p==SYMBOL_TRADE_TICK_SIZE)return 0.05;if(p==SYMBOL_VOLUME_MIN)return 0.01;
 return 1;
}
long SymbolInfoInteger(string,int p){if(p==SYMBOL_SPREAD)return 80;if(p==SYMBOL_DIGITS)return 2;if(p==SYMBOL_EXPIRATION_MODE)return expirationMode;
 if(p==SYMBOL_FILLING_MODE)return fillingMode;if(p==SYMBOL_TRADE_EXEMODE)return executionMode;return 0;}
bool OrderCalcMargin(int,string,double lot,double,double &m){m=lot*100;return true;}
bool HistorySelect(int,datetime){return historyOK;}
int HistoryDealsTotal(){return deals.size();}
ulong HistoryDealGetTicket(int i){return deals[i].ticket;}
Native &deal(ulong ticket){for(auto &d:deals)if(d.ticket==ticket)return d;assert(false);return deals[0];}
long HistoryDealGetInteger(ulong t,int p){return deal(t).ints[p];}
double HistoryDealGetDouble(ulong t,int p){return deal(t).doubles[p];}
string HistoryDealGetString(ulong t,int p){return deal(t).strings[p];}
int PositionsTotal(){return positions.size();}int OrdersTotal(){return pending.size();}
bool PositionSelectByTicket(ulong t){for(int i=0;i<int(positions.size());i++)if(positions[i].ticket==t){selectedPos=i;return true;}return false;}
ulong PositionGetTicket(int i){return positions[i].ticket;}
long PositionGetInteger(int p){return positions[selectedPos].ints[p];}
double PositionGetDouble(int p){return positions[selectedPos].doubles[p];}
string PositionGetString(int p){return positions[selectedPos].strings[p];}
bool OrderSelect(ulong t){for(int i=0;i<int(pending.size());i++)if(pending[i].ticket==t){selectedOrder=i;return true;}return false;}
ulong OrderGetTicket(int i){return pending[i].ticket;}
long OrderGetInteger(int p){return pending[selectedOrder].ints[p];}
double OrderGetDouble(int p){return pending[selectedOrder].doubles[p];}
string OrderGetString(int p){return pending[selectedOrder].strings[p];}
bool OrderCheck(MqlTradeRequest &r,MqlTradeCheckResult &c){checks++;last=r;c.retcode=serverCode;return checkOK;}
bool OrderSend(MqlTradeRequest &r,MqlTradeResult &s){sends++;last=r;s.retcode=serverCode;s.order=9000000001UL;return sendOK;}
'''
        main=r'''
Native history(ulong ticket,long id,long side,long entry,double vol,double profit,int time,long magic,string comment){
 Native n{};n.ticket=ticket;n.ints={{DEAL_POSITION_ID,id},{DEAL_TYPE,side},{DEAL_ENTRY,entry},{DEAL_TIME,time},{DEAL_MAGIC,magic}};
 n.doubles={{DEAL_VOLUME,vol},{DEAL_PRICE,2000},{DEAL_PROFIT,profit},{DEAL_COMMISSION,-vol*2}};
 n.strings={{DEAL_SYMBOL,"XAUUSD"},{DEAL_COMMENT,comment}};return n;
}
int main(){
 marginMode=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;tradeMode=ACCOUNT_TRADE_MODE_DEMO;
 expirationMode=SYMBOL_EXPIRATION_GTC|SYMBOL_EXPIRATION_SPECIFIED;fillingMode=SYMBOL_FILLING_IOC;executionMode=SYMBOL_TRADE_EXECUTION_MARKET;x9Magic=123457;
 assert(X9MarketInfo(_Symbol,X9_MODE_SPREAD)==80);
 assert(X9MarketInfo(_Symbol,X9_MODE_POINT)==1);
 // A BUY closed with SELL deals must still report BUY, attributed to entry identity.
 deals={history(8000000001UL,7000000001L,DEAL_TYPE_BUY,DEAL_ENTRY_IN,1,0,100,123457,"X9 S9"),
        history(8000000002UL,7000000001L,DEAL_TYPE_SELL,DEAL_ENTRY_OUT,.4,20,200,0,"manual exit"),
        history(8000000003UL,7000000001L,DEAL_TYPE_SELL,DEAL_ENTRY_OUT_BY,.6,-3,300,0,"close by")};
 Native deposit=history(8000000004UL,0,9999,DEAL_ENTRY_IN,0,500,400,0,"deposit");deals.push_back(deposit);
 assert(X9OrdersHistoryTotal()==2);
 assert(X9OrderSelect(0,SELECT_BY_POS,X9_MODE_HISTORY));assert(X9OrderType()==OP_BUY);
 assert(X9OrderTicket()==8000000002L&&X9OrderMagicNumber()==123457&&X9OrderComment()=="X9 S9");
 assert(abs(X9OrderCommission()+1.6)<1e-9&&X9OrderLots()==.4&&X9OrderProfit()==20);
 // Tick/floating changes do not add samples; a corrected deal invalidates cleanly.
 assert(X9OrdersHistoryTotal()==2);deals[1].doubles[DEAL_PROFIT]=21;x9HistoryDirty=true;
 assert(X9OrdersHistoryTotal()==2);X9OrderSelect(0,SELECT_BY_POS,X9_MODE_HISTORY);assert(X9OrderProfit()==21);
 historyOK=false;x9HistoryDirty=true;assert(X9OrdersHistoryTotal()==-1);assert(x9History.size()==2);historyOK=true;
 Native p{};p.ticket=6000000001UL;p.ints={{POSITION_IDENTIFIER,7000000001L},{POSITION_MAGIC,123457},{POSITION_TYPE,POSITION_TYPE_BUY},{POSITION_TIME,100}};
 p.strings={{POSITION_SYMBOL,"XAUUSD"},{POSITION_COMMENT,"X9 S9"}};p.doubles={{POSITION_VOLUME,1},{POSITION_PRICE_OPEN,2000},{POSITION_PROFIT,15}};positions.push_back(p);
 Native o{};o.ticket=6000000002UL;o.ints={{ORDER_TYPE,ORDER_TYPE_SELL_STOP},{ORDER_MAGIC,123457}};o.strings={{ORDER_SYMBOL,"XAUUSD"}};o.doubles={{ORDER_VOLUME_CURRENT,.1}};pending.push_back(o);
 assert(X9OrdersTotal()==2);assert(X9OrderSelect(0,SELECT_BY_POS)&&X9OrderType()==OP_BUY);
 assert(X9OrderSelect(1,SELECT_BY_POS)&&X9OrderType()==OP_SELLSTOP);
 assert(X9OrderSelect(6000000001L,SELECT_BY_TICKET)&&X9OrderTicket()==6000000001L);
 serverCode=TRADE_RETCODE_PLACED;
 assert(X9OrderSend(_Symbol,OP_BUYSTOP,.1,2010.023,30,1990,2050,"X9",x9Magic,1800,0)==9000000001L);
 assert(last.action==TRADE_ACTION_PENDING&&last.type==ORDER_TYPE_BUY_STOP&&last.type_time==ORDER_TIME_SPECIFIED);
 assert(last.price==2010.0&&last.type_filling==ORDER_FILLING_RETURN);
 expirationMode=SYMBOL_EXPIRATION_GTC;
 assert(X9OrderSend(_Symbol,OP_SELLLIMIT,.1,2010,30,2020,1990,"X9",x9Magic,1800,0)>0);
 assert(last.type_time==ORDER_TIME_GTC&&last.expiration==0);
 expirationMode=0;int previous=sends;
 assert(X9OrderSend(_Symbol,OP_BUYSTOP,.1,2010,30,0,0,"X9",x9Magic,1800,0)<0&&sends==previous);
 serverCode=TRADE_RETCODE_DONE;
 assert(X9OrderModify(6000000001L,2000,2005,2050,0,0));assert(last.position==6000000001UL&&last.action==TRADE_ACTION_SLTP);
 assert(X9OrderClose(6000000001L,.5,2000,30,0));assert(last.position==6000000001UL&&last.type==ORDER_TYPE_SELL&&last.volume==.5&&last.type_filling==ORDER_FILLING_IOC);
 assert(X9OrderDelete(6000000002L,0)&&last.order==6000000002UL);
 // Broader reporting never grants management of another magic's position.
 positions[0].ints[POSITION_MAGIC]=999;previous=sends;
 assert(!X9OrderClose(6000000001L,.5,2000,30,0)&&sends==previous);
 assert(!X9OrderModify(6000000001L,2000,1990,2050,0,0));positions[0].ints[POSITION_MAGIC]=123457;
 tradeMode=ACCOUNT_TRADE_MODE_REAL;previous=sends;
 assert(!X9OrderClose(6000000001L,.5,2000,30,0)&&sends==previous);
 mt5AllowLiveTrading=true;assert(X9OrderClose(6000000001L,.5,2000,30,0));
 marginMode=999;previous=sends;assert(!X9OrderClose(6000000001L,.5,2000,30,0)&&sends==previous);
 marginMode=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;tradeMode=ACCOUNT_TRADE_MODE_DEMO;
 checkOK=false;previous=sends;serverCode=TRADE_RETCODE_NO_MONEY;
 assert(!X9OrderClose(6000000001L,.5,2000,30,0)&&sends==previous&&X9GetLastError()==134);
 checkOK=true;serverCode=999;assert(!X9OrderClose(6000000001L,.5,2000,30,0));
 assert(X9GetLastError()==999); // Unknown/server failure is never marked successful.
}
'''
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/'bridge.cpp').write_text(stub+code+main)
            subprocess.run(['g++','-std=c++17',str(path/'bridge.cpp'),'-o',str(path/'bridge')],check=True)
            subprocess.run([str(path/'bridge')],check=True)

if __name__=='__main__':unittest.main()
