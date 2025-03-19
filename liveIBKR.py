from ib_insync import *
util.startLoop()
import datetime
import pandas as pd
from stockstats import StockDataFrame as Sdf
from config import can_trade_upto, ib_config, folder_name, stop_loss_atr, next_stop_loss_atr, max_allocation
import os 

def create_folder(parent):
    directory = os.path.join(parent, "live_simulation")
    if not os.path.exists(directory):
        os.makedirs(directory)
        
class LiveTrading:
    def __init__(self) -> None:
        #  get current cash in account
        try:
            self.connect2Ibkr()
        except:
            raise ValueError("can not connect to Interactive Broker")
        
        self.currentCash = [v for v in self.ib.accountValues() if v.tag == 'NetLiquidationByCurrency' and v.currency == 'BASE'][0].value 
        self.currentCash = float(self.currentCash)
        self.max_allocation = max_allocation
        self.trade= {}
        self.completed_trade = {}
    
    def connect2Ibkr(self):
        port = ib_config["port"]
        ip = ib_config["ip"]
        clientId = ib_config["clientId"]
        
        self.ib = IB()
        self.ib.connect('127.0.0.1', 7497, clientId=999)
    
    def Disconnect(self):
        self.ib.disconnect()
    
    def _getOngoingTradeDetails(self):
        self.trade = {}
        try:
            dict_obj = pd.read_csv(f"./{folder_name}/live_simulation/onGoing_trade.csv").to_dict(orient='records')
            for record in dict_obj:
                key = record.pop('Unnamed: 0')
                self.trade[key] = record
        except:
            pass
            
    def _getCurrentPosition(self):
        self._getOngoingTradeDetails()
        
        position = self.ib.positions()
        temp_positionDetails = []
        for p in position:
            _symbol = p.contract.symbol
            temp_positionDetails.append(_symbol)
            if _symbol in self.trade.keys():
                self.trade[_symbol]["entry_price"] = p.avgCost
                self.trade[_symbol]["qty"] = p.position
        
        temp_trade = {key: value for key, value in self.trade.items() if key in temp_positionDetails}
        self.trade = temp_trade.copy()
                
    def _getCurrentDate(self):
        self.today = datetime.date.today().strftime("%Y-%m-%d")
    
    def _checkTodayPattern(self):
        self._getCurrentDate()
        pattern_df = pd.read_csv(f"./{folder_name}/pattern.csv")
        pattern_df = pattern_df[pattern_df["date"]==self.today].sort_values(by=["rvol"], ascending=False)
        pattern_ticker = pattern_df["tic"].unique().tolist()
        return pattern_df["tic"].unique().tolist()
    
    def createContract(self, ticker):
        contract = Stock(ticker, "SMART", "USD")
        self.ib.qualifyContracts(contract)
        return contract
    
    def process(self, **kwargs):
        duration = kwargs["duration"]
        time_interval = kwargs["time_interval"]
        self.pattern = self._checkTodayPattern()
        if len(self.pattern) == 0:
            print("No pattern found for today")
            self.Disconnect()
            return
        self._getCurrentPosition()    
        temp_trade = self.trade.copy()
        for tic, val in self.trade.items():
            contract = self.createContract(tic)
            df = self.downloadHistoryData(tic, contract, **kwargs)
            df = self.calculateATR(df)
            if df["low"] <= val["stop_loss"]:
                order = MarketOrder('SELL', int(val["qty"]))
                trade = self.ib.placeOrder(contract, order)
                while not trade.isDone():
                    self.ib.waitOnUpdate()
                del temp_trade[tic]
                
            elif (df["close"] >=val["next_stop_loss"]):
                # move Stop loss dynamically
                temp_trade[tic]["stop_loss"] = df["close"] - df["atr"] * stop_loss_atr
                temp_trade[tic]["next_stop_loss"] = df["close"] + df["atr"] * next_stop_loss_atr
                lmtId = val["lmtId"]
                qty = val["qty"]
                self._cancelOpenOrderId(lmtId) # cancel older limit order
                limitOrder = LimitOrder('SELL', qty, round(temp_trade[tic]["stop_loss"],2)) #place new limit order
                limitTrade = self.ib.placeOrder(contract, limitOrder)
                # limitTrade = ib.placeOrder(contract, limitTrade)
                while not limitTrade.isDone():
                    self.ib.waitOnUpdate()
                temp_trade[tic]["lmtId"] = limitOrder.orderId
                
        self.trade = temp_trade.copy()
        # now place new order
        
        for tic in self.pattern:
            if len(self.trade.keys()) > can_trade_upto:
                self.Disconnect()
                return
            if tic in self.trade.keys():
                continue
            contract = self.createContract(tic)
            df = self.downloadHistoryData(tic, contract, **kwargs)
            if df.empty:
               continue
            df = self.calculateATR(df)
            close = df["close"]
            stop_loss = close - df["atr"]*2
            next_stop_loss = close + df["atr"]*2
            qty = (self.max_allocation * 0.9) // close
            # print(f" current cash: {self.currentCash} {type(self.currentCash)}max allocation: {self.max_allocation}")
            if qty == 0 or self.currentCash < self.max_allocation:
                print("not enough money for ", tic)
                continue
            order = MarketOrder('BUY', qty)
            trade = self.ib.placeOrder(contract, order)
            while not trade.isDone():
                self.ib.waitOnUpdate()
            print(f"order placed(Buy) {tic} = {trade.order.totalQuantity}")
            limitOrder = StopOrder('SELL', trade.order.totalQuantity, round(stop_loss,2),tif='GTC')
            # limitOrder = LimitOrder("SELL", 100, 115.0)
            
            limitTrade = self.ib.placeOrder(contract, limitOrder)
            #print(f"Limit order placed(Sell) {tic} = {trade.order.totalQuantity} Limit price={stop_loss}")
            print()
            while not limitTrade.isDone():
                self.ib.waitOnUpdate()
            self.trade[tic]={
                "amount": self.max_allocation,
                "enter_date": datetime.date.today().strftime("%Y-%m-%d"),
                "entry_price": trade.orderStatus.avgFillPrice,
                "current_price": close,
                "qty": int(trade.order.totalQuantity),
                "stop_loss": stop_loss,
                "next_stop_loss": next_stop_loss,
                "pl": 0,
                "lmtId": trade.order.orderId
            }
            
            
        self.Disconnect()
        
        ongoing_trade = pd.DataFrame.from_dict(self.trade, orient='index')
        ongoing_trade.to_csv(f"./{folder_name}/live_simulation/onGoing_trade.csv")
            
    def _cancelOpenOrderId(self, id):
        for i in self.ib.openOrders():
            if i.orderId == id:
                self.ib.cancelOrder(i)
    
    def downloadHistoryData(self, symbol, contract, **kwargs):
        duration=kwargs["duration"]
        time_interval = kwargs["time_interval"]
        df = pd.DataFrame()
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=time_interval,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1)
            df = util.df(bars)
            
        except:
            df = pd.DataFrame()
        return df
    
    def calculateATR(self, df):
        df = Sdf.retype(df)
        df["atr"] = df["atr_14"]
        df["date"] = df.index
        return df.iloc[-1]
    
if __name__ == "__main__":
    create_folder(folder_name)
    live = LiveTrading()
    kwargs={
        "time_interval" : "1 day",
        "duration": "22 D"
    }
    live.process(**kwargs)