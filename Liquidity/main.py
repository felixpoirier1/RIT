#import tradeapp module 
from tradeapp.tradeapp import TradingApp, LOG_COLORS
import winsound
# for raw arbitrages
from utils import createSyntheticETF, findOptimalArbitrageQty
# for tenders
from utils import isProfitable, findVwap
import matplotlib.pyplot as plt
import numpy as np
import time
import multiprocessing as mp
import logging
import colored
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



############### Main function ################

def main(app : TradingApp, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    #while True is a loop that will run forever (CTRL+C to stop it)

    print("="*50)
    securities_info = app.getSecurities()
    tickers_name = list(securities_info.keys())

    while True:
            
        tick = app.currentTick()

        
        latest_tenders = app.getTenders()
        if latest_tenders == None:
            latest_tenders = {}

        tenders = {}
        auctions = {}

        # tenders 
        if latest_tenders != {}:
            for key in latest_tenders.keys():
                    if latest_tenders[key]["is_fixed_bid"] == True:
                        tenders[key] = latest_tenders[key]
                    else:
                        auctions[key] = latest_tenders[key]

            for id in tenders:
                price = tenders[id]["price"]
                qty = tenders[id]["quantity"]
                action = tenders[id]["action"]
                ticker = tenders[id]["ticker"]

                if action == "BUY":
                    direction = "bids"
                    action_to_close = "SELL"
                elif action == "SELL":
                    direction = "asks"
                    action_to_close = "BUY"
                
                book = app.getSecuritiesBook(ticker, df = False)
                book = np.array([[int(book[direction][i]["quantity"] - book[direction][i]["quantity_filled"]), float(book[direction][i]["price"])] for i in range(len(book[direction]))])

                #the lower the slack the more likely the tender will be accepted but the less profitable they likely will be
                if isProfitable(price, book, direction[:-1], qty, slack = price*0.001):
                    tender_id = app.postTender(id)
                    
                    print(f"{colored.fg(2)}\toffload {qty} shares of {ticker} by clicking on the {'right <=' if action=='BUY' else 'left =>'} {colored.attr(0)}")
                    print("="*50)
                    winsound.Beep(500, 500)


                else:
                    print(f"{colored.fg(1)}tender for {qty} shares of {ticker} @ {price} is not profitable{colored.attr(0)}")    
            

            for id in auctions:
                qty = auctions[id]["quantity"]
                action = auctions[id]["action"]
                ticker = auctions[id]["ticker"]
                expiration = auctions[id]["expires"]


                if action == "BUY":
                    direction = "bids"
                    action_to_close = "SELL"
                elif action == "SELL":
                    direction = "asks"
                    action_to_close = "BUY"
                
                book = app.getSecuritiesBook(ticker, df = False)
                book = np.array([[int(book[direction][i]["quantity"] - book[direction][i]["quantity_filled"]), float(book[direction][i]["price"])] for i in range(len(book[direction]))])
                
                vwap = round(findVwap(book, direction[:-1], qty), 2)

                if action == "BUY":
                    print(f"{colored.fg(3)}auction is profitable below {vwap*(1-0.001)} {colored.attr(0)}")

                    if tick == expiration-1:
                        app.postTender(id, price = vwap*(1-0.001))
                        print(f"{colored.fg(4)}\tif auction accepted offload {qty} shares of {ticker} by clicking on the {'right <=' if action=='BUY' else 'left =>'} {colored.attr(0)}")
                        winsound.Beep(500, 500)

                        
                elif action == "SELL":
                    print(f"{colored.fg(3)}auction is profitable above {vwap*(1+0.001)} {colored.attr(0)}")

                    if tick == expiration-1:
                        app.postTender(id, price = vwap*(1+0.001))
                        print(f"{colored.fg(4)}\tif auction accepted offload {qty} shares of {ticker} by clicking on the {'right <=' if action=='BUY' else 'left =>'} {colored.attr(0)}")
                        winsound.Beep(500, 500)

        time.sleep(1)
                






if __name__ == "__main__":
    app = MyTradingApp("9999", "0CEN4JP9")
    # shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.

    # retrieves the list of tickers and stores it in a shared list

    main(app)




