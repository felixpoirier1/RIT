from tradeapp.tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
from multiprocessing.managers import BaseManager, NamespaceProxy
import requests

def var_list():
    # return the list of securities we can trade on the actual period
    nb_var = 11
    list_var=[40]
    list_var[0]="RTM"
    
    app=TradingApp("9999","EG6SMVYC")    
    case = requests.get(app.url + '/case', headers=app.API_KEY).json()

    if case["period"] ==1 :
        for i in range(1,nb_var):
                
            c1="RTM1C"+str(i+44)
            p1= "RTM1P"+str(i+44)
            c2= "RTM2C"+str(i+44)
            p2="RTM2P"+str(i+44)
            list_var.extend([c1,p1,c2,p2])
            # list of variable for the first month 
        
    else:  
        for i in range(1,nb_var):
                
            c2= "RTM2C"+str(i+44)
            p2="RTM2P"+str(i+44)
            list_var.extend([c2,p2])
        
        # list of varibale for the second month
    return(list_var)


class MyTradingApp(TradingApp):
    def __init__(self, host, API_KEY):
        super().__init__(host, API_KEY)
    def varList(self):
        nb_var = 11
        list_var=[40]
        list_var[0]="RTM" 
        if self.period ==1 :
            for i in range(1,nb_var):
                    
                c1="RTM1C"+str(i+44)
                p1= "RTM1P"+str(i+44)
                c2= "RTM2C"+str(i+44)
                p2="RTM2P"+str(i+44)
                list_var.extend([c1,p1,c2,p2])
                # list of variable for the first month
        
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
    app = MyTradingApp("9999", "0CEN4JP9")

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




