#import tradeapp module 
from tradeapp.tradeapp import TradingApp, LOG_COLORS
from utils import createSyntheticETF, findOptimalArbitrageQty
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
        time.sleep(0.05)
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
    ARB_SLIPPAGE = 0.02
    arb_qty_realized = 0
    ARB_SLACK = ARB_COMMISSION + ARB_SLIPPAGE
    arb_open = False
    last_arb_tick = 0
    time_till_double_down = 0
    arb_multiplier = 1
    time_till_double_down = 2
    swing_difference = 0.05

    while True:
        if s_d["streaming_started"].value:
            
            tick = app.currentTick()
            if tick != None:
                print(str(tick).zfill(3), end="\r")
            
            RITC_bid = s_d["tickers_bid"][s_d["tickers_name"].index("RITC")]
            RITC_ask = s_d["tickers_ask"][s_d["tickers_name"].index("RITC")]
            RITC_pos = s_d["tickers_pos"][s_d["tickers_name"].index("RITC")]

            BULL_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BULL")]
            BULL_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BULL")]
            BULL_pos = s_d["tickers_pos"][s_d["tickers_name"].index("BULL")]

            BEAR_ask = s_d["tickers_ask"][s_d["tickers_name"].index("BEAR")]
            BEAR_bid = s_d["tickers_bid"][s_d["tickers_name"].index("BEAR")]
            BEAR_pos = s_d["tickers_pos"][s_d["tickers_name"].index("BEAR")]

            USD_ask = s_d["tickers_ask"][s_d["tickers_name"].index("USD")]
            USD_bid = s_d["tickers_bid"][s_d["tickers_name"].index("USD")]

            # all([pos == 0 for pos in s_d["tickers_pos"][:]]) and 
            if ((BULL_ask + BEAR_ask)/USD_ask < (RITC_bid - ARB_SLACK)) and ((arb_type == -1) or (arb_type == 0)) and (tick >= last_arb_tick + time_till_double_down) and (abs(BEAR_pos)*BEAR_ask + abs(BULL_pos)*BULL_ask + abs(RITC_pos)*RITC_bid < 280000):
                # find the optimal quantity to arbitrage
                BULL_book = app.getSecuritiesBook("BULL", 10, False)
                BULL_book = np.array([[float(BULL_book["asks"][i]["price"]/USD_ask), int(BULL_book["asks"][i]["quantity"] - BULL_book["asks"][i]["quantity_filled"])] for i in range(len(BULL_book["asks"]))])

                BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                BEAR_book = np.array([[float(BEAR_book["asks"][i]["price"]/USD_ask), int(BEAR_book["asks"][i]["quantity"] - BEAR_book["asks"][i]["quantity_filled"])] for i in range(len(BEAR_book["asks"]))])

                RITC_book = app.getSecuritiesBook("RITC", 10, False)
                RITC_book = np.array([[int(RITC_book["bids"][i]["quantity"] - RITC_book["bids"][i]["quantity_filled"]), float(RITC_book["bids"][i]["price"]),] for i in range(len(RITC_book["bids"]))])
                synthbook = createSyntheticETF({"BULL":BULL_book, "BEAR":BEAR_book})

                arb_quantity = min(findOptimalArbitrageQty(RITC_book, synthbook, ARB_SLACK), 10000)


                if arb_quantity == 0:
                    time.sleep(0.01)
                    continue

                else:
                    arb_quantity *= arb_multiplier
                    arb_multiplier = arb_multiplier**2
                    # take position
                    app.postOrder("SELL", "RITC", arb_quantity)
                    app.postOrder("BUY", "BULL", arb_quantity)
                    app.postOrder("BUY", "BEAR", arb_quantity)
                    arb_qty_realized += arb_quantity
                    last_arb_tick = tick
                    arb_open = True
                    arb_type = 0

            elif ((BULL_bid + BEAR_bid)/USD_bid > (RITC_ask + ARB_SLACK)) and ((arb_type == -1) or (arb_type == 1))  and (tick >= last_arb_tick + time_till_double_down) and (abs(BEAR_pos)*BEAR_bid + abs(BULL_pos)*BULL_bid + abs(RITC_pos)*RITC_ask < 280000):
                # find the optimal quantity to arbitrage
                BULL_book = app.getSecuritiesBook("BULL", 10, False)
                BULL_book = np.array([[float(BULL_book["bids"][i]["price"]/USD_bid), int(BULL_book["bids"][i]["quantity"] - BULL_book["bids"][i]["quantity_filled"])] for i in range(len(BULL_book["bids"]))])

                BEAR_book = app.getSecuritiesBook("BEAR", 10, False)
                BEAR_book = np.array([[float(BEAR_book["bids"][i]["price"]/USD_bid), int(BEAR_book["bids"][i]["quantity"] - BEAR_book["bids"][i]["quantity_filled"])] for i in range(len(BEAR_book["bids"]))])

                RITC_book = app.getSecuritiesBook("RITC", 10, False)
                RITC_book = np.array([[int(RITC_book["asks"][i]["quantity"] - RITC_book["asks"][i]["quantity_filled"]), float(RITC_book["asks"][i]["price"])] for i in range(len(RITC_book["asks"]))])

                synthbook = createSyntheticETF({"BULL":BULL_book, "BEAR":BEAR_book})

                arb_quantity = min(findOptimalArbitrageQty(synthbook, RITC_book, ARB_SLACK), 10000)

                if arb_quantity == 0:
                    time.sleep(0.01)
                    continue
                
                else:
                    arb_quantity *= arb_multiplier
                    arb_multiplier = arb_multiplier**2
                    # take position
                    app.postOrder("BUY", "RITC", arb_quantity)
                    app.postOrder("SELL", "BULL", arb_quantity)
                    app.postOrder("SELL", "BEAR", arb_quantity)
                    arb_qty_realized += arb_quantity
                    last_arb_tick = tick
                    arb_type = 1
                    arb_open = True

            
            if arb_open == True and arb_type == 0:
                if ((BULL_bid + BEAR_bid)/USD_bid > RITC_ask + swing_difference):
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

                        qty_to_sell = min(findOptimalArbitrageQty(synthbook, RITC_book, 0), 10000)

                        if qty_to_sell != 0:

                            swing_difference = swing_difference * 0.8
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
                arb_multiplier = 1
                arb_type = -1

            
            elif arb_open == True and arb_type == 1:
                if ((BULL_ask + BEAR_ask)/USD_ask < RITC_bid - swing_difference):
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

                        qty_to_sell = min(findOptimalArbitrageQty(RITC_book, synthbook, -0.2), 10000)

                        if qty_to_sell != 0:
                            swing_difference = swing_difference * 0.8
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
                    arb_multiplier = 1
                    arb_type = -1



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

    qty_filled = mp.Array('i', len(tickers_name_))

    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "tickers_pos": tickers_pos,
                    "latest_tenders": latest_tenders,
                    "qty_filled": qty_filled,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




