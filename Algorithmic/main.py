from tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp


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
        print(s_d["tickers_bid"][:])

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
    tickers_bid[0] = 50

    tickers_ask = mp.Array('f', len(tickers_name_)) 




    shared_data = {
                    'streaming_started': streaming_started,
                    'tickers_name': tickers_name,
                    "tickers_bid": tickers_bid,
                    "tickers_ask": tickers_ask,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




