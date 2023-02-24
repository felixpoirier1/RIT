#import tradeapp module 
from tradeapp.tradeapp import TradingApp, LOG_COLORS
# for raw arbitrages
from utils import createSyntheticETF, findOptimalArbitrageQty
# for tenders
from utils import isProfitable
import matplotlib.pyplot as plt
import numpy as np
import time
import multiprocessing as mp
import logging
import timeit
from sklearn.linear_model import LinearRegression

# access the logger defined in the TradingApp class
logger = TradingApp.logger
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Define custom formatter with color codes
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level_color = LOG_COLORS.get(record.levelno, '')
        reset_color = '\033[0m'
        message = super().format(record)
        return level_color + message + reset_color

# create formatter
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# My own trading app class
class MyTradingApp(TradingApp):
    class_name = "MyTradingApp"
    def __init__(self, host, API_KEY):
        super().__init__(host, API_KEY)
        
##### General variables to share between processes #####
streaming_started = mp.Value('b', False)

lock = mp.Lock()


############## Streaming function #############

def streamPrice(app : TradingApp, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    while True:
        tick = app.currentTick()
        s_d["tick"].value = tick
        
        time.sleep(0.05)
        #examples for modifying shared data stored in arrays
        securities = app.getSecurities()
        lock.acquire()
        for index, ticker in enumerate(s_d["tickers_name"][:]):
            s_d["tickers_ask"][index] = securities[ticker]["ask"]
            s_d["tickers_bid"][index] = securities[ticker]["bid"]
            s_d["tickers_pos"][index] = securities[ticker]["position"]
        lock.release()
        
        if tick % 2 == 0:
            time.sleep(0.1)
            latest_tenders = app.getTenders()
            print(latest_tenders)
            lock.acquire()
            if latest_tenders != None:
                s_d["latest_tenders"].update(latest_tenders)
                with open("tenders.txt", "a") as f:
                    f.write(str(latest_tenders))
            else:
                s_d["latest_tenders"].clear()
            lock.release()

        

        #print(s_d["tickers_bid"][-1])
        if s_d["streaming_started"].value == False:
            time.sleep(0.5)
        #always use the .value attribute when accessing shared single value (mp.Value)
        s_d["streaming_started"].value = True


############### Main function ################

def main(app : TradingApp, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    #while True is a loop that will run forever (CTRL+C to stop it)
    arb_type = -1
    ARB_COMMISSION = 0.12
    ARB_SLIPPAGE = 0.02
    arb_qty_realized = 0
    ARB_SLACK = ARB_COMMISSION + ARB_SLIPPAGE
    arb_open = False
    last_arb_tick = 0
    time_till_double_down = 0
    time_till_double_down = 2
    swing_difference = 0.05

    while True:
        if s_d["streaming_started"].value:

            
            tick = s_d["tick"].value
            if tick != None:
                print(str(tick).zfill(3), end="\r")

            # tender arbitrage logic
            try:
                latest_tenders = dict(s_d["latest_tenders"])
            except:
                # to prevent the error of reading a tender while it is being updated
                latest_tenders = {}
            if latest_tenders != {}:
                id = list(latest_tenders.keys())[0]
                price = latest_tenders[id]["price"]
                qty = latest_tenders[id]["quantity"]
                action = latest_tenders[id]["action"]

                if action == "BUY":
                    direction = "bids"
                    action_to_close = "SELL"
                elif action == "SELL":
                    direction = "asks"
                    action_to_close = "BUY"
                
                RITC_book = app.getSecuritiesBook("RITC", df = False)
                # ignore the first two orders because they are the market maker orders and likely to be before accepting the tender
                RITC_book = np.array([[int(RITC_book[direction][i]["quantity"] - RITC_book[direction][i]["quantity_filled"]), float(RITC_book[direction][i]["price"])] for i in range(len(RITC_book[direction]))])

                if isProfitable(price, RITC_book, direction[:-1], qty):
                    #tender_id = app.postTender(id)
                    print("Tender is profitable")
                else:
                    print("Tender is not profitable")

                    
                






if __name__ == "__main__":
    app = MyTradingApp("9999", "0CEN4JP9")
    # shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.

    # retrieves the list of tickers and stores it in a shared lis
    
    securities_info = app.getSecurities()
    tickers_name_ = list(securities_info.keys())
    tickers_name = [mp.Array('c', 1) for i in range(len(tickers_name_))]
    tickers_name[:] = list(securities_info.keys())

    tickers_bid = mp.Array('f', len(tickers_name_))
    tickers_ask = mp.Array('f', len(tickers_name_)) 
    tickers_pos = mp.Array('f', len(tickers_name_))

    latest_tenders = {}
    mgr = mp.Manager()
    latest_tenders = mgr.dict()
    latest_tenders.update(latest_tenders)

    tick = mp.Value('i', 0)

    qty_filled = mp.Array('i', len(tickers_name_))

    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "tickers_pos": tickers_pos,
                    "latest_tenders": latest_tenders,
                    "qty_filled": qty_filled,
                    "tick": tick,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()

    # marketmakingthread = mp.Process(target=marketmaking, args=(app,), kwargs = shared_data)
    # marketmakingthread.start()


    main(app, **shared_data)




