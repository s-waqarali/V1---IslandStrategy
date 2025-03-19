from ib_insync import *
import pandas as pd
# from ta.utils import dropna
# from ta.trend import SMAIndicator
from datetime import datetime
from stockstats import StockDataFrame as Sdf
import warnings
import os
from tqdm import tqdm
# import matplotlib.pyplot as plt

# Suppress SettingWithCopyWarning
warnings.filterwarnings("ignore")

# util.startLoop()

class IBKRData:
    def __init__(self, time_interval,
                 slow_sma_period,
                 fast_sma_period,
                 first_gap,
                 second_gap,
                 cons_gap,
                 cons_period) -> None:
        self.ib = IB()
        self.ib.connect('127.0.0.1', 7497, clientId=999)
        self.data= pd.DataFrame({})
        self.time_interval = time_interval # 1 M
        self.slow_sma_period = slow_sma_period
        self.fast_sma_period = fast_sma_period
        if first_gap > 0:
            self.first_gap = - first_gap
        else:
            self.first_gap = first_gap
        self.second_gap = second_gap
        self.cons_gap = cons_gap
        self.cons_period = cons_period
    
    def find_pattern(self, df):
        # self.gap_date_list = []
        self.gap_date_list = {}
        ticks = df["tic"].unique().tolist()
        df.index = df["date"]
        for tic in ticks:
            temp_df = df[df["tic"]==tic]
            temp_df = self.find_indicator(temp_df)
            temp_df["gap_per"] = ((temp_df["open"] - temp_df["close"].shift(1)) / temp_df["close"].shift(1)) * 100
            temp_df["gap"] = (temp_df["open"] - temp_df["close"].shift(1))
            downtrend = temp_df["slow_sma"] > temp_df["fast_sma"]
            temp_df["downtrend"] = downtrend
            gap = temp_df[(temp_df["gap_per"] <= self.first_gap) & (temp_df["downtrend"] == True)]
            for idx, row in gap.iterrows():
                if isinstance(idx, str):
                    gap_time = datetime.datetime.strptime(idx, "%Y-%m-%d").date()
                else:
                    gap_time = idx
                    
                gap_idx = temp_df.index.get_loc(gap_time)
                gap_df = temp_df.iloc[gap_idx+1 : gap_idx + self.cons_period]
                
                for i, r in gap_df.iterrows():
                                        
                    if not abs(r["gap_per"]) <= self.cons_gap:
                        if r["gap_per"] > abs(self.second_gap):
                            print(tic)
                            print(f"First Gap: {row['gap']} Gap%: {row['gap_per']} at {idx} Close: {row['close']} Open: {row['open']}")
                            print(f"2nd Gap: {r['gap']} Gap%: {r['gap_per']} at {i} Close: {r['close']} Open: {r['open']}")
                            print("----------------------------------")
                            # self.gap_date_list.append({
                            #     tic: i,
                            #     "rvol": 0
                            # })
                            if tic not in self.gap_date_list.keys():
                                self.gap_date_list[tic] = [[i, row["average_volume"] / row["volume"]]]
                            else:
                                self.gap_date_list[tic].append([i, row["average_volume"] / row["volume"]])
                            # self.gap_date_list["rvol"] = row["volume"]
                            break
                
    
    def historyData(self, tickers, time_interval=None, duration=None):
        """
        durationStr: Time span of all the bars. Examples:
                '60 S', '30 D', '13 W', '6 M', '10 Y'.
        barSizeSetting: Time period of one bar. Must be one of:
            '1 secs', '5 secs', '10 secs' 15 secs', '30 secs',
            '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
            '20 mins', '30 mins',
            '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
            '1 day', '1 week', '1 month'.
        """
        if time_interval is None:
            time_interval = self.time_interval
        if duration is None:
            if self.slow_sma_period >= 30 and self.slow_sma_period <= 365:
                d = round(self.slow_sma_period / 30)
                duration = f"{d} M"
            elif self.slow_sma_period < 30:
                duration= f"{self.slow_sma_period} D"
            elif self.slow_sma_period >= 365:
                d = round(self.slow_sma_period / 365)
                duration = f"{d} Y"
            else:
                raise ValueError("NOt found the correct Time Duration")
                
        df = pd.DataFrame({})
        self.tickers = tickers
        self.action_df = pd.DataFrame([], columns=self.tickers)
        for tic in tqdm(tickers, desc="Fetching Data"):
            contract = self.CreateContract(tic)
            try:
                bars = self.ib.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr=duration,
                    barSizeSetting=time_interval,
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1)
                temp_df = util.df(bars)
                temp_df["tic"] = [tic] * len(temp_df)
                df = pd.concat([df, temp_df], ignore_index=True)
            except:
                continue
        
        self.data = df
        # print(df)
        self.find_pattern(df)
        return df
    
    def find_indicator(self,df=None):
        df.loc[:, "slow_sma"] = df["close"].rolling(window=self.slow_sma_period).mean()
        df.loc[:, "fast_sma"] = df["close"].rolling(window=self.fast_sma_period).mean()
        df["average_volume"] = df['volume'].rolling(window=14).mean()
        return df
        
        
    def find_crossover(self, df=None):
        if df is None:
            df = self.data
        self.golden_cross = {}
        self.death_cross = {}
        self.traded = {}
        for tic in self.tickers:
            temp_df = df[self.data["tic"] == tic]
            temp_df.reset_index(drop=True, inplace=True)
            temp_df = self.find_indicator(temp_df)

            
                    
    def onBarUpdate(self, bars, hasNewBar):
        # print(util.df([bars[-1]]))
        df = util.df([bars[-1]])
        df["tic"] = [bars.contract.symbol]
        # print(bars.contract.symbol)
        # print(df)
        self.data = pd.concat([self.data, df])
        self.data["date"] = self.data["time"]
        self.data["open"] = self.data["open_"]

        self.find_crossover()
        
   
    def LiveData(self, tickers:list, hist_df):
        """
        1 minute: bar_size_in_seconds = 60
        5 minutes: bar_size_in_seconds = 300
        15 minutes: bar_size_in_seconds = 900
        1 hour: bar_size_in_seconds = 3600
        1 day: bar_size_in_seconds = 86400
        """
        self.data = hist_df
        self.tickers = tickers
        for tic in tickers:
            self.cur_tic = tic
            contract = self.CreateContract(tic)
            bars = self.ib.reqRealTimeBars(contract, 60, 'MIDPOINT', False)
            bars.updateEvent += self.onBarUpdate
        
        try:
            self.ib.sleep(100000)
            pass
        except KeyboardInterrupt:
            self.ib.cancelRealTimeBars(bars)
            self.ib.disconnect()
        finally:
            self.ib.cancelRealTimeBars(bars)
            self.ib.disconnect()
                
    def CreateContract(self, ticker):
        contract = Stock(ticker, "SMART", "USD")
        self.ib.qualifyContracts(contract)
        return contract

    def disconnect(self):
        self.ib.disconnect()
def create_folder(folder_name):
    if not os.path.exists("./" + folder_name):
        os.makedirs("./" + folder_name)

if __name__=="__main__":
    from config import *
    folder_name = "Strategy_Directory"
    create_folder(folder_name)
    tickers_df =pd.read_csv("./stocks.csv")
    tickers = tickers_df["name"].to_list()
    
    hist_df = pd.DataFrame({})
    ib_obj = IBKRData(
        time_interval=time_interval,
        slow_sma_period=slow_sma,
        fast_sma_period=fast_sma,
        first_gap = first_gap_per,
        second_gap = second_gap_per,
        cons_gap = cons_gap_per,
        cons_period = cons_period
        
    )
    try:
        hist_df = ib_obj.historyData(tickers, time_interval=time_interval, duration=duration)
               
    except KeyboardInterrupt:
        ib_obj.disconnect()
    finally:
        ib_obj.disconnect()
    ib_obj.disconnect()
    
    gaps = ib_obj.gap_date_list
    data = []
    for tic, values in gaps.items():
        
        for i in range(len(values)):
            values[i].append(tic)
            data.append(values[i])

    df = pd.DataFrame(data)
    
    df.columns=["date", "rvol", "tic"]
    df.to_csv(f"./{folder_name}/pattern.csv", index=False)
    hist_df.to_csv(f"./{folder_name}/stock_OHLC.csv", index=False)
    