from tradeapp import TradingApp, LOG_COLORS

import matplotlib.pyplot as plt
import time
import multiprocessing as mp
import logging
import re
import pandas as pd
import array
import pandas as pd



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
#This 
# This function returns the first three key-value pairs in the dictionary as a new dictionary.
# If the original dictionary has less than three key-value pairs, it returns the entire dictionary.
def get_first_three_values(my_dict):
    # Get the first three keys in the dictionary.
    first_three_keys = list(my_dict.keys())[:3]
    # Create a new dictionary containing only the key-value pairs with the first three keys.
    first_three_values = {k: v for k, v in my_dict.items() if k in first_three_keys}
    # If the new dictionary is empty, return the first key-value pair in the original dictionary.
    return first_three_values or my_dict.get(list(my_dict.keys())[0], {})

# This function takes a dictionary whose keys are strings of integers and returns a new dictionary
# with the same key-value pairs, but with the keys sorted as integers.
def reorder_dict_by_int_keys(d):
    return {k: d[k] for k in sorted(d, key=lambda x: int(x))}

# This function takes a dictionary whose values are lists containing strings of integers and/or '.' 
# and returns a list of the same values, but with any '.' removed and the integers converted to integers.
# If a value contains only one integer, it is returned as a single value rather than a tuple.
def get_all_values(d):
    """
    Returns all values of a dictionary, returning lists as lists and tuples as tuples.

    Args:
        d (dict): The dictionary to get the values from.

    Returns:
        list: A list containing all the values of the dictionary, with lists returned as lists and tuples returned as tuples.
    """
    result = []
    for value in d.values():
        if isinstance(value, list):
            result.append(value)
        elif isinstance(value, tuple):
            result.append(value)
        else:
            result.append([value])
    return result

def check_float(input_value):
    """
    This function takes an input value and checks if it is a float. If it is a float, it returns a new array where the
    first element is a list containing the float value. Otherwise, it returns the input value unchanged.
    """
    if isinstance(input_value, float):
        array = [[input_value]]
        return array
    else:
        return input_value

def demand_function(x):
    return((200-15*x+0.8*x**2))

def predicted_prod(x):
    return(6*x)

def Average(lst):
    return sum(lst) / len(lst)
    
def streamElements(app,role):
    global new
    global period
    global sunLight
    global spot_volume
    
    bidask = app.getSecuritiesBook("NG")
    bid = float(bidask["asks"].iloc[0]["price"])
    ask = float(bidask["bids"].iloc[0]["price"])
    new = app.getNews(return_latest=False)
    
    period = app.getCaseDetails()["period"]
    
    newsinfo=newsInfoFounder(new)
    spot_securities = {
    1:"NG",
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
        ELECF=app.getSecuritiesBook("ELEC")
        spot_volume=next(iter(newsinfo[5].values()))
        PriceVol=next(iter(newsinfo[6].values()))
        possibleTenders=newsinfo[3]
        fines=newsinfo[4]
        tendeoffer=app.getTenders()
        print(tendeoffer)
    elif role==2:
        print("Distributor Function")
        todayBidSpot=bidaskSpot
        try:
            spot_volume=next(iter(newsinfo[5].values()))
        except:
            pass
        try:
            PriceVol=next(iter(newsinfo[6].values()))
        except:
            pass
        fines=newsinfo[4]
        try:
            for j in my_list:
                if len(j)==1:
                    sunlightList.append(demand_function(j[0]))
                if len(j)==2:
                    average=Average(j)
                    sunlightList.append(demand_function(average))
            projecteddemand=sunlightList[0]
            print(projecteddemand)
        except:
            pass
        
    elif role==1:
        print("Producer Function")
        inputs=pd.read_excel("DemandVariable.xlsx")
        demand=inputs["Demand Input"][0]
        print(demand)
        
        sunlight =get_first_three_values(newsinfo[2])
        
        my_list=get_all_values(sunlight)
        sunlightList = []
        try:
            for j in my_list:
                if len(j)==1:
                    sunlightList.append(j[0])
                if len(j)==2:
                    average=Average(j)
                    sunlightList.append(average)
            projectedprotect=sunlightList[0]
            projectedProduction=predicted_prod(projectedprotect)
        except:
            pass
        print("sunprod: ",projectedProduction)
        print("NgBuy", demand-projectedProduction)
        
        try:
            todayBidSpot=bidaskSpot
        except:
            pass
        try:
            ngPrice=bidask
        except:
            pass
        try:
            PriceVol=next(iter(newsinfo[6].values()))
        except:
            pass
        fines=newsinfo[4]
       

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
        streamElements(app,role=1)
        
   
        




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





