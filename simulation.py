import pandas as pd
from stockstats import StockDataFrame as Sdf
from copy import deepcopy
from ib_insync import *
from config import stop_loss_atr, next_stop_loss_atr, baseline_slow_sma, baseline_fast_sma, baseline_duration, baseline_index, Cash, can_trade_upto
import numpy as np
import pandas as pd
from stockstats import StockDataFrame as Sdf
import quantstats as qs
from utilFunction import fetchHistoricalData
from tqdm import tqdm
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def downloadBaselineData():
    spx = fetchHistoricalData([baseline_index], index=True, duration=baseline_duration)
    spx = Sdf.retype(spx)
    spx["SMA_fast"] = spx[f"close_{baseline_fast_sma}_sma"] 
    spx["SMA_slow"] = spx[f"close_{baseline_slow_sma}_sma"]
    spx['bullish'] = spx['SMA_fast'] > spx['SMA_slow']
    spx.index = spx.index.map(lambda x: x.strftime('%Y-%m-%d'))
    return spx

class Simulation:
    def __init__(self, df_cwd) -> None:
        self.df = pd.read_csv(df_cwd)
        self.day = 0
        self.ticker_list = self.df["tic"].unique().tolist()
        self.data = self.df.loc[self.day, :]
        self.trade = {}
        self.completedTrade = {}
        self.asset_memory = []
        self.date_memory = []
        self.initial_amount = Cash
        self.max_allocate_amount = self.initial_amount / can_trade_upto
        self.brokerage_charge = 1
        self.running_ticker = []
        self.long_price = []
        self.long_date = []
        self.amount_allocated = []
        self.num_shares = []
        self.state = []
        self.stop_loss_atr = stop_loss_atr
        self.next_stop_loss_atr = next_stop_loss_atr
        
        
    def convert2Sdf(self):
        a = pd.DataFrame({})
        for tic in self.ticker_list:
            b = self.df[self.df["tic"]==tic]
            b = Sdf.retype(b)
            b["atr"] = b["atr_14"]
            a = pd.concat([a,b])
        a["date"] = a.index
        a.reset_index(drop=True, inplace=True)
        a.index = a["date"].factorize()[0]
        a.sort_values(by=["date","tic"])
        self.df = a.copy()
        
    
    def managePortfolio(self):
        pass
    
    def manageTrade(self):
        pass
    
    def manageCompletedTrade(self):
        pass
    
    def __update_state(self):
        pass
    
    def step(self, patterns:list):
        self.data = self.df.loc[self.day, :]
        curr_date = self.data["date"].unique()[0]
        end_total_assets = self.initial_amount
        for pattern in tqdm(patterns, desc="Analyzing Data"):
            try:
                pattern_df = self.data[self.data["tic"] == pattern].iloc[0]
            except:
                break
            close = pattern_df["close"]
            low = pattern_df["low"]
            date = pattern_df["date"]
            atr = pattern_df["atr"] 
            if len(self.trade) < can_trade_upto and pattern not in self.trade: #spx.loc[date]["bullish"] and 
                if self.max_allocate_amount <= self.initial_amount:
                    # place long order
                    amount = self.max_allocate_amount
                    qty = ((amount - self.brokerage_charge) // close)
                    cost = close * qty + self.brokerage_charge
                    self.trade[pattern] = {
                        "amount" : amount,
                        "entry_date": date,
                        "entry_price": close,
                        "current_price": close,
                        "qty": qty,
                        "stop_loss": close - atr * self.stop_loss_atr,
                        "next_stop_loss": close + atr * self.next_stop_loss_atr,
                        "pl": 0
                    }
                    self.initial_amount -= cost
                    self.running_ticker.append(pattern)
        
        # simulation
        end_total_assets = self.initial_amount
        temp_running_ticker = self.running_ticker.copy()
        for rt in self.running_ticker:
            rt_df = self.data[self.data["tic"] == rt].iloc[0]
            close = rt_df["close"]
            low = rt_df["low"]
            atr = rt_df["atr"]
            date = rt_df['date']
            rt_stop_loss = self.trade[rt]["stop_loss"]
            rt_next_stop_loss = self.trade[rt]["next_stop_loss"]
            shares = self.trade[rt]["qty"]
            if close <= rt_stop_loss:                
                pl = (close * shares) - (shares * self.trade[rt]["entry_price"])
                amount_left = close * shares
                if rt in self.completedTrade.keys():
                    self.completedTrade[rt].append({
                        "amount": self.trade[rt]["amount"],
                        "price": self.trade[rt]["entry_price"],
                        "shares": self.trade[rt]["qty"],
                        "stop_loss": rt_stop_loss,
                        "next_stop_loss": rt_next_stop_loss,
                        "pl": pl,
                        "entry_date": self.trade[rt]["entry_date"],
                        "exit_date": date,
                        "exit price": close,
                    })
                else:
                    self.completedTrade[rt] = [{
                        "amount": self.trade[rt]["amount"],
                        "price": self.trade[rt]["entry_price"],
                        "shares": self.trade[rt]["qty"],
                        "stop_loss": rt_stop_loss,
                        "next_stop_loss": rt_next_stop_loss,
                        "pl": pl,
                        "entry_date": self.trade[rt]["entry_date"],
                        "exit_date": date,
                        "exit price": close,
                    }]
                del self.trade[rt]
                self.initial_amount += amount_left
                # end_total_assets += close * shares
                # self.running_ticker.remove(rt)
                temp_running_ticker.remove(rt)
            elif close >= rt_next_stop_loss:
                self.trade[rt]["stop_loss"] = close - atr * self.stop_loss_atr
                self.trade[rt]["next_stop_loss"] = close + atr * self.next_stop_loss_atr
                print(f" next stoploss hit at {date} #{rt} Close: {close} stop loss: {rt_stop_loss} next stoploss: {rt_next_stop_loss}")
            else:
                pl = (close * shares) - (shares * self.trade[rt]["entry_price"])
                self.trade[rt]["pl"] = pl
                self.trade[rt]["current_price"] = close
            
            end_total_assets += close * shares
        self.running_ticker = temp_running_ticker.copy()
        # calculate portfolio value 
        self.date_memory.append(curr_date)
        self.asset_memory.append(end_total_assets)
        
        self.day += 1

def create_folder(parent, folder_name):
    directory = os.path.join(parent, folder_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
def find_profitFactor(folder):
    
    completed_trade = pd.read_csv(f"./{folder}/simulation_result/completed_trade.csv")
    ongoing_trade = pd.read_csv(f"./{folder}/simulation_result/onGoing_trade.csv")
    try:
        trade1 = ongoing_trade["pl"].values
    except:
        trade1 = np.array([])
    try:
        trade2 = completed_trade["pl"].values
    except:
        trade2 = np.array([])

    pl = np.concatenate((trade1, trade2))

    gross_profit = np.sum(pl[pl > 0])
    gross_loss = np.sum(pl[pl < 0])
    gross_factor = gross_profit / abs(gross_loss)
    with open(f"./{folder}/simulation_result/profit_factor.txt", "w") as file:
        file.write(f"Profit factor: {gross_factor}")


def get_daily_return(df, value_col_name="account_value"):
    df = deepcopy(df)
    df["daily_return"] = df[value_col_name].pct_change(1)
    df["date"] = pd.to_datetime(df.index)
    df.set_index("date", inplace=True, drop=True)
    df.index = df.index.tz_localize("UTC")
    return pd.Series(df["daily_return"], index=df.index)



if __name__ == "__main__":
    from config import folder_name
    create_folder(folder_name, "simulation_result")
    a = Simulation(df_cwd=f"./{folder_name}/stock_OHLC.csv")
    pattern = pd.read_csv(f"./{folder_name}/pattern.csv")

    a.convert2Sdf()
    for i in range(max(a.df.index)):
        date = a.df.loc[i, "date"].unique()[0]
        # is_pattern = pattern[pattern["date"]== date]
        is_pattern = pattern[(pattern["date"] == date)]# & (pattern["rvol"] >= 0.5)]
        if is_pattern.empty:
            a.step([])
        else:
            top4ticker = is_pattern.sort_values(by=["rvol"], ascending=False).head(can_trade_upto)
            top4ticker["tic"].values.tolist()
            a.step(top4ticker["tic"].values.tolist())
    print("Analyze Completed.. wait for Result Save...")
    amount_value = pd.DataFrame({'asset_memory': a.asset_memory, 'date_memory': a.date_memory})
    
    completed_trade_data = []

    for ticker, trades in a.completedTrade.items():
        for trade in trades:
            completed_trade_data.append({'ticker': ticker,
                                        'amount': trade['amount'],
                                        'price': trade['price'],
                                        'shares': trade['shares'],
                                        'stop_loss': trade['stop_loss'],
                                        'next_stop_loss': trade['next_stop_loss'],
                                        'pl': trade['pl'],
                                        'entry_date': trade['entry_date'],
                                        'exit_date': trade['exit_date'],
                                        'exit_price': trade['exit price']})

    completed_trade = pd.DataFrame(completed_trade_data)
    completed_trade.to_csv(f"./{folder_name}/simulation_result/completed_trade.csv")
    
    ongoing_trade = pd.DataFrame.from_dict(a.trade, orient='index')
    ongoing_trade.to_csv(f"./{folder_name}/simulation_result/onGoing_trade.csv")
    spx = downloadBaselineData()
    
    baseline_return = get_daily_return(spx, "close")
    portfolio_df = amount_value.copy()
    portfolio_df['date_memory'] = pd.to_datetime(portfolio_df['date_memory'])
    portfolio_df.set_index('date_memory', inplace=True)

    portfolio_df['returns'] = portfolio_df['asset_memory'].pct_change().fillna(0)
    stretagy_returns = portfolio_df["returns"]
    baseline_return = get_daily_return(spx, "close")
    if stretagy_returns.index.tz:
        stretagy_returns.index = stretagy_returns.index.tz_convert(None)
        pass
    if baseline_return.index.tz:
        baseline_return.index = baseline_return.index.tz_convert(None)
        pass
    qs.reports.html(portfolio_df['returns'],baseline_return, output=f'./{folder_name}/simulation_result/my_portfolio_analysis.html')
