from tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
from multiprocessing.managers import BaseManager, NamespaceProxy


##### Variables to share between processes #####
number = mp.Value('f', 0.00)
# create array of n elements of type string


lock = mp.Lock()


############## Streaming function #############

def streamPrice(app, **shared_data):
    while True:
        bidask = app.getSecuritiesBook("RITC")
        shared_data["lock"].acquire()
        shared_data["number"].value = float(bidask["asks"].iloc[0]["price"])
        shared_data["lock"].release()

        #number = float(bidask["asks"].iloc[0]["price"])


############### Main function ################

def main(app, **shared_data):
    while True:
        time.sleep(0.1)
        securities = app.getSecuritiesBook("RITC")
        print(shared_data["number"].value)
        



BaseManager.register('TradingApp', TradingApp)

if __name__ == "__main__":
    app = TradingApp("9999", "0CEN4JP9")

    # shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.
    shared_data = {
                    'number': number,
                    "lock": lock
                    }

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    streamthread = mp.Process(target=streamPrice, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app, **shared_data)




