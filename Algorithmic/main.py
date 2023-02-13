from tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging
import sys

#logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])


##### Variables to share between processes #####
streaming_started = mp.Value('b', False)

# create array of n elements of type string

lock = mp.Lock()


############## Streaming function #############

def streamPrice(app, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    while True:
        time.sleep(0.1)
        #examples for modifying shared data stored in arrays
        securities = app.getSecurities()
        for index, ticker in enumerate(s_d["tickers_name"][:]):
            s_d["tickers_ask"][index] = securities[ticker]["ask"]
            s_d["tickers_bid"][index] = securities[ticker]["bid"]
            s_d["tickers_pos"][index] = securities[ticker]["position"]
        
        # time.sleep(0.1)
        # latest_tenders = app.getTenders()
        # if latest_tenders != None:
        #     s_d["latest_tenders"].update(latest_tenders)
        

        #print(s_d["tickers_bid"][-1])
        if s_d["streaming_started"].value == False:
            time.sleep(2)
        #always use the .value attribute when accessing shared single value (mp.Value)
        s_d["streaming_started"].value = True
        #number = float(bidask["asks"].iloc[0]["price"])


############### Main function ################

def main(app, **s_d):
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

            if all([pos == 0 for pos in s_d["tickers_pos"][:]]):
                print((BULL_ask + BEAR_ask)/USD_ask, RITC_bid*0.99)
                if (BULL_ask + BEAR_ask)/USD_ask < RITC_bid*0.98:
                    app.postOrder("SELL", "RITC", 100)
                    app.postOrder("BUY", "BULL", 100)
                    app.postOrder("BUY", "BEAR", 100)
                
                elif (BULL_bid + BEAR_bid)/USD_bid > RITC_ask*1.02:
                    app.postOrder("BUY", "RITC", 100)
                    app.postOrder("SELL", "BULL", 100)
                    app.postOrder("SELL", "BEAR", 100)
            





if __name__ == "__main__":
    app = TradingApp("9999", "0CEN4JP9")

    # shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.

    # retrieves the list of tickers and stores it in a shared list
    tickers_name_ = list(app.getSecurities().keys())
    tickers_name = [mp.Array('c', 1) for i in range(len(tickers_name_))]
    tickers_name[:] = list(app.getSecurities().keys())

    tickers_bid = mp.Array('f', len(tickers_name_))

    tickers_ask = mp.Array('f', len(tickers_name_)) 

    tickers_pos = mp.Array('f', len(tickers_name_))

    latest_tenders = {}
    mgr = mp.Manager()
    latest_tenders = mgr.dict()
    latest_tenders.update(latest_tenders)


    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "tickers_pos": tickers_pos,
                    "latest_tenders": latest_tenders,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




