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
            time.sleep(1)
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
    print("="*50)

    while True:
        if s_d["streaming_started"].value:

            
            tick = s_d["tick"].value
            if tick != None:
                print(str(tick).zfill(3), end="\r")
            
            # raw arbitrage
            if ((s_d["tickers_ask"][s_d["tickers_name"].index("BULL")] + s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")])/s_d["tickers_ask"][s_d["tickers_name"].index("USD")] < (s_d["tickers_bid"][s_d["tickers_name"].index("RITC")] - ARB_SLACK)) and \
                ((arb_type == -1) or (arb_type == 0)) and \
                (tick >= last_arb_tick + time_till_double_down) and \
                (abs(s_d["tickers_pos"][s_d["tickers_name"].index("BEAR")])*s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")] + abs(s_d["tickers_pos"][s_d["tickers_name"].index("BULL")])*s_d["tickers_ask"][s_d["tickers_name"].index("BULL")] + abs(s_d["tickers_pos"][s_d["tickers_name"].index("RITC")])*s_d["tickers_bid"][s_d["tickers_name"].index("RITC")] < 250000):
                
                # find the optimal quantity to arbitrage
                BULL_book = app.getSecuritiesBook("BULL", 10, False)
                BULL_book = np.array([[float(BULL_book["asks"][i]["price"]/s_d["tickers_ask"][s_d["tickers_name"].index("USD")]), int(BULL_book["asks"][i]["quantity"] - BULL_book["asks"][i]["quantity_filled"])] for i in range(len(BULL_book["asks"]))])

                BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                BEAR_book = np.array([[float(BEAR_book["asks"][i]["price"]/s_d["tickers_ask"][s_d["tickers_name"].index("USD")]), int(BEAR_book["asks"][i]["quantity"] - BEAR_book["asks"][i]["quantity_filled"])] for i in range(len(BEAR_book["asks"]))])

                RITC_book = app.getSecuritiesBook("RITC", 10, False)
                RITC_book = np.array([[int(RITC_book["bids"][i]["quantity"] - RITC_book["bids"][i]["quantity_filled"]), float(RITC_book["bids"][i]["price"]),] for i in range(len(RITC_book["bids"]))])
                synthbook = createSyntheticETF({"BULL":BULL_book, "BEAR":BEAR_book})

                arb_quantity = min(findOptimalArbitrageQty(RITC_book, synthbook, ARB_SLACK), 10000)


                if arb_quantity == 0:
                    time.sleep(0.01)
                    continue

                else:
                    # take position
                    app.postOrder("SELL", "RITC", arb_quantity)
                    app.postOrder("BUY", "BULL", arb_quantity)
                    app.postOrder("BUY", "BEAR", arb_quantity)
                    arb_qty_realized += arb_quantity
                    last_arb_tick = tick
                    arb_open = True
                    arb_type = 0

            elif ((s_d["tickers_bid"][s_d["tickers_name"].index("BULL")] + s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")])/s_d["tickers_bid"][s_d["tickers_name"].index("USD")] > (s_d["tickers_ask"][s_d["tickers_name"].index("RITC")] + ARB_SLACK)) and \
                ((arb_type == -1) or (arb_type == 1))  and \
                (tick >= last_arb_tick + time_till_double_down) and (abs(s_d["tickers_pos"][s_d["tickers_name"].index("BEAR")])*s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")] + abs(s_d["tickers_pos"][s_d["tickers_name"].index("BULL")])*s_d["tickers_bid"][s_d["tickers_name"].index("BULL")] + abs(s_d["tickers_pos"][s_d["tickers_name"].index("RITC")])*s_d["tickers_ask"][s_d["tickers_name"].index("RITC")] < 250000):
                
                # find the optimal quantity to arbitrage
                BULL_book = app.getSecuritiesBook("BULL", 10, False)
                BULL_book = np.array([[float(BULL_book["bids"][i]["price"]/s_d["tickers_bid"][s_d["tickers_name"].index("USD")]), int(BULL_book["bids"][i]["quantity"] - BULL_book["bids"][i]["quantity_filled"])] for i in range(len(BULL_book["bids"]))])

                BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                BEAR_book = np.array([[float(BEAR_book["bids"][i]["price"]/s_d["tickers_bid"][s_d["tickers_name"].index("USD")]), int(BEAR_book["bids"][i]["quantity"] - BEAR_book["bids"][i]["quantity_filled"])] for i in range(len(BEAR_book["bids"]))])

                RITC_book = app.getSecuritiesBook("RITC", 10, False)
                RITC_book = np.array([[int(RITC_book["asks"][i]["quantity"] - RITC_book["asks"][i]["quantity_filled"]), float(RITC_book["asks"][i]["price"])] for i in range(len(RITC_book["asks"]))])

                synthbook = createSyntheticETF({"BULL":BULL_book, "BEAR":BEAR_book})

                arb_quantity = min(findOptimalArbitrageQty(synthbook, RITC_book, ARB_SLACK), 10000)

                if arb_quantity == 0:
                    time.sleep(0.01)
                    continue
                
                else:
                    # take position
                    app.postOrder("BUY", "RITC", arb_quantity)
                    app.postOrder("SELL", "BULL", arb_quantity)
                    app.postOrder("SELL", "BEAR", arb_quantity)
                    arb_qty_realized += arb_quantity
                    last_arb_tick = tick
                    arb_type = 1
                    arb_open = True

            if arb_open == True and arb_type == 0:
                if ((s_d["tickers_bid"][s_d["tickers_name"].index("BULL")] + s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")])/s_d["tickers_bid"][s_d["tickers_name"].index("USD")] > s_d["tickers_ask"][s_d["tickers_name"].index("RITC")] + swing_difference):
                    print("-"*50)
                    print(arb_qty_realized)
                    # unwind position
                    while arb_qty_realized > 0:
                        BULL_book = app.getSecuritiesBook("BULL", 10, False)
                        BULL_book = np.array([[float(BULL_book["bids"][i]["price"]/s_d["tickers_bid"][s_d["tickers_name"].index("USD")]), int(BULL_book["bids"][i]["quantity"] - BULL_book["bids"][i]["quantity_filled"])] for i in range(len(BULL_book["bids"]))])

                        BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                        BEAR_book = np.array([[float(BEAR_book["bids"][i]["price"]/s_d["tickers_bid"][s_d["tickers_name"].index("USD")]), int(BEAR_book["bids"][i]["quantity"] - BEAR_book["bids"][i]["quantity_filled"])] for i in range(len(BEAR_book["bids"]))])

                        RITC_book = app.getSecuritiesBook("RITC", 10, False)
                        RITC_book = np.array([[int(RITC_book["asks"][i]["quantity"] - RITC_book["asks"][i]["quantity_filled"]), float(RITC_book["asks"][i]["price"])] for i in range(len(RITC_book["asks"]))])

                        synthbook = createSyntheticETF({"BULL":BULL_book, "BEAR":BEAR_book})

                        qty_to_sell = min(findOptimalArbitrageQty(synthbook, RITC_book, -0.05), 10000)

                        if qty_to_sell != 0:
                            qty_to_sell = min(arb_qty_realized, 10000)
                            app.postOrder("BUY", "RITC", qty_to_sell)
                            app.postOrder("SELL", "BULL", qty_to_sell)
                            app.postOrder("SELL", "BEAR", qty_to_sell)
                            arb_qty_realized -= qty_to_sell
                            time.sleep(0.1)
                        else:
                            pass
                        time.sleep(0.1)
                    swing_difference = 0.05
                    print("="*50)
                
                    arb_open = False
                    arb_qty_realized = 0
                    arb_type = -1

            
            elif arb_open == True and arb_type == 1:
                if ((s_d["tickers_ask"][s_d["tickers_name"].index("BULL")] + s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")])/s_d["tickers_ask"][s_d["tickers_name"].index("USD")] < s_d["tickers_bid"][s_d["tickers_name"].index("RITC")] - swing_difference):
                    print("-"*50)
                    print(arb_qty_realized)
                    # unwind position 
                    while arb_qty_realized > 0:
                        BULL_book = app.getSecuritiesBook("BULL", 10, False)
                        BULL_book = np.array([[float(BULL_book["bids"][i]["price"]/s_d["tickers_ask"][s_d["tickers_name"].index("USD")]), int(BULL_book["bids"][i]["quantity"] - BULL_book["bids"][i]["quantity_filled"])] for i in range(len(BULL_book["asks"]))])

                        BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                        BEAR_book = np.array([[float(BEAR_book["bids"][i]["price"]/s_d["tickers_ask"][s_d["tickers_name"].index("USD")]), int(BEAR_book["bids"][i]["quantity"] - BEAR_book["bids"][i]["quantity_filled"])] for i in range(len(BEAR_book["asks"]))])

                        RITC_book = app.getSecuritiesBook("RITC", 10, False)
                        RITC_book = np.array([[int(RITC_book["asks"][i]["quantity"] - RITC_book["asks"][i]["quantity_filled"]), float(RITC_book["asks"][i]["price"])] for i in range(len(RITC_book["bids"]))])

                        qty_to_sell = min(findOptimalArbitrageQty(RITC_book, synthbook, -0.05), 10000)

                        if qty_to_sell != 0:
                            qty_to_sell = min(arb_qty_realized, 10000)
                            app.postOrder("SELL", "RITC", qty_to_sell)
                            app.postOrder("BUY", "BULL", qty_to_sell)
                            app.postOrder("BUY", "BEAR", qty_to_sell)
                            arb_qty_realized -= qty_to_sell
                            time.sleep(0.1)
                        else:
                            pass
                        time.sleep(0.1)
                    swing_difference = 0.05
                    print("="*50)
                    
                    arb_open = False
                    arb_qty_realized = 0
                    arb_type = -1

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
                    tender_id = app.postTender(id)
                    print("-"*50)

                    if tender_id == 200:
                        while qty > 0:
                            qty_to_sell = min(qty, 10000)
                            app.postOrder(action_to_close, "RITC", qty_to_sell)
                            qty -= qty_to_sell
                            time.sleep(0.1)

                        print("="*50)
                    else:
                        print("tender failed")

def marketmaking(app : MyTradingApp, **s_d):
    while True:
        app.getSecuritiesBook("RITC", 10, False)
        time.sleep(1)

                    
                






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

    marketmakingthread = mp.Process(target=marketmaking, args=(app,), kwargs = shared_data)
    marketmakingthread.start()


    main(app, **shared_data)




