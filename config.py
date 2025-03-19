first_gap_per = 5
second_gap_per = 5
cons_gap_per = 2
cons_period = 22
stop_loss_atr = 2
next_stop_loss_atr = 1
slow_sma = 20
fast_sma = 10

duration = '1 Y' # Supported " '30 D', '13 W', '6 M', '10 Y'"

####### account details###############
Cash = 2000
can_trade_upto = 5 # hold maximum 4 tickers at same time 
max_allocation = Cash / can_trade_upto 
######################

# baseline config 

use_baseline = False
baseline_index = 'SPX'
baseline_slow_sma = 100
baseline_fast_sma = 20
baseline_duration = '3 Y' # suggested to use 1 year extra data 
# recommend to not change without consulting it might produce an error

time_interval = '1 day'
folder_name = 'Strategy_Directory'

# IBKR connect
ib_config = {'port': 7400, 'ip': '127.0.0.1', 'clientId': 999}

# License Key
license_key = "92TRXH8Q"

