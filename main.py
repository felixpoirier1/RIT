from tradeapp import TradingApp, LOG_COLORS

import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging


##### Variables to share between processes #####
number = [mp.Value('d', 0.0) for i in range(2)]


# create array of n elements of type string


lock = mp.Lock()

#create al ist len tick with all news elements
news=[]
############## Streaming function #############
def casedetails(app):
    while True:
        info=app.getTraderDetail()
        return(info)
previous_news=None
temperaturelog={}
def returnDay(stringNews: str):
    days = {"DAY 1", "DAY 2", "DAY 3", "DAY 4", "DAY 5"}
    for day in days:
        if day in news["headline"]:
            givenday=day
            break
        else:
            givenday=None
    return givenday
def returnType(stringElement):
    if "TEMPERATURE Forecast" in stringElement:
        return("Temp")
    elif "FINES" == stringElement:
        return("Fine")
    elif "SPOT PRICE AND VOLUMES" in stringElement:
        return("SpotVol")
    elif ""
def newsInfoFounder(news: list):
    #Return given day
    
    
        
    
    
def streamElements(app, **shared_data):
    global previous_news
    global newsevent
    while True:
        bidask = app.getSecuritiesBook("NG")
        
        bid = float(bidask["asks"].iloc[0]["price"])
        ask= float(bidask["bids"].iloc[0]["price"])
        new = app.getNews()
        
        print(bid,ask)
        print(new)
        #number = float(bidask["asks"].iloc[0]["price"])



############### Main function ################

def main(app):
    while True:
        time.sleep(0.1)
        securities = app.getTradingLimits()
        
   
        




if __name__ == "__main__":
    app = TradingApp("9999", "SNLJLYXD")

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
    streamthread = mp.Process(target=streamElements, args=(app,), kwargs = shared_data)
    streamthread.start()


    main(app)





