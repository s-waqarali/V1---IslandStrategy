from ib_insync import *
import pandas as pd
import os

def create_folder(folder_name):
    if not os.path.exists("./" + folder_name):
        os.makedirs("./" + folder_name)

def CreateContract(tic, ib):
    contract = Stock(tic, "SMART","USD")
    ib.qualifyContracts(contract)
    return contract

def CreateContractIndex(tic, ib):
    # contract = Index(tic, "SMART", "USD")
    contract = Index(symbol=tic, exchange='CBOE')
    # contract = Index(tic)
    ib.qualifyContracts(contract)
    return contract

def connect2IB(host="127.0.0.1", port=7497, clientId=999):
    ib = IB()
    ib.connect(host, port, clientId)
    
    return ib

def fetchHistoricalData(ticker, duration="2 M", time_interval="1 day", index=False):
    ib = connect2IB()
    df = pd.DataFrame({})
    for tic in ticker:
        try:
            if index:
                contract = CreateContractIndex(tic, ib)
            else:
                contract = CreateContract(tic, ib)
            bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=time_interval,
                whatToShow='TRADES',
                useRTH=False,
                formatDate=1)
            temp_df = util.df(bars)
            temp_df["tic"] = [tic] * len(temp_df)
            df = pd.concat([df, temp_df], ignore_index=True)
        except:
            ib.disconnect()
    ib.disconnect()
    return df