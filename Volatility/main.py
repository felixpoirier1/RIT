from tradeapp.tradeapp import TradingApp
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
from multiprocessing.managers import BaseManager, NamespaceProxy
import requests
from scipy.stats import norm
from math import log,exp,sqrt
import re

class MyTradingApp(TradingApp):
    def __init__(self, host, API_KEY):
        super().__init__(host, API_KEY)
        
    def varList(self):
        nb_var = 11
        list_var=[40]
        list_var[0]="RTM" 
        if (self.period ==2) or (self.tick >=300):
            for i in range(1,nb_var):   
                c2= "RTM2C"+str(i+44)
                p2="RTM2P"+str(i+44)
                list_var.extend([c2,p2])
        else :
            for i in range(1,nb_var):
                
                c1="RTM1C"+str(i+44)
                p1= "RTM1P"+str(i+44)
                c2= "RTM2C"+str(i+44)
                p2="RTM2P"+str(i+44)
                list_var.extend([c1,p1,c2,p2])
                
        return(list_var)
    def black_scholes(S, K, T, r, sigma, IsCall):
        
        """This method returns the theorical price of an option
            Parameters
            ----------
            S : Underlying asset price
            K : Strike price
            T : maturity 
            r : risk free
            IsCall : 1 for a call, -1 for a put """
            
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        N_d1 = norm.cdf(d1*IsCall)
        N_d2 = norm.cdf(d2*IsCall)
        return IsCall*S * N_d1 - K*IsCall * exp(-r * T) * N_d2
    
    def implied_volatility(price, S, K, T, r, IsCall,delta = None):
        """This method returns the implied volatility or the implied delta of an option

            Parameters
            ----------
            Price : Price of the option
            S : Underlying asset price
            K : Strike price
            T : maturity 
            r : risk free
            IsCall : 1 for a call, -1 for a put
            delta : If <> None, the function returns implied delta
            """
    
        tolerance=0.000001
        max_iter=100
        sigma = 0.5
        for i in range(max_iter):
            vega = S * norm.pdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) * sqrt(T)
            price_diff = MyTradingApp.black_scholes(S, K, T, r, sigma, IsCall) - price
            if abs(price_diff) < tolerance:
                if delta==None:
                    return sigma
                else:
                    return norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
            sigma -= price_diff / vega
        
        return None
    
    def price(self,ticker,type):
        """This method sends the bid/ask price of a ticker

            Parameters
            ----------
            type : int
                0 for bid price, 1 for ask price and 2 for lastprice"""
                
        list_var = MyTradingApp.varList(app)
        if type == 0:
            bid = TradingApp.getSecuritiesBook(app,ticker).get("bids")["price"]
            return bid
        elif type==1:
            ask = TradingApp.getSecuritiesBook(app,ticker).get("asks")["price"]
            return ask
        elif type==2:
            lastPrice = 0.01 +TradingApp.getSecuritiesBook(app,ticker).get("bids")["price"]
            return lastPrice
        return None

    def newsExtract(self):
        """This method returns the delta, the mean vol or the annualized vol annonced with the latest news

            Parameters
            ----------
            
        # news timing 0,0,37,75,112,150,187,225,262"""
        
        x = MyTradingApp.getNews(app,20,1,True)
    
        if x["news_id"]%2 ==0 and x["news_id"]>2 :
            percentage_pattern = r'\d+\.?\d*%'
            percentage_match = re.search(percentage_pattern, x["body"])
            
            if percentage_match:
                percentage_value = float(percentage_match.group(0).strip('%')) / 100
        elif x["news_id"]%2 ==1 and x["news_id"]>=2:  
            percentage_pattern = r'\d+\.?\d*%'
            percentage_match = re.search(percentage_pattern, x["body"])
            if percentage_match:
                bottomVol = float(percentage_match.group(0).strip('%'))
            percentage_value = bottomVol +0.025
            #bottom/top spread is constant and equal to 5% 
            
        elif x["news_id"]==2: 
            lines = x["body"].split(" and ")
            for line in lines:
                if "delta limit for this heat is" in line:
                    percentage_value= int(line.split(" ")[-1].replace(",", ""))
        elif x["news_id"]==1: 
            lines = x["body"].split(".")
            for line in lines:
                if "annualized volatility is" in line:
                    percentage_value = float(line.split(" ")[-2].strip("%"))
        return(percentage_value)
        
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
        


# shared data contains the data that will be shared between processes
    # it's important that data that is stored in shared_data and is declared using mp.Value,
    # or mp.Array otherwise it will not be shared between processes.
    # I recommend declaring these variables right after the imports and before the functions
    # see above for an examples.
    #shared_data = {
                    #'number': number,
                    #"lock": lock
                    #}

    # streamthread is a variable which will be used to stream data to data declared in shared_data
    #streamthread.start()


    #main(app, **shared_data)

#BaseManager.register('TradingApp', TradingApp)

if __name__ == "__main__":
    app = MyTradingApp("9999", "EG6SMVYC")
    x= MyTradingApp.newsExtract(app)
    print(x)