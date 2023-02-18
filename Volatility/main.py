from tradeapp import TradingApp
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

    def newsExtract(self,type):
        """This method returns the delta, the mean vol or the annualized vol annonced with the latest news

            Parameters
            ----------
            type : 0 if we want delta limit ,1 for the rest and 2 for the first annonced volatility
            
        # news timing 0,0,37,75,112,150,187,225,262"""
        if type ==2: 
            x = MyTradingApp.getNews(app,0,25,True)
            lines = x["body"].split(".")
            for line in lines:
                if "annualized volatility is" in line:
                    percentage_value = float(line.split(" ")[-1].strip("%")) *0.01
                    
        x = MyTradingApp.getNews(app,(20*type)+1,25,True)
    
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
        return percentage_value

        
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
    tick = 700
    realVol = MyTradingApp.newsExtract(app,2)  
    varList = MyTradingApp.varList(app)
    k =len(varList)
    priceList = [0]*k
    posList = [0]*k
    theoPriceList=[0]*k
    diffList = [0]*k
    oldBuyPos = 0
    oldSellPos=0
    deltalimit = MyTradingApp.newsExtract(app,0) * 0.98
    while tick < 600:
        maturity1M = (300-tick)/3600
        maturity2M = (600-tick)/3600
        if tick >300 and tick <305:
            varList = MyTradingApp.varList(app) # refresh list of secuities when the 1st month option expires
            k =len(varList)
            priceList = [0]*k
            posList = [0]*k
            theoPriceList=[0]*k
            diffList = [0]*k
            callList = [0]*(k+(k%2))/2
            putList = [0]*(k+(k%2))/2
        if tick in range(0,10) or tick in range(37,40) or tick in range(75,78) or tick in range(112,115) or tick in range(150,153) or tick in range(187,190) or tick in range(225,228) or tick in range(262,265) or tick in range(300,303) or tick in range(337,340) or tick in range(375,378) or tick in range(412,415) or tick in range(450,453) or tick in range(487,490) or tick in range(525,528):
            realVol = MyTradingApp.newsExtract(app,1) # extract the last news info about annualized volatility
        
        priceList[0]= MyTradingApp.price(app,varList[0],2) # prix RTM
        for i in range(1,k-1):
            priceList[i]= MyTradingApp.price(app,varList[i],2)
            if i%4 == 3 or i%4 ==0:
                theoPriceList[i]=MyTradingApp.black_scholes(priceList[0],45+int((i-1)/4),maturity2M,0,realVol,(-1)^(1+i))
            else: 
                theoPriceList[i]=MyTradingApp.black_scholes(priceList[0],45+int((i-1)/4),maturity1M,0,realVol,(-1)^(1+i))
            diffList[i] = theoPriceList[i]-priceList[i]
            if i%2==1:
                callList[(i+1)/2]=priceList[i]
            else:
                putList[i/2]=priceList[i]
            
        maxdiff=max(diffList)
        mindiff = min(diffList)
        topdiff = max(maxdiff,abs(mindiff))
        buyNumber = diffList.index(maxdiff) 
        sellNumber = diffList.index(mindiff)
        if (buyNumber*sellNumber)%2 ==1:
            if topdiff == maxdiff:
                if buyNumber%2==1:
                    sellNumber=(callList.index(min(callList))*2)+1
                else:
                    sellNumber=(putList.index(min(putList))*2)
            else:
                if sellNumber%2==1:
                    buyNumber=(callList.index(max(callList))*2)+1
                else:
                    buyNumber=(putList.index(max(putList))*2)
                             
        buySec = varList[buyNumber] # we find the most underpriced option
        sellSec = varList[sellNumber] # we find the most overpriced option
        if buyNumber%4 == 0 or buyNumber%4==3:
            buyDelta = MyTradingApp.implied_volatility(priceList[0],priceList[buyNumber],45+((buyNumber-1)/4),maturity2M,0,(-1)^(1+buyNumber),1)
        else:
            buyDelta = MyTradingApp.implied_volatility(priceList[0],priceList[buyNumber],45+((buyNumber-1)/4),maturity1M,0,(-1)^(1+buyNumber),1)
        if sellNumber%4 == 0 or sellNumber%4==3:
            sellDelta = MyTradingApp.implied_volatility(priceList[0],priceList[sellNumber],45+((sellNumber-1)/4),maturity2M,0,(-1)^(1+sellNumber),1)
        else:
            sellDelta = MyTradingApp.implied_volatility(priceList[0],priceList[sellNumber],45+((sellNumber-1)/4),maturity1M,0,(-1)^(1+sellNumber),1)    
        
        if abs(maxdiff/buyDelta)> abs(mindiff/sellDelta):
            
            sellPos = int(-1500*buyDelta)/(sellDelta-buyDelta)+1
            buyPos =1500-sellPos +int(abs(deltalimit/buyDelta))
        else:   
            
            buyPos = int(-1500*sellDelta)/(buyDelta-sellDelta)+1
            sellPos =1500-buyPos +int(abs(deltalimit/sellDelta))
        if oldSellSec!=sellSec or oldBuySec!=buySec: 
            MyTradingApp.postOrder(app,"BUY",oldSellSec,oldSellPos)
            MyTradingApp.postOrder(app,"SELL",oldBuySec,oldBuyPos,100)
            
            MyTradingApp.postOrder(app,"SELL",sellSec,sellPos,100)
            MyTradingApp.postOrder(app,"BUY",buySec,buyPos,100)
        else:
            adjSellPos = sellPos- oldSellPos
            adjBuyPos = buyPos-oldBuyPos
            MyTradingApp.postOrder(app,"SELL",sellSec,adjSellPos)
            MyTradingApp.postOrder(app,"BUY",buySec,adjBuyPos)
            sellPos+=adjSellPos
            buyPos+=adjBuyPos
            
        oldSellSec=sellSec
        oldSellPos = sellPos
        oldBuySec = buySec
        oldBuyPos = buyPos
    
    print(varList)
            
        