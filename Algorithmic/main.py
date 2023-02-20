#import tradeapp module 
from tradeapp.tradeapp import TradingApp, LOG_COLORS
from utils import enoughLiquidty, optimalPrice
import matplotlib.pyplot as plt
import numpy as np
import time
import multiprocessing as mp
import logging
import timeit

# access the logger defined in the TradingApp class
logger = TradingApp.logger
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)

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
        else:
            s_d["latest_tenders"].clear()

        

        #print(s_d["tickers_bid"][-1])
        if s_d["streaming_started"].value == False:
            time.sleep(1)
        #always use the .value attribute when accessing shared single value (mp.Value)
        s_d["streaming_started"].value = True


############### Main function ################

def main(app : TradingApp, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    #while True is a loop that will run forever (CTRL+C to stop it)
    arb_type = -1
    ARB_COMMISSION = 0.12
    ARB_SLIPPAGE = 0.1
    ARB_SLACK = ARB_COMMISSION + ARB_SLIPPAGE
    arb_open = False
    while True:

        if s_d["streaming_started"].value:
            time.sleep(0.1)
            # tick = app.currentTick()
            # if tick != None:
            #     print(str(tick).zfill(3), end="\r")

            #print(s_d["tickers_ask"][:])

            RITC_bid = s_d["tickers_bid"][s_d["tickers_name"].index("RITC")]
            RITC_ask = s_d["tickers_ask"][s_d["tickers_name"].index("RITC")]

            BULL_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BULL")]
            BULL_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BULL")]

            BEAR_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")]
            BEAR_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")]

            USD_ask = s_d["tickers_ask"][s_d["tickers_name"].index("USD")]
            USD_bid = s_d["tickers_bid"][s_d["tickers_name"].index("USD")]

            # all([pos == 0 for pos in s_d["tickers_pos"][:]]) and 
            if (BULL_ask + BEAR_ask)/USD_ask < RITC_bid - ARB_SLACK and arb_open == False:
                # take position
                app.postOrder("SELL", "RITC", 10)
                app.postOrder("BUY", "BULL", 10)
                app.postOrder("BUY", "BEAR", 10)
                arb_open = True
                arb_type = 0

            elif ((BULL_bid + BEAR_bid)/USD_bid > (RITC_ask + ARB_SLACK)) and arb_open == False:
                # take position
                app.postOrder("BUY", "RITC", 10)
                app.postOrder("SELL", "BULL", 10)
                app.postOrder("SELL", "BEAR", 10)
                arb_type = 1
                arb_open = True

            
            if arb_open == True and arb_type == 0:
                if ((BULL_bid + BEAR_bid)/USD_bid > RITC_ask):
                    # unwind position
                    app.postOrder("BUY", "RITC", 10)
                    app.postOrder("SELL", "BULL", 10)
                    app.postOrder("SELL", "BEAR", 10)
                    arb_open = False
                    time.sleep(0.5)

            
            elif arb_open == True and arb_type == 1:
                if ((BULL_ask + BEAR_ask)/USD_ask < RITC_bid):
                    # unwind position 
                    app.postOrder("SELL", "RITC", 10)
                    app.postOrder("BUY", "BULL", 10)
                    app.postOrder("BUY", "BEAR", 10)
                    arb_open = False
                    time.sleep(0.5)



            # latest_tenders = dict(s_d["latest_tenders"])
            # if latest_tenders != {} and s_d["unwinding"].value == False:
            #     id = list(latest_tenders.keys())[0]
            #     ticker = latest_tenders[id]["ticker"]
            #     #direction can take the values "BUY" or "SELL"
            #     direction = latest_tenders[id]["action"]
            #     price = latest_tenders[id]["price"]
            #     quantity = latest_tenders[id]["quantity"]
            #     seconds_till_expiration =  latest_tenders[id]["expires"] - tick

            #     if direction == "BUY":
            #         direction_to_unwind = "SELL"
            #     else:
            #         direction_to_unwind = "BUY"
            #     #verify that the price is appropriate and that there is a market to sell to or buy from
            #     bidask = app.getSecuritiesBook(ticker)
                
            #     liquidty_cond = enoughLiquidty(bidask, 0.5, price, quantity, direction_to_unwind)
            #     #optimalPrice(bidask, quantity, direction_to_unwind)
            #     #send the order
            #     if liquidty_cond:
            #         id = list(latest_tenders.keys())[0]
            #         response = app.postTender(id, "ACCEPT")
            #         print(response)

            #         # verifiy if the order was accepted
            #         if response == 200:
            #             # if it was accepted, then we need to unwind the position
            #             total_order_qty = np.ceil(quantity/10000)
            #             if direction_to_unwind == "SELL":
            #                 tiers = [1 for i in range(1, int(total_order_qty))]
            #             else:
            #                 tiers = [1 for i in range(1, int(total_order_qty))]
            #             remaining_qty = quantity
            #             while remaining_qty != 0:

            #                 quantity = min(remaining_qty, 10000)
            #                 price = (RITC_bid+RITC_ask)/2
            #                 price = price if direction_to_unwind == "SELL" else price

            #                 g = app.postOrder(direction_to_unwind, ticker, quantity, type="MARKET")
            #                 remaining_qty -= quantity  

                    



                    
                






if __name__ == "__main__":
    app = MyTradingApp("9999", "0CEN4JP9")
    
    def TESTgetSecuritiesBook():
        book = app.getSecuritiesBook("RITC", 10, False)
        book = np.array([[float(book["bids"][i]["price"]), int(book["bids"][i]["quantity"])] for i in range(len(book["bids"]))])
        print(book)
        return None
    def TEST1getSecuritiesBook():
        book = app.getSecuritiesBook("RITC", 10, True)
        return None
    print(timeit.timeit(TESTgetSecuritiesBook, number=2))
    print(timeit.timeit(TEST1getSecuritiesBook, number=2))

    exit()
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
    unwinding = mp.Value('b', False)

    qty_filled = mp.Array('i', len(tickers_name_))

    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "tickers_pos": tickers_pos,
                    "tickers_fee": tickers_fee,
                    "latest_tenders": latest_tenders,
                    "arb_open": arb_open,
                    "unwinding": unwinding,
                    "qty_filled": qty_filled,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




