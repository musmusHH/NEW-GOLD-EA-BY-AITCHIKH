// X9 native MT5 hedging adapter. Included inline by tools/build_mt5.py.
// No DLLs. MT4-style views are snapshots of MT5 positions/orders/exit deals.
input bool mt5AllowLiveTrading=false; // Explicit opt-in AFTER tester/demo validation

#define OP_BUY 0
#define OP_SELL 1
#define OP_BUYLIMIT 2
#define OP_SELLLIMIT 3
#define OP_BUYSTOP 4
#define OP_SELLSTOP 5
#define SELECT_BY_POS 0
#define SELECT_BY_TICKET 1
#define MODE_TRADES 0
#define MODE_HISTORY 1
#define ERR_TRADE_CONTEXT_BUSY 146
#define ERR_REQUOTE 138
#define ERR_PRICE_CHANGED 135
#define ERR_OFF_QUOTES 136
enum X9MarketProperty { MODE_ASK,MODE_BID,MODE_POINT,MODE_DIGITS,MODE_STOPLEVEL,
 MODE_FREEZELEVEL,MODE_MAXLOT,MODE_MINLOT,MODE_LOTSTEP,MODE_TICKSIZE,MODE_TICKVALUE,
 MODE_SPREAD,MODE_MARGINREQUIRED };

struct X9Record
  {
   long ticket,magic,position;
   int type;
   string symbol,comment;
   datetime opened,closed,expiration;
   double volume,entry,exit,sl,tp,profit,swap,commission;
  };
X9Record x9Selected,x9History[],x9Entries[];
long x9Magic=0;
int x9Error=0;
bool x9HistoryDirty=true;
datetime x9HistoryChecked=0;
int x9NativeDealCount=-1;

bool X9IsTesting(){return (bool)MQLInfoInteger(MQL_TESTER);}
bool X9IsVisualMode(){return (bool)MQLInfoInteger(MQL_VISUAL_MODE);}
double X9AccountBalance(){return AccountInfoDouble(ACCOUNT_BALANCE);}
double X9AccountEquity(){return AccountInfoDouble(ACCOUNT_EQUITY);}
double X9AccountMargin(){return AccountInfoDouble(ACCOUNT_MARGIN);}
double X9AccountFreeMargin(){return AccountInfoDouble(ACCOUNT_MARGIN_FREE);}
string X9AccountCurrency(){return AccountInfoString(ACCOUNT_CURRENCY);}
bool X9RefreshRates(){MqlTick tick;return SymbolInfoTick(_Symbol,tick);}
int X9GetLastError(){return x9Error!=0?x9Error:GetLastError();}
void X9ResetLastError(){x9Error=0;ResetLastError();}

// Returned tick size is a PRICE increment, as used by the strategy's risk math.
double X9MarketInfo(string symbol,int mode)
  {
   switch(mode)
     {
      case MODE_ASK:return SymbolInfoDouble(symbol,SYMBOL_ASK);
      case MODE_BID:return SymbolInfoDouble(symbol,SYMBOL_BID);
      case MODE_POINT:return SymbolInfoDouble(symbol,SYMBOL_POINT);
      case MODE_DIGITS:return (double)SymbolInfoInteger(symbol,SYMBOL_DIGITS);
      case MODE_STOPLEVEL:return (double)SymbolInfoInteger(symbol,SYMBOL_TRADE_STOPS_LEVEL);
      case MODE_FREEZELEVEL:return (double)SymbolInfoInteger(symbol,SYMBOL_TRADE_FREEZE_LEVEL);
      case MODE_MAXLOT:return SymbolInfoDouble(symbol,SYMBOL_VOLUME_MAX);
      case MODE_MINLOT:return SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN);
      case MODE_LOTSTEP:return SymbolInfoDouble(symbol,SYMBOL_VOLUME_STEP);
      case MODE_TICKSIZE:return SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE);
      case MODE_TICKVALUE:return SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_VALUE);
      case MODE_SPREAD:return (double)SymbolInfoInteger(symbol,SYMBOL_SPREAD);
      case MODE_MARGINREQUIRED:
        {
         double margin=0;double lot=SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN);
         if(lot>0 && OrderCalcMargin(ORDER_TYPE_BUY,symbol,lot,SymbolInfoDouble(symbol,SYMBOL_ASK),margin)) return margin/lot;
         return 0; // Every actual request is also validated with OrderCheck.
        }
     }
   return 0;
  }

int X9Type(ENUM_ORDER_TYPE type)
  {
   switch(type)
     {
      case ORDER_TYPE_BUY:return OP_BUY;
      case ORDER_TYPE_SELL:return OP_SELL;
      case ORDER_TYPE_BUY_LIMIT:return OP_BUYLIMIT;
      case ORDER_TYPE_SELL_LIMIT:return OP_SELLLIMIT;
      case ORDER_TYPE_BUY_STOP:return OP_BUYSTOP;
      case ORDER_TYPE_SELL_STOP:return OP_SELLSTOP;
     }
   return -1; // Stop-limit orders are not managed by this strategy.
  }
ENUM_ORDER_TYPE X9NativeType(int type)
  {
   if(type==OP_BUY)return ORDER_TYPE_BUY;
   if(type==OP_SELL)return ORDER_TYPE_SELL;
   if(type==OP_BUYLIMIT)return ORDER_TYPE_BUY_LIMIT;
   if(type==OP_SELLLIMIT)return ORDER_TYPE_SELL_LIMIT;
   if(type==OP_BUYSTOP)return ORDER_TYPE_BUY_STOP;
   return ORDER_TYPE_SELL_STOP;
  }

// Sorted entry identity map: exit-deal comments/magic can differ after manual closure.
int X9EntryIndex(long position,bool insert)
  {
   int lo=0,hi=ArraySize(x9Entries);
   while(lo<hi){int mid=(lo+hi)/2;if(x9Entries[mid].position<position)lo=mid+1;else hi=mid;}
   if(lo<ArraySize(x9Entries) && x9Entries[lo].position==position)return lo;
   if(!insert)return -1;
   int n=ArraySize(x9Entries);if(ArrayResize(x9Entries,n+1)!=n+1)return -1;
   for(int i=n;i>lo;i--)x9Entries[i]=x9Entries[i-1];
   ZeroMemory(x9Entries[lo]);x9Entries[lo].position=position;return lo;
  }

bool X9BuildHistory()
  {
   if(!x9HistoryDirty && TimeCurrent()-x9HistoryChecked<5)return true;
   if(!HistorySelect(0,TimeCurrent()))return false;
   int total=HistoryDealsTotal();
   x9HistoryChecked=TimeCurrent();
   if(!x9HistoryDirty && total==x9NativeDealCount)return true;
   x9HistoryDirty=true;
   ArrayResize(x9Entries,0);
   for(int i=0;i<total;i++)
     {
      ulong ticket=HistoryDealGetTicket(i);if(ticket==0)return false;
      long type=HistoryDealGetInteger(ticket,DEAL_TYPE),entry=HistoryDealGetInteger(ticket,DEAL_ENTRY);
      if((type!=DEAL_TYPE_BUY && type!=DEAL_TYPE_SELL) || entry!=DEAL_ENTRY_IN)continue;
      int index=X9EntryIndex(HistoryDealGetInteger(ticket,DEAL_POSITION_ID),true);if(index<0)return false;
      double volume=HistoryDealGetDouble(ticket,DEAL_VOLUME),price=HistoryDealGetDouble(ticket,DEAL_PRICE);
      double oldVolume=x9Entries[index].volume;
      if(oldVolume==0)
        {
         x9Entries[index].type=type==DEAL_TYPE_BUY?OP_BUY:OP_SELL;
         x9Entries[index].symbol=HistoryDealGetString(ticket,DEAL_SYMBOL);
         x9Entries[index].comment=HistoryDealGetString(ticket,DEAL_COMMENT);
         x9Entries[index].magic=HistoryDealGetInteger(ticket,DEAL_MAGIC);
         x9Entries[index].opened=(datetime)HistoryDealGetInteger(ticket,DEAL_TIME);
        }
      x9Entries[index].volume+=volume;
      if(x9Entries[index].volume>0)x9Entries[index].entry=(x9Entries[index].entry*oldVolume+price*volume)/x9Entries[index].volume;
      x9Entries[index].commission+=HistoryDealGetDouble(ticket,DEAL_COMMISSION)+HistoryDealGetDouble(ticket,DEAL_FEE);
     }
   X9Record snapshot[];
   if(ArrayResize(snapshot,total)!=total)return false;
   int count=0;
   for(int i=0;i<total;i++)
     {
      ulong ticket=HistoryDealGetTicket(i);if(ticket==0)return false;
      long type=HistoryDealGetInteger(ticket,DEAL_TYPE),entry=HistoryDealGetInteger(ticket,DEAL_ENTRY);
      if((type!=DEAL_TYPE_BUY && type!=DEAL_TYPE_SELL) || (entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY))continue;
      int index=X9EntryIndex(HistoryDealGetInteger(ticket,DEAL_POSITION_ID),false);
      if(index<0)continue; // Incomplete broker history: don't attribute unknown positions to this EA.
      X9Record row=x9Entries[index];
      row.ticket=(long)ticket;row.closed=(datetime)HistoryDealGetInteger(ticket,DEAL_TIME);
      row.volume=HistoryDealGetDouble(ticket,DEAL_VOLUME);row.exit=HistoryDealGetDouble(ticket,DEAL_PRICE);
      row.profit=HistoryDealGetDouble(ticket,DEAL_PROFIT);row.swap=HistoryDealGetDouble(ticket,DEAL_SWAP);
      row.commission=HistoryDealGetDouble(ticket,DEAL_COMMISSION)+HistoryDealGetDouble(ticket,DEAL_FEE);
      if(x9Entries[index].volume>0)row.commission+=x9Entries[index].commission*row.volume/x9Entries[index].volume;
      snapshot[count++]=row;
     }
   if(ArrayResize(x9History,count)!=count)return false;
   for(int i=0;i<count;i++)x9History[i]=snapshot[i];
   x9NativeDealCount=total;x9HistoryDirty=false;return true;
  }
int X9OrdersHistoryTotal(){if(!X9BuildHistory())return -1;return ArraySize(x9History);}
int X9OrdersTotal(){return PositionsTotal()+OrdersTotal();}

bool X9LoadPosition(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket))return false;
   ZeroMemory(x9Selected);
   x9Selected.ticket=(long)ticket;x9Selected.position=PositionGetInteger(POSITION_IDENTIFIER);
   x9Selected.type=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?OP_BUY:OP_SELL;
   x9Selected.magic=PositionGetInteger(POSITION_MAGIC);
   x9Selected.symbol=PositionGetString(POSITION_SYMBOL);x9Selected.comment=PositionGetString(POSITION_COMMENT);
   x9Selected.opened=(datetime)PositionGetInteger(POSITION_TIME);
   x9Selected.volume=PositionGetDouble(POSITION_VOLUME);x9Selected.entry=PositionGetDouble(POSITION_PRICE_OPEN);
   x9Selected.sl=PositionGetDouble(POSITION_SL);x9Selected.tp=PositionGetDouble(POSITION_TP);
   x9Selected.profit=PositionGetDouble(POSITION_PROFIT);x9Selected.swap=PositionGetDouble(POSITION_SWAP);
   int index=X9EntryIndex(x9Selected.position,false);
   if(index>=0 && x9Entries[index].volume>0)x9Selected.commission=x9Entries[index].commission*x9Selected.volume/x9Entries[index].volume;
   return true;
  }
bool X9LoadPending(ulong ticket)
  {
   if(!OrderSelect(ticket))return false;
   ZeroMemory(x9Selected);
   x9Selected.ticket=(long)ticket;x9Selected.type=X9Type((ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE));
   x9Selected.magic=OrderGetInteger(ORDER_MAGIC);x9Selected.symbol=OrderGetString(ORDER_SYMBOL);
   x9Selected.comment=OrderGetString(ORDER_COMMENT);x9Selected.opened=(datetime)OrderGetInteger(ORDER_TIME_SETUP);
   x9Selected.expiration=(datetime)OrderGetInteger(ORDER_TIME_EXPIRATION);
   x9Selected.volume=OrderGetDouble(ORDER_VOLUME_CURRENT);x9Selected.entry=OrderGetDouble(ORDER_PRICE_OPEN);
   x9Selected.sl=OrderGetDouble(ORDER_SL);x9Selected.tp=OrderGetDouble(ORDER_TP);return true;
  }
bool X9OrderSelect(long value,int select,int pool=MODE_TRADES)
  {
   ZeroMemory(x9Selected);x9Selected.type=-1;
   if(pool==MODE_HISTORY)
     {
      if(!X9BuildHistory())return false;
      if(select==SELECT_BY_POS){if(value<0 || value>=ArraySize(x9History))return false;x9Selected=x9History[(int)value];return true;}
      for(int i=0;i<ArraySize(x9History);i++)if(x9History[i].ticket==value){x9Selected=x9History[i];return true;}
      return false;
     }
   if(select==SELECT_BY_TICKET)return X9LoadPosition((ulong)value) || X9LoadPending((ulong)value);
   int positions=PositionsTotal();if(value<0 || value>=positions+OrdersTotal())return false;
   if(value<positions)return X9LoadPosition(PositionGetTicket((int)value));
   return X9LoadPending(OrderGetTicket((int)value-positions));
  }
long X9OrderTicket(){return x9Selected.ticket;}
long X9OrderMagicNumber(){return x9Selected.magic;}
int X9OrderType(){return x9Selected.type;}
string X9OrderSymbol(){return x9Selected.symbol;}
string X9OrderComment(){return x9Selected.comment;}
datetime X9OrderOpenTime(){return x9Selected.opened;}
datetime X9OrderCloseTime(){return x9Selected.closed;}
datetime X9OrderExpiration(){return x9Selected.expiration;}
double X9OrderOpenPrice(){return x9Selected.entry;}
double X9OrderClosePrice(){return x9Selected.exit;}
double X9OrderLots(){return x9Selected.volume;}
double X9OrderStopLoss(){return x9Selected.sl;}
double X9OrderTakeProfit(){return x9Selected.tp;}
double X9OrderProfit(){return x9Selected.profit;}
double X9OrderSwap(){return x9Selected.swap;}
double X9OrderCommission(){return x9Selected.commission;}

bool X9TradingAllowed()
  {
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING){x9Error=133;return false;}
   if(!X9IsTesting() && AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_REAL && !mt5AllowLiveTrading){x9Error=133;return false;}
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED) || !TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)){x9Error=133;return false;}
   return true;
  }
int X9TradeError(uint retcode)
  {
   if(retcode==TRADE_RETCODE_REQUOTE)return ERR_REQUOTE;
   if(retcode==TRADE_RETCODE_PRICE_CHANGED)return ERR_PRICE_CHANGED;
   if(retcode==TRADE_RETCODE_PRICE_OFF)return ERR_OFF_QUOTES;
   if(retcode==TRADE_RETCODE_INVALID_EXPIRATION)return 147;
   if(retcode==TRADE_RETCODE_NO_MONEY)return 134;
   if(retcode==TRADE_RETCODE_INVALID_STOPS)return 130;
   return (int)retcode; // In particular, no automatic retry on timeout/unknown acceptance.
  }
bool X9Submit(MqlTradeRequest &request,MqlTradeResult &result)
  {
   X9ResetLastError();if(!X9TradingAllowed())return false;
   MqlTradeCheckResult check={};
   if(!OrderCheck(request,check)){x9Error=X9TradeError(check.retcode);Print("X9 MT5 check failed: ",check.retcode," ",check.comment);return false;}
   bool sent=OrderSend(request,result);
   bool accepted=(result.retcode==TRADE_RETCODE_DONE || result.retcode==TRADE_RETCODE_DONE_PARTIAL ||
      (request.action==TRADE_ACTION_PENDING && result.retcode==TRADE_RETCODE_PLACED) ||
      (request.action==TRADE_ACTION_SLTP && result.retcode==TRADE_RETCODE_NO_CHANGES));
   if(!sent || !accepted){x9Error=X9TradeError(result.retcode);Print("X9 MT5 request failed: ",result.retcode," ",result.comment);return false;}
   x9HistoryDirty=true;return true;
  }
double X9Price(string symbol,double price)
  {
   if(price==0)return 0;
   double step=SymbolInfoDouble(symbol,SYMBOL_TRADE_TICK_SIZE);
   if(step>0)price=MathRound(price/step)*step;
   return NormalizeDouble(price,(int)SymbolInfoInteger(symbol,SYMBOL_DIGITS));
  }
long X9OrderSend(string symbol,int type,double lots,double price,int deviation,double sl,double tp,string comment,long magic,datetime expiration,color arrow)
  {
   if(symbol!=_Symbol || magic!=x9Magic || type<OP_BUYLIMIT || type>OP_SELLSTOP){x9Error=3;return -1;}
   MqlTradeRequest request={};MqlTradeResult result={};
   request.action=TRADE_ACTION_PENDING;request.symbol=symbol;request.magic=(ulong)magic;
   request.type=X9NativeType(type);request.volume=lots;request.price=X9Price(symbol,price);
   request.sl=X9Price(symbol,sl);request.tp=X9Price(symbol,tp);request.deviation=deviation;request.comment=comment;
   request.type_filling=ORDER_FILLING_RETURN;
   long modes=SymbolInfoInteger(symbol,SYMBOL_EXPIRATION_MODE);
   if(expiration>0 && (modes & SYMBOL_EXPIRATION_SPECIFIED)!=0){request.type_time=ORDER_TIME_SPECIFIED;request.expiration=expiration;}
   else if((modes & SYMBOL_EXPIRATION_GTC)!=0)request.type_time=ORDER_TIME_GTC; // Strategy expires it locally.
   else {x9Error=147;return -1;} // Don't silently substitute DAY expiry.
   if(!X9Submit(request,result))return -1;
   return result.order>0?(long)result.order:-1;
  }
bool X9OwnPosition(long ticket)
  {
   return PositionSelectByTicket((ulong)ticket) && PositionGetInteger(POSITION_MAGIC)==x9Magic && PositionGetString(POSITION_SYMBOL)==_Symbol;
  }
bool X9OrderModify(long ticket,double entry,double sl,double tp,datetime expiration,color arrow)
  {
   if(!X9OwnPosition(ticket)){x9Error=3;return false;}
   MqlTradeRequest request={};MqlTradeResult result={};
   request.action=TRADE_ACTION_SLTP;request.position=(ulong)ticket;request.symbol=_Symbol;request.magic=(ulong)x9Magic;
   request.sl=X9Price(_Symbol,sl);request.tp=X9Price(_Symbol,tp);return X9Submit(request,result);
  }
bool X9OrderDelete(long ticket,color arrow)
  {
   if(!OrderSelect((ulong)ticket) || OrderGetInteger(ORDER_MAGIC)!=x9Magic || OrderGetString(ORDER_SYMBOL)!=_Symbol){x9Error=3;return false;}
   MqlTradeRequest request={};MqlTradeResult result={};
   request.action=TRADE_ACTION_REMOVE;request.order=(ulong)ticket;request.symbol=_Symbol;request.magic=(ulong)x9Magic;
   return X9Submit(request,result);
  }
bool X9OrderClose(long ticket,double lots,double price,int deviation,color arrow)
  {
   if(!X9OwnPosition(ticket)){x9Error=3;return false;}
   MqlTradeRequest request={};MqlTradeResult result={};
   request.action=TRADE_ACTION_DEAL;request.position=(ulong)ticket;request.symbol=_Symbol;request.magic=(ulong)x9Magic;
   request.type=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?ORDER_TYPE_SELL:ORDER_TYPE_BUY;
   if(lots<=0 || lots>PositionGetDouble(POSITION_VOLUME)){x9Error=131;return false;}
   request.volume=lots;request.deviation=deviation;
   MqlTick tick;if(!SymbolInfoTick(_Symbol,tick)){x9Error=ERR_OFF_QUOTES;return false;}
   request.price=request.type==ORDER_TYPE_BUY?tick.ask:tick.bid;
   long filling=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_FOK)!=0)request.type_filling=ORDER_FILLING_FOK;
   else if((filling & SYMBOL_FILLING_IOC)!=0)request.type_filling=ORDER_FILLING_IOC;
   else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE)!=SYMBOL_TRADE_EXECUTION_MARKET)request.type_filling=ORDER_FILLING_RETURN;
   else {x9Error=3;return false;}
   return X9Submit(request,result);
  }
