#import tradeapp module 
from tradeapp.tradeapp import TradingApp, LOG_COLORS

import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging

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
        time.sleep(0.1)
        #examples for modifying shared data stored in arrays
        securities = app.getSecurities()
        for index, ticker in enumerate(s_d["tickers_name"][:]):
            s_d["tickers_ask"][index] = securities[ticker]["ask"]
            s_d["tickers_bid"][index] = securities[ticker]["bid"]
            s_d["tickers_pos"][index] = securities[ticker]["position"]
        
        time.sleep(0.1)
        latest_tenders = app.getTenders()
        if latest_tenders != None:
            s_d["latest_tenders"].update(latest_tenders)
        

        #print(s_d["tickers_bid"][-1])
        if s_d["streaming_started"].value == False:
            time.sleep(2)
        #always use the .value attribute when accessing shared single value (mp.Value)
        s_d["streaming_started"].value = True


############### Main function ################

def main(app : TradingApp, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    #while True is a loop that will run forever (CTRL+C to stop it)
    while True:

        if s_d["streaming_started"].value:
            time.sleep(0.1)

            #print(s_d["tickers_ask"][:])

            RITC_bid = s_d["tickers_bid"][s_d["tickers_name"].index("RITC")]
            RITC_ask = s_d["tickers_ask"][s_d["tickers_name"].index("RITC")]

            BULL_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BULL")]
            BULL_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BULL")]

            BEAR_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")]
            BEAR_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")]

            USD_ask = s_d["tickers_ask"][s_d["tickers_name"].index("USD")]
            USD_bid = s_d["tickers_bid"][s_d["tickers_name"].index("USD")]
            print(app.currentTick())
            # ARB_BOUND = 0.01
            # if all([pos == 0 for pos in s_d["tickers_pos"][:]]) and s_d["arb_open"].value == False:
            #     print((BULL_ask + BEAR_ask)/USD_ask, RITC_bid)
            #     if (BULL_ask + BEAR_ask)/USD_ask < RITC_bid*(1-ARB_BOUND):
            #         # take position
            #         app.postOrder("SELL", "RITC", 100)
            #         app.postOrder("BUY", "BULL", 100)
            #         app.postOrder("BUY", "BEAR", 100)

            #         s_d["arb_open"] = True
            #         # cover position with limit
            #         # app.postOrder("BUY", "RITC", 100, price = (BULL_ask + BEAR_ask)/USD_ask, type="LIMIT")
            #         # app.postOrder("SELL", "BULL", 100, price = RITC_bid*USD_ask - BEAR_ask, type="LIMIT")
            #         # app.postOrder("SELL", "BEAR", 100, price = RITC_bid*USD_ask - BULL_ask, type="LIMIT")

            #     elif (BULL_bid + BEAR_bid)/USD_bid > RITC_ask*(1+ARB_BOUND):
            #         # take position
            #         app.postOrder("BUY", "RITC", 100)
            #         app.postOrder("SELL", "BULL", 100)
            #         app.postOrder("SELL", "BEAR", 100)
                    
            #         s_d["arb_open"] = True
            #         # cover position with limit
            #         # app.postOrder("SELL", "RITC", 100, price = (BULL_bid + BEAR_bid)/USD_bid, type="LIMIT")
            #         # app.postOrder("BUY", "BULL", 100, price = RITC_ask*USD_bid - BEAR_bid, type="LIMIT")
            #         # app.postOrder("BUY", "BEAR", 100, price = RITC_ask*USD_bid - BULL_bid, type="LIMIT")


            #     time.sleep(0.2)
            
            # elif any([pos != 0 for pos in s_d["tickers_pos"][:]]) and s_d["arb_open"] == True:
            #     print("..")
            #     if ((BULL_ask + BEAR_ask)/USD_ask > RITC_bid) or ((BULL_bid + BEAR_bid)/USD_bid < RITC_ask):
            #         for index, pos in enumerate(s_d["tickers_pos"][:]):
            #             if pos != 0:
            #                 app.postOrder("SELL" if pos > 0 else "BUY", s_d["tickers_name"][index], abs(pos))
                    
            #         s_d["arb_open"] = False
            latest_tenders = dict(s_d["latest_tenders"])
            if latest_tenders != {}:
                response = app.postTender(list(latest_tenders.keys())[0])
                s_d["latest_tenders"].popitem()
                if response == 200:


                    
                






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

    tickers_fee = mp.Array('f', len(tickers_name_))
    tickers_fee[:] = [securities_info[ticker]["trading_fee"] for ticker in tickers_name_]

    latest_tenders = {}
    mgr = mp.Manager()
    latest_tenders = mgr.dict()
    latest_tenders.update(latest_tenders)

    arb_open = mp.Value('b', False)

    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "tickers_pos": tickers_pos,
                    "tickers_fee": tickers_fee,
                    "latest_tenders": latest_tenders,
                    "arb_open": arb_open,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




