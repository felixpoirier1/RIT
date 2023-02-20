from tradeapp.tradeapp import TradingApp 
import matplotlib.pyplot as plt
import time
import multiprocessing as mp
from multiprocessing.managers import BaseManager, NamespaceProxy
import requests
from scipy.stats import norm
import numpy as np
from math import log,exp,sqrt
import re
from mibian import BS
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
    def black_scholes(self,S, K, T, r, sigma, IsCall):
        
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
    
    def implied_volatility(self,price, S, K, T, r, IsCall,delta = None): #useless
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
    
        tolerance=0.0001
        max_iter=50
        sigma = 0.23
        vega = S * norm.pdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) * sqrt(T)
        for i in range(1,max_iter):
            if sigma <= 0.001:
                sigma = 0.001
            price_diff = self.black_scholes(S, K, T, r, sigma, IsCall) - price
            if abs(price_diff) < tolerance:
                if delta==None:
                    return sigma
                else:
                    return norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
            sigma = sigma-(price_diff / vega)
        if delta == None:
            return vega
        else: 
            return norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
        
    def deltaclac(self,price, S, K, T,sigma, r, IsCall):
        tol = 0.00001
        delta = norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
        vega = S * norm.pdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) * sqrt(T)
        if vega !=0 :
            for i in range(1,100): 
                
                if sigma <= 0.01:
                    sigma = 0.25 
                bsPrice = self.black_scholes(S,K,T,0,sigma,IsCall)
                priceDiff = price - bsPrice
                if abs(priceDiff)<tol: 
                    delta = norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
                    break
                delta = norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
                sigma = sigma + (priceDiff/(vega))
            
        return delta
           
    def price(self,ticker,type):
        """This method sends the bid/ask price of a ticker

            Parameters
            ----------
            type : int
                0 for bid price, 1 for ask price and 2 for lastprice"""
                
        book = self.getSecuritiesBook(ticker)
        if type == 0:
            bid = book.get("bids")["price"].item()
            return bid
        elif type==1:
            ask = book.get("asks")["price"].item()
            return ask
        elif type==2:
            lastPrice = 0.01 + book.get("bids")["price"].item()
            return lastPrice
        return None

    def newsExtract(self,type):
        """This method returns the delta, the mean vol or the annualized vol annonced with the latest news

            Parameters
            ----------
            type : 0 if we want delta limit ,1 for the rest and 2 for the first annonced volatility
            
        # news timing 0,0,37,75,112,150,187,225,262"""
        if type ==2: 
            x = self.getNews(0,25,True)
            lines = x["body"].split(".")
            for line in lines:
                if "annualized volatility is" in line:
                    percentage_value = float(line.split(" ")[-1].strip("%")) *0.01
        elif type ==1:            
            x = self.getNews(25,1,True)
            if x["news_id"]%2 ==0 and x["news_id"]>2 :
                percentage_pattern = r'\d+\.?\d*%'
                percentage_match = re.search(percentage_pattern, x["body"])
                if percentage_match:
                    percentage_value = float(percentage_match.group(0).strip('%')) / 100
                    
            elif x["news_id"]%2 ==1 and x["news_id"]>=2:  
                percentage_pattern = r'\d+\.?\d*%'
                percentage_match = re.search(percentage_pattern, x["body"])
                if percentage_match:
                    bottomVol = int(percentage_match.group(0).strip('%'))
                percentage_value = bottomVol +0.025
                #bottom/top spread is constant and equal to 5% 
            
        elif type==0: 
            x = self.getNews(1,25,True)
            lines = x["body"].split(" and ")
            for line in lines:
                if "delta limit for this heat is" in line:
                    percentage_value= float(line.split(" ")[-1].replace(",", ""))
        return percentage_value
    
    def passOrder(self,nList,posList,secList):
        
        buyPosMod = posList[0]
        sellPosMod = posList[1]
        adjBuyPosMod = posList[2]
        adjSellPosMod = posList[3]
        oldSellPosMod = posList[4]
        oldBuyPosMod = posList[5]
        # Order command
        if secList[3]!=secList[1] and secList[2]!=secList[0]:  # case full new strat
            for i in range(1,max(nList)):
                if i<= nList[4] : 
                    if oldBuyPosMod>=100:
                        self.postOrder("SELL",secList[2],100)
                        oldBuyPosMod -= 100
                    elif oldBuyPosMod>0:
                        self.postOrder("SELL",secList[2],oldBuyPosMod)
                        oldBuyPosMod =0
                if i<= nList[5] : 
                    if oldSellPosMod>=100:
                        self.postOrder("BUY",secList[3],100)
                        oldSellPosMod -= 100
                    elif oldSellPosMod>0:
                        self.postOrder("BUY",secList[3],oldSellPosMod)
                        oldSellPosMod =0     
                if i<= nList[0] : 
                    if buyPosMod>=100:
                        self.postOrder("BUY",secList[0],100)
                        buyPosMod -= 100
                    elif buyPosMod>0:
                        self.postOrder("BUY",secList[0],buyPosMod)
                        buyPosMod = 0
                    
                if i<= nList[1] : 
                    if sellPosMod>=100:
                        self.postOrder("SELL",secList[1],100)
                        sellPosMod -= 100
                    elif sellPosMod>0:
                        self.postOrder("SELL",secList[1],sellPosMod)
                        sellPosMod =0

        elif secList[2]!=secList[0]:  # case new buy 
            for i in range(1,max(nList[0],nList[3],nList[4])):
                if i<= nList[4] : 
                    if oldBuyPosMod>=100:
                        self.postOrder("SELL",secList[2],100)
                        oldBuyPosMod -= 100
                    elif oldBuyPosMod>0:
                        self.postOrder("SELL",secList[2],oldBuyPosMod)
                        oldBuyPosMod =0
                if i<= nList[3] : 
                    if adjSellPosMod>=100:
                        self.postOrder(adjSellDirection,secList[3],100)
                        adjSellPosMod -= 100
                    elif adjSellPosMod>0:
                        self.postOrder(adjSellDirection,secList[3],adjSellPosMod)
                        adjSellPosMod =0     
                if i<= nList[0] : 
                    if buyPosMod>=100:
                        self.postOrder("BUY",secList[0],100)
                        buyPosMod -= 100
                    elif buyPosMod>0:
                        self.postOrder("BUY",secList[0],buyPosMod)
                        buyPosMod = 0
        
        elif secList[3]!=secList[1]:  # case new sell
            for i in range(1,max(nList[1],nList[2],nList[5])):
                if i<= nList[5] : 
                    if oldSellPosMod>=100:
                        self.postOrder("BUY",secList[3],100)
                        oldSellPosMod -= 100
                    elif oldSellPosMod>0:
                        self.postOrder("BUY",secList[3],oldSellPosMod)
                        oldSellPosMod =0
                if i<= nList[2] : 
                    if adjBuyPosMod>=100:
                        self.postOrder(adjBuyDirection,secList[2],100)
                        adjBuyPosMod -= 100
                    elif adjBuyPosMod>0:
                        self.postOrder(adjBuyDirection,secList[2],adjBuyPosMod)
                        adjBuyPosMod =0     
                if i<= nList[1] : 
                    if sellPosMod>=100:
                        self.postOrder("SELL",secList[1],100)
                        sellPosMod -= 100
                    elif sellPosMod>0:
                        self.postOrder("SELL",secList[1],sellPosMod)
                        sellPosMod = 0
        else:  # case no new à modif
            for i in range(1,max(nList[2],nList[3])):
                if i<= nList[2] : 
                    if adjBuyPosMod>=100:
                        self.postOrder(adjBuyDirection,secList[2],100)
                        adjBuyPosMod -= 100
                    elif adjBuyPosMod>0:
                        self.postOrder(adjBuyDirection,secList[2],adjBuyPosMod)
                        adjBuyPosMod =0     
                if i<= nList[3] : 
                    if adjSellPosMod>=100:
                        self.postOrder(adjSellDirection,secList[3],100)
                        adjSellPosMod -= 100
                    elif adjSellPosMod>0:
                        self.postOrder(adjSellDirection,secList[3],adjSellPosMod)
                        adjSellPosMod =0
        

if __name__ == "__main__":
    app = MyTradingApp("9999", "EG6SMVYC")

    realVol = app.newsExtract(2)  # corriger partout mytradingapp par app
    varList = app.varList()
    k =len(varList)
    priceList = [0]*k
    theoPriceList=[0]*k
    diffList = [0]*k 
    callList = [0]*int((k+1)/2)
    putList = [0]*int((k+1)/2)
    nList = []
    posList=[]
    secList=[]
    directionList=[]
    oldSellSec=0
    oldSellPos = 0
    oldBuySec = 0
    oldBuyPos = 0
    oldBuyPos = 0
    oldSellPos=0
    deltalimit = app.newsExtract(0) * 0.98
    while True:  
        tick =app.currentAbsoluteTick()
        maturity1M = (300-tick)/3600
        maturity2M = (600-tick)/3600
        if tick >300 and tick <305: # refresh list of secuities when the 1st month option expires
            varList = app.varList() 
            k =len(varList)
            priceList = [0]*k
            posList = [0]*k
            theoPriceList=[0]*k
            diffList = [0]*k
            
            callList = [0]*int((k+(k%2))/2) # list of call option price
            putList = [0]*int((k+(k%2))/2) # list of put option price
        
        if  tick in range(37,40) or tick in range(75,78) or tick in range(112,115) or tick in range(150,153) or tick in range(187,190) or tick in range(225,228) or tick in range(262,265) or tick in range(300,303) or tick in range(337,340) or tick in range(375,378) or tick in range(412,415) or tick in range(450,453) or tick in range(487,490) or tick in range(525,528):
            realVol = app.newsExtract(1) # extract the last news info about annualized volatility
            # vol a update, on prend la news effective alors que l'intervalle l'est pas 
            
        priceList[0]= app.price(varList[0],2) # RTM price
        for i in range(1,k): # price list, theorical price list, differences list, call List and put list
            priceList[i]= app.price(varList[i],2)
            if (i%4 == 3 or i%4 ==0) or tick>=300 :
                theoPriceList[i]=app.black_scholes(priceList[0],45+int((i-1)/4),maturity2M,0,realVol,(-1)**(1+i)) 
            else: 
                theoPriceList[i]=app.black_scholes(priceList[0],(45+int((i-1)/4)),maturity1M,0,realVol,((-1)**(1+i)))
                
            diffList[i] = theoPriceList[i]-priceList[i]
            if i%2==1:
                callList[int((i+1)/2)]=diffList[i]
            else:
                putList[int(i/2)]=diffList[i]

        maxdiff=max(diffList)
        mindiff = min(diffList)
        topdiff = max(maxdiff,abs(mindiff))
        buyNumber = diffList.index(maxdiff) 
        sellNumber = diffList.index(mindiff)
        
        if (buyNumber*sellNumber)%2 ==1: # for the strategy, we need to have 2 calls or 2 puts, so we have to change the security if it's necessary
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
                             
        buySec = varList[buyNumber] # the most underpriced option
        sellSec = varList[sellNumber] # the most overpriced option
        if buyNumber != 0: # calculate for each case the buy implied delta 
            if buyNumber%4 == 0 or buyNumber%4==3 or tick>=300: 
                buyDelta = app.deltaclac(priceList[buyNumber],priceList[0],45+((buyNumber-1)/4),maturity2M,realVol,0,(-1)**(1+buyNumber))
            else:
                buyDelta = app.deltaclac(priceList[buyNumber],priceList[0],45+((buyNumber-1)/4),maturity1M,realVol,0,(-1)**(1+buyNumber))
        else: 
            buyDelta = 1
        if sellNumber != 0: # calculate for each case the sell implied delta
            if sellNumber%4 == 0 or sellNumber%4==3 or tick>=300:
                sellDelta = app.deltaclac(priceList[sellNumber],priceList[0],45+((sellNumber-1)/4),maturity2M,realVol,0,(-1)**(1+sellNumber))
            else:
                sellDelta = app.deltaclac(priceList[sellNumber],priceList[0],45+((sellNumber-1)/4),maturity2M,realVol,0,(-1)**(1+sellNumber))   
        else: 
            sellDelta =1
  
        if abs(maxdiff/buyDelta)> abs(mindiff/sellDelta):
            
            sellPos = int(-1500*buyDelta)/(sellDelta-buyDelta)+1
            buyPos =1500-sellPos +int(abs(deltalimit/buyDelta))    
        else:   
            
            buyPos = int(-1500*sellDelta)/(buyDelta-sellDelta)+1
            sellPos =1500-buyPos +int(abs(deltalimit/sellDelta))
        
        secList.extend([buySec,sellSec,oldBuySec,oldSellSec])
        
        adjBuyPos = abs(buyPos-oldBuyPos)
        adjSellPos = abs(sellPos- oldSellPos)
        posList.extend([buyPos,sellPos,adjBuyPos,adjSellPos,oldBuyPos,oldSellPos])
        
        n1 = int(buyPos/100)+1
        n2 = int(sellPos/100) +1
        n3 = int(adjBuyPos/100) +1
        n4 = int(adjSellPos/100) +1
        n5 = int(oldBuyPos/100)+1
        n6 = int(oldSellPos/100)+1
        nList.extend([n1,n2,n3,n4,n5,n6])

        
        if buyPos>= oldBuyPos:
            adjBuyDirection = "BUY"
        else: 
            adjBuyDirection = "SELL"
        if sellPos>=oldSellPos:
            adjSellDirection = "BUY"
        else:
            adjSellDirection = "SELL"
        directionList.extend([adjBuyDirection,adjSellDirection])

        app.passOrder(nList,posList,secList)    

            
        oldSellSec=sellSec
        oldSellPos = sellPos
        oldBuySec = buySec
        oldBuyPos = buyPos
        time.sleep(0.2)
   
        