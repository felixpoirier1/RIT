from tradeapp import TradingApp, LOG_COLORS

import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging
import re
import pandas as pd
import array


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
        
        days = ["DAY 1", "DAY 2", "DAY 3", "DAY 4", "DAY 5","DAY 6"]
        for day in days:
            
            if day in string:
                givenday=day
                return givenday
            else:
                pass
        
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
            matches = re.findall(r'{}.*?([\d.]+).*?([\d.]+)'.format(target_string), phrase)[0]
            matches = [float(match) for match in matches]
            return matches
            
        else:
            matches=float(textAnalysis.returnWordBefore(phrase,1,str2))
        return matches

        
    def returnWordBefore(phrase,order, substring):
        # Search for the substring and extract the portion of the string before it
        match = re.search(r'(.*{}).*'.format(substring), phrase)
        
        if match is None:
            return None
        
        prefix = match.group(order)
        
        # Search for the last number in the prefix
        match = re.search(r'\d+(?:\.\d+)?', prefix)
        if match is None:
            return None
        
        return match.group()
  

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
    def word_in_phrase(word, phrase):
        return int(word in phrase)

def newsInfoFounder(news: list):
    # create an empty dictionary to hold the information we'll extract from the news list
    InfoDic = {}
    TempLog={}
    SunlightLog={}
    TenderInfoLog={}
    FineLog={}
    SpotVol={}
    PriceVol={}
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
            TempLog[textAnalysis.returnDay(j["headline"])+str(j["tick"])]=textAnalysis.returnTwoNum(j["body"], "temperature")

        # if the news item is about fines
        elif typeReturn == "Fine":
            # extract the fine amount and tick information from the news item's body
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["Fines " + str(textAnalysis.returnDay(j["body"])) + " at tick " + str(j["tick"])] = (
                textAnalysis.returnTwoNum(j["body"], "fine")[0], j["tick"])
            FineLog[str(j["tick"])]=(textAnalysis.returnTwoNum(j["body"], "fine")[0], j["tick"])

        # if the news item is about volume and price movements for a particular commodity
        elif typeReturn == "VolumeBul":
            
            # extract the volume information and tick information from the news item's body
            # as well as other information about the contracts and participants
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["VolumeBul"+ " at tick" + str(j["tick"])] = [
                textAnalysis.returnTwoNum(j["body"], "between"),
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for buying"),
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for selling"),
                textAnalysis.returnWordBefore(j["body"], 1, "Producers"),
                textAnalysis.returnWordBefore(j["body"], 1, "Distributors"),
                textAnalysis.returnWordBefore(j["body"], 1, "Traders"),
                textAnalysis.returnWordBefore(j["body"],1,"cent")
            ]
            PriceVol[str(j["tick"])]=[
                textAnalysis.returnTwoNum(j["body"], "between"),
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for buying"),
                textAnalysis.returnWordBefore(j["body"], 1, "contracts for selling"),
                textAnalysis.returnWordBefore(j["body"], 1, "Producers"),
                textAnalysis.returnWordBefore(j["body"], 1, "Distributors"),
                textAnalysis.returnWordBefore(j["body"], 1, "Traders"),
                textAnalysis.returnWordBefore(j["body"],1,"cent")
            ]


        # if the news item is about spot volume and price movements for a particular commodity
        elif typeReturn == "SpotVol":
            # extract the spot volume and price information and tick information from the news item's body
            # and add it to the InfoDic dictionary with a key that includes the day and tick information
            InfoDic["SpotVol "+ " at tick " + str(j["tick"])] = (
                textAnalysis.returnWordBefore(j["body"], 1, "to buy")[0],
                textAnalysis.get_decimal_after_word(j["body"], "buy at a price"),
                textAnalysis.returnWordBefore(j["body"], 1, "to sell")[0],
                textAnalysis.get_decimal_after_word(j["body"], "sell at a price"),
                
            )
            SpotVol[str(j["tick"])]=(
                textAnalysis.returnWordBefore(j["body"], 1, "to buy")[0],
                textAnalysis.get_decimal_after_word(j["body"], "buy at a price"),
                textAnalysis.returnWordBefore(j["body"], 1, "to sell")[0],
                textAnalysis.get_decimal_after_word(j["body"], "sell at a price")
                
            )

        # if the news item is about sunlight forecast
        elif "SUNLIGHT Forecast" in j["headline"]:
            # extract the forecasted sunlight information from the news item's body
            # and add it to the InfoDic dictionary with a key that

            
            InfoDic["Sunlight forecast at"+str(textAnalysis.returnDay(j["headline"]))+" at tick "+str(j["tick"])]=textAnalysis.returnTwoNums(j["body"],"between","sunlight")
            SunlightLog[str(j["tick"])+textAnalysis.returnDay(j["headline"])]=textAnalysis.returnTwoNums(j["body"],"between","sunlight")
        
        elif "TENDER" in j["headline"]:
            InfoDic["Tender "+"Tick "+str(j["tick"])]=textAnalysis.word_in_phrase("BUY",j["body"])
            TenderInfoLog[str(j["tick"])]=textAnalysis.word_in_phrase("BUY",j["body"])
        SpotVolLog = {}
        PriceVolLog={}
        for key in sorted(SpotVol, key=int, reverse=True):
            SpotVolLog[key] = SpotVol[key]
        for key in sorted(PriceVol, key=int, reverse=True):
            PriceVolLog[key] = PriceVol[key]
    return(InfoDic,TempLog,SunlightLog,TenderInfoLog,FineLog,SpotVolLog,PriceVolLog)      


    
    
def reorder_dict_by_int_keys(d):
    return {k: d[k] for k in sorted(d, key=lambda x: int(x))}

    
    
def streamElements(app,role):
    global new
    global period
    global sunLight
    bidask = app.getSecuritiesBook("NG")
    bid = float(bidask["asks"].iloc[0]["price"])
    ask = float(bidask["bids"].iloc[0]["price"])
    new = app.getNews()
    
    period = app.getCaseDetails()["period"]
    
    newsinfo=newsInfoFounder(new)
    spot_securities = {
    2: "ELEC-day2",
    3: "ELEC-day3",
    4: "ELEC-day4",
    5: "ELEC-day5",
    6: "ELEC-day6"
    }
    spot_book_name = spot_securities.get(period)

    #(InfoDic,TempLog,SunlightLog,TenderInfoLog,FineLog,SpotVol)   

    bidaskSpot = app.getSecuritiesBook(spot_book_name)
    
    if role==3:
        print("Trader Functions")
        todayBidSpot=bidaskSpot
        spot_volume=next(iter(newsinfo[5].values()))
        PriceVol=next(iter(newsinfo[6].values()))
        possibleTenders=newsinfo[3]
        fines=newsinfo[4]
        tendeoffer=app.getTenders()
    elif role==2:
        print("Distributor Function")
        todayBidSpot=bidaskSpot
        spot_volume=next(iter(newsinfo[5].values()))
        PriceVol=next(iter(newsinfo[6].values()))
        fines=newsinfo[4]
        temperature=newsinfo[1]
        print(temperature)
    elif role==1:
        print("Producer Function")
        sunLight=newsinfo[2]
        
        todayBidSpot=bidaskSpot
        ngPrice=bidask
        spot_volume=next(iter(newsinfo[5].values()))
        PriceVol=next(iter(newsinfo[6].values()))
        fines=newsinfo[4]
        print(sunLight)

############### Main function ################

def main(app):
    """""
    roles are the roles you are given during the competition
    role=1 if producer
    role=2 if distributer
    role=3 if trader
    
    
    """""
    
    while True:
        time.sleep(0.001)
        streamElements(app,role=3)
        
   
        




if __name__ == "__main__":
    app = TradingApp("9999", "SNLJLYXD")

    # shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.
    # shared_data = {
    #                 'number': number,
    #                 "lock": lock
    #                 }

    # # streamthread is a variable which will be used to stream data to data declared in shared_data
    # streamthread = mp.Process(target=streamElements, args=(app,rol), kwargs = shared_data)
    # streamthread.start()


    main(app)





