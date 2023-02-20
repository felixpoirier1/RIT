from tradeapp import TradingApp, LOG_COLORS

import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging
import re


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
class textAnalysis():
    def returnDay(string:str):
        days = {"DAY 1", "DAY 2", "DAY 3", "DAY 4", "DAY 5"}
        for day in days:
            if day in string.capitalize():
                givenday=day
                break
            else:
                givenday="None"
        return givenday
    def returnType(stringElement):
        if "temperature forecast" in stringElement.lower():
            return("Temp")
        elif "fines" == stringElement.lower():
            return("Fine")
        elif "spot price and volumes" in stringElement.lower():
            return("SpotVol")
        elif "sunlight forecast" in stringElement.lower():
            return("LightForecast")
        elif "price and volume bulletin" in stringElement.lower():
            return("VolumeBul")
        elif "sunlight" in stringElement.lower():
            return("SunlightFor")
       
        
        
    
    def returnTwoNum(phrase,target_string):
       
        matches = re.findall(r'{}.*?([\d.]+).*?([\d.]+)'.format(target_string), phrase)
        return matches
       
    def returnTwoNums(phrase,target_string,str2):
        if target_string in phrase:
            matches = re.findall(r'{}.*?([\d.]+).*?([\d.]+)'.format(target_string), phrase)
            
        else:
            matches=textAnalysis.returnWordBefore(phrase,1,str2)
        return matches

    def returnWordBefore(my_phrase,order,line):

        match = re.search(r'(\d+(?:\.\d+)?)\D+(?={})'.format(line), my_phrase)
        return(match.group(order))
    def get_decimal_after_word(phrase, word):
       
        
        pos = phrase.find(word)
        if pos == -1:
            return None

    
        substring = phrase[pos+len(word):]

        
        decimal_str = re.search(r'\d+\.\d+', substring)
        if not decimal_str:
            return None
        decimal = float(decimal_str.group())

        return decimal

def newsInfoFounder(news: list):
    # create an empty dictionary to hold the information we'll extract from the news list
    InfoDic = {}

    # loop through each news item in the list
    for j in news:
        # determine the type of news item based on its headline
        typeReturn = textAnalysis.returnType(j["headline"])

        # if the news item is about temperature
        if typeReturn == "Temp":
            # extract the temperature and tick information from the news item's body
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["Temp " + textAnalysis.returnDay(j["headline"]) + " at tick " + str(j["tick"])] = (
                textAnalysis.returnTwoNum(j["body"], "temperature"), j["tick"])

        # if the news item is about fines
        elif typeReturn == "Fine":
            # extract the fine amount and tick information from the news item's body
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["Fines " + str(textAnalysis.returnDay(j["body"])) + " at tick " + str(j["tick"])] = (
                textAnalysis.returnTwoNum(j["body"], "fine")[0], j["tick"])

        # if the news item is about volume and price movements for a particular commodity
        elif typeReturn == "VolumeBul":
            # extract the volume information and tick information from the news item's body
            # as well as other information about the contracts and participants
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["VolumeBul" + textAnalysis.returnDay(j["headline"]) + " at tick" + str(j["tick"])] = [
                textAnalysis.returnTwoNum(j["body"], "between"),
                j["tick"],
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for buying"),
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for selling"),
                textAnalysis.returnWordBefore(j["body"], 1, "Producers"),
                textAnalysis.returnWordBefore(j["body"], 1, "Distributors"),
                textAnalysis.returnWordBefore(j["body"], 1, "Traders"),
                float(textAnalysis.returnWordBefore(j["body"], 1, "cent")) / 100
            ]

        # if the news item is about spot volume and price movements for a particular commodity
        elif typeReturn == "SpotVol":
            # extract the spot volume and price information and tick information from the news item's body
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["SpotVol " + str(textAnalysis.returnDay(j["headline"])) + " at tick " + str(j["tick"])] = (
                textAnalysis.returnWordBefore(j["body"], 1, "to buy")[0],
                textAnalysis.get_decimal_after_word(j["body"], "buy at a price"),
                textAnalysis.returnWordBefore(j["body"], 1, "to sell")[0],
                textAnalysis.get_decimal_after_word(j["body"], "sell at a price"),
                j["tick"]
            )

        # if the news item is about sunlight forecast
        elif "SUNLIGHT Forecast" in j["headline"]:
            # extract the forecasted sunlight information from the news item's body
            # and add it to the InfoDic dictionary with a key that


            InfoDic["Sunlight forecast at"+str(textAnalysis.returnDay(j["headline"]))+" at tick "+str(j["tick"])]=textAnalysis.returnTwoNums(j["body"],"between","sunlight")
        
    return(InfoDic)      


    
    
        
    
    
def streamElements(app, **shared_data):
    global new
    bidask = app.getSecuritiesBook("NG")
    bid = float(bidask["asks"].iloc[0]["price"])
    ask= float(bidask["bids"].iloc[0]["price"])
    new = app.getNews()
    
    print(newsInfoFounder(new))
    
   
    
    
        #number = float(bidask["asks"].iloc[0]["price"])



############### Main function ################

def main(app):
    while True:
        time.sleep(0.001)
        streamElements(app)
        
   
        




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





