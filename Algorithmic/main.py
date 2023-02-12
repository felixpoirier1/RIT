from tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging
import sys

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])


##### Variables to share between processes #####
streaming_started = mp.Value('b', False)

# create array of n elements of type string

lock = mp.Lock()


############## Streaming function #############

def streamPrice(app, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    while True:
        time.sleep(0.2)
        #examples for modifying shared data stored in arrays
        securities = app.getSecurities()
        for index, ticker in enumerate(s_d["tickers_name"][:]):
            s_d["lock"].acquire()
            s_d["tickers_ask"][index] = securities[ticker]["ask"]
            s_d["tickers_bid"][index] = securities[ticker]["bid"]
            s_d["lock"].release()
        
        time.sleep(0.1)
        latest_tenders = app.getTenders()
        if latest_tenders != None:
            s_d["latest_tenders"].update(latest_tenders)
        

        #print(s_d["tickers_bid"][-1])

        #always use the .value attribute when accessing shared single value (mp.Value)
        s_d["streaming_started"].value = True
        #number = float(bidask["asks"].iloc[0]["price"])


############### Main function ################

def main(app, **s_d):
    #s_d stands for shared_data (but shorter to make it easier to type and shorter to read)
    #while True is a loop that will run forever (CTRL+C to stop it)
    while True:

        if s_d["streaming_started"].value:
            time.sleep(0.01)
            #print(s_d["tickers_bid"][:])

            if s_d["tickers_bid"][:][s_d["tickers_name"][:].index("RITC")] > 10:
                pass
            print(" "*20, end ="\r")
            print(s_d["tickers_bid"][:], end ="\r")
            
            # if len(s_d["latest_tenders"].keys()) != 0:
            #     all_tender_ids = list(s_d["latest_tenders"].keys())
            #     all_tender_tickers = [s_d["latest_tenders"][tender_id]["ticker"] for tender_id in all_tender_ids]
            #     all_tender_tick = [s_d["latest_tenders"][tender_id]["tick"] for tender_id in all_tender_ids]
            #     all_tender_expiration = [s_d["latest_tenders"][tender_id]["expires"] for tender_id in all_tender_ids]
            #     all_tender_price = [s_d["latest_tenders"][tender_id]["price"] for tender_id in all_tender_ids]
            #     all_tender_quantity = [s_d["latest_tenders"][tender_id]["quantity"] for tender_id in all_tender_ids]

            #     if all_tender_price[-1] > 10:
            #         print(f"executing tender {all_tender_ids[-1]}")
            #         time.sleep(2)
            #         app.postTender(all_tender_ids[-1])



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

    latest_tenders = {}
    mgr = mp.Manager()
    latest_tenders = mgr.dict()
    latest_tenders.update(latest_tenders)




    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "latest_tenders": latest_tenders,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




