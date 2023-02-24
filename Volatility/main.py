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
            lastPrice = 0.01 + book.get("bids").iloc[0]["price"].item()
            
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
            if x["news_id"]%2 ==0 and x["news_id"]>=2 :
                percentage_pattern = r'\d+\.?\d*%'
                percentage_match = re.search(percentage_pattern, x["body"])
                if percentage_match:
                    percentage_value = float(percentage_match.group(0).strip('%')) / 100
                    
            elif x["news_id"]%2 ==1 and x["news_id"]>=2:  
                percentage_pattern = r'\d+\.?\d*%'
                percentage_match = re.search(percentage_pattern, x["body"])
                if percentage_match:
                    bottomVol = int(percentage_match.group(0).strip('%')) / 100
                percentage_value = bottomVol +0.025
                #bottom/top spread is constant and equal to 5% 
            
        elif type==0: 
            x = self.getNews(1,25,True)
            lines = x["body"].split(" and ")
            for line in lines:
                if "delta limit for this heat is" in line:
                    percentage_value= float(line.split(" ")[-1].replace(",", ""))
        return percentage_value
    
    def oldBestStrategy(self,varList,priceList,diffList,absDiffList,callList,putList,maturity1M,maturity2M,realVol,tick,fees,oldStrat):
        
        oldName = oldStrat["name"]
        oldMainSec = oldStrat["main"][0]
        oldMainPos = oldStrat["main"][1]
        oldMainDirection = oldStrat["main"][2]
        oldMainNumber = oldStrat["main"][3]
        oldHedgingSec = oldStrat["hedge"][0]
        oldHedgingPos = oldStrat["hedge"][1]
        oldHedgingDirection = oldStrat["hedge"][2]
        oldHedgingNumber = oldStrat["hedge"][3]
        oldHedgingSec2 = oldStrat["hedge2"][0]
        oldHedgingPos2 = oldStrat["hedge2"][1]
        oldHedgingDirection2 = oldStrat["hedge2"][2]
        oldHedgingNumber2 = oldStrat["hedge2"][3]

        oldStratValue = 0
        oldPos =0      
        
        if oldName=="strat 1":
            if oldMainDirection =="BUY":
                oldMainDirection = 1
                oldHedgingDirection = -1
            else:
                oldMainDirection = -1
                oldHedgingDirection = 1
            
            oldStratValue = oldMainDirection*(oldMainPos*float(diffList[oldMainNumber] )-oldHedgingPos*(float(diffList[oldHedgingNumber]))) -100*fees*2500
            oldPos = (oldMainPos+oldHedgingPos)*200
        elif oldName =="strat 2":
            if oldMainDirection =="BUY":
                oldMainDirection = 1
                oldHedgingDirection = 1
            else:
                oldMainDirection = -1
                oldHedgingDirection = -1
            
            
            oldStratValue = (oldMainDirection*((oldMainPos*float(diffList[oldMainNumber]) + float(oldHedgingPos*diffList[oldHedgingNumber])))) -1000*100*fees
            oldPos = (oldMainPos+oldHedgingPos)*200
        elif oldName =="strat 3":
            if oldMainDirection =="BUY":
                oldMainDirection = 1
                oldHedgingDirection = 1
            else:
                oldMainDirection = -1
                oldHedgingDirection = -1 
            
            oldStratValue = oldMainDirection*(oldMainPos*float(diffList[oldMainNumber]) - oldHedgingPos2*float(diffList[oldHedgingNumber2]))-(2500*100*fees) - fees*oldHedgingPos   
            oldPos = (oldMainPos+oldHedgingPos2)*200 + oldHedgingPos*2
        lossValue = oldStratValue 
        return lossValue
    
    def bestStrategy(self,varList,priceList,diffList,absDiffList,callList,putList,maturity1M,maturity2M,realVol,tick,fees,oldStrat):
        
        stratDic = {}
        # main option calculation:
        maxDiff=max(absDiffList) 
        if  maxDiff == max(diffList)-2*fees:
            mainNumber = diffList.index(maxDiff+2*fees) # main option is underpriced
            mainDirection = 1 
        else: 
            mainNumber = diffList.index(-maxDiff-2*fees) # main option is overpriced         
            mainDirection = -1
        mainSec = varList[mainNumber]
        if mainNumber%2 ==1:
            mainType = 1 # 1 = call, -1=put
        else:
            mainType = -1   
        
        if mainNumber%4 == 0 or mainNumber%4==3 or tick>=300: 
            mainDelta = self.deltaclac(priceList[mainNumber],priceList[0],45+((mainNumber-1)/4),maturity2M,realVol,0,(-1)**(1+mainNumber))
        else:
            mainDelta = self.deltaclac(priceList[mainNumber],priceList[0],45+((mainNumber-1)/4),maturity1M,realVol,0,(-1)**(1+mainNumber))
        mainPos = 0 
        hedgingDirection =0
        hedgingPos = 0
        hedgingDirection2 = 0
        hedgingPos2 =0
        strat1 = 0
        strat2 =0
        strat3 = 0
        hedgingSec2 = 0
        hedgingNumber2 = 0
        
        # begining of the strat 1 
        for i in range (1,4):
            if  maxDiff == max(diffList)-2*fees:
                mainNumber = diffList.index(maxDiff+2*fees) # main option is underpriced
                mainDirection = 1 
            else: 
                mainNumber = diffList.index(-maxDiff-2*fees) # main option is overpriced         
                mainDirection = -1
            
            if i ==1:
                if mainType ==1:
                    hedgingList = callList
                else:
                    hedgingList = putList 
                if mainDirection==1:
                    hedgingNumber = diffList.index(min(hedgingList))
                else: 
                    hedgingNumber = diffList.index(max(hedgingList))
                    
                hedgingSec = varList[hedgingNumber]
                
                if hedgingNumber !=0:
                    if hedgingNumber%4 == 0 or hedgingNumber%4==3 or tick>=300: 
                        hedgingDelta = self.deltaclac(priceList[hedgingNumber],priceList[0],45+((hedgingNumber-1)/4),maturity2M,realVol,0,(-1)**(1+hedgingNumber))
                    else:
                        hedgingDelta = self.deltaclac(priceList[hedgingNumber],priceList[0],45+((hedgingNumber-1)/4),maturity1M,realVol,0,(-1)**(1+hedgingNumber))
                
                    mainPos = int(2500*hedgingDelta/(mainDelta+hedgingDelta))+1
                    hedgingPos = 2500-mainPos
                    hedgingDirection = -mainDirection
                    
                    strat1 = (mainDirection*(mainPos*diffList[mainNumber] - hedgingPos*diffList[hedgingNumber]) -2*2500*fees)*100
                    if mainDirection ==1:
                        mainDirection = "BUY"
                        hedgingDirection = "SELL"
                        hedgingDirection2 = "SELL"
                    else:
                        mainDirection = "SELL"
                        hedgingDirection = "BUY"
                        hedgingDirection2 = "BUY"
                        
                
                stratDic["strat1"] = {}
                stratDic["strat1"]["name"] = "strat 1"
                stratDic["strat1"]["value"] = strat1
                stratDic["strat1"]["main"] = [mainSec,mainPos,mainDirection,mainNumber]
                stratDic["strat1"]["hedge"] = [hedgingSec,hedgingPos,hedgingDirection,hedgingNumber]
                stratDic["strat1"]["hedge2"] = [hedgingSec2,hedgingPos2,hedgingDirection2,hedgingNumber2]
        
        #begining of strat 2 : 
            elif i ==2:
                
                if mainType ==1:
                    hedgingList = putList
                else:
                    hedgingList = callList 
                if mainDirection==1:
                    hedgingNumber = diffList.index(max(hedgingList))
                else: 
                    hedgingNumber = diffList.index(min(hedgingList))
                
                hedgingSec = varList[hedgingNumber]
                if hedgingNumber !=0:
                    if hedgingNumber%4 == 0 or hedgingNumber%4==3 or tick>=300: 
                        hedgingDelta = self.deltaclac(priceList[hedgingNumber],priceList[0],45+((hedgingNumber-1)/4),maturity2M,realVol,0,(-1)**(1+hedgingNumber))
                    else:
                        hedgingDelta = self.deltaclac(priceList[hedgingNumber],priceList[0],45+((hedgingNumber-1)/4),maturity1M,realVol,0,(-1)**(1+hedgingNumber))
                
                    if mainDelta - hedgingDelta !=0:
                        mainPos = int(abs(1000*hedgingDelta/(mainDelta-hedgingDelta)))
                        hedgingPos = 1000-mainPos
                    else :
                        mainPos = 500
                        hedgingPos = 500 
                    
                    strat2 = (mainDirection*(mainPos*diffList[mainNumber] + hedgingPos*diffList[hedgingNumber]) -2*1000*fees)*100
                    if mainDirection ==1:
                        mainDirection = "BUY"
                        hedgingDirection = "BUY"
                    else:
                        mainDirection = "SELL"
                        hedgingDirection = "SELL"
                else: 
                    strat2 = 0    
                        
                stratDic["strat2"] = {}
                stratDic["strat2"]["name"] = "strat 2"
                stratDic["strat2"]["value"] = strat2
                stratDic["strat2"]["main"] = [mainSec,mainPos,mainDirection,mainNumber]
                stratDic["strat2"]["hedge"] = [hedgingSec,hedgingPos,hedgingDirection,hedgingNumber]
                stratDic["strat2"]["hedge2"] = [hedgingSec2,hedgingPos2,hedgingDirection2,hedgingNumber2]
                
        
        #begining of strat 3 : 
            elif i ==3: 
                hedgingNumber = 0 
                hedgingSec = "RTM"
                hedgingDelta = 1 
                hedgingDirection = -mainDirection*mainType
                
                if mainType ==1:
                    hedgingList = callList
                else:
                    hedgingList = putList 
                if mainDirection==1:
                    hedgingNumber2 = diffList.index(min(hedgingList))
                else: 
                    hedgingNumber2 = diffList.index(max(hedgingList))
                    
                hedgingSec2 = varList[hedgingNumber2]
                hedgingDirection2 = -mainDirection
                if hedgingNumber2 !=0:
                    if hedgingNumber2%4 == 0 or hedgingNumber2%4==3 or tick>=300: 
                        hedgingDelta2 = self.deltaclac(priceList[hedgingNumber2],priceList[0],45+((hedgingNumber2-1)/4),maturity2M,realVol,0,(-1)**(1+hedgingNumber2))
                    else:
                        hedgingDelta2 = self.deltaclac(priceList[hedgingNumber2],priceList[0],45+((hedgingNumber2-1)/4),maturity1M,realVol,0,(-1)**(1+hedgingNumber2))
                
                    mainPos1 = int(min(999.9,abs(500/mainDelta)))+1
                    hedgingPos = int(min(50000,abs(100*mainPos1*mainDelta)))
                    
                    if (absDiffList[mainNumber]-absDiffList[hedgingNumber2])>0: # if buy more with a non-optimal hedge is profitable  
                        hedgingPos2 = abs(int((2500-mainPos1)*mainDelta/(hedgingDelta2+mainDelta)))
                        mainPos = 2500-hedgingPos2       
                    
                    strat3 = (mainDirection*(mainPos*diffList[mainNumber]- hedgingPos2*diffList[hedgingNumber2])-2*2500*fees)*100 - 2*fees*hedgingPos
                    
                    if mainDirection ==1:
                        mainDirection = "BUY"
                        hedgingDirection = "SELL"
                        hedgingDirection2 = "SELL"
                    else:
                        mainDirection = "SELL"
                        hedgingDirection = "BUY"
                        hedgingDirection2 = "BUY"
                
                            
                stratDic["strat3"] = {}
                stratDic["strat3"]["name"] = "strat 3"
                stratDic["strat3"]["value"] = strat3
                stratDic["strat3"]["main"] = [mainSec,mainPos,mainDirection,mainNumber]
                stratDic["strat3"]["hedge"] = [hedgingSec,hedgingPos,hedgingDirection,hedgingNumber]
                stratDic["strat3"]["hedge2"] = [hedgingSec2,hedgingPos2,hedgingDirection2,hedgingNumber2]
                    
        # print(stratDic)
        # print("Main : ", stratDic["strat3"]["main"][0],diffList[stratDic["strat3"]["main"][3]],stratDic["strat3"]["main"][1],stratDic["strat3"]["main"][2],mainDelta)
        # print("Hedge strat1 : ", stratDic["strat1"]["hedge"][0],diffList[stratDic["strat1"]["hedge"][3]],stratDic["strat1"]["hedge"][1],stratDic["strat1"]["hedge"][2])
        # print("Hedge strat2 : ", stratDic["strat2"]["hedge"][0],diffList[stratDic["strat2"]["hedge"][3]],stratDic["strat2"]["hedge"][1],stratDic["strat2"]["hedge"][2])
        # print("Hedge strat3 : ", stratDic["strat3"]["hedge"][0],diffList[stratDic["strat3"]["hedge"][3]],stratDic["strat3"]["hedge"][1],stratDic["strat3"]["hedge"][2])
        # print("Hedge2 strat3 : ", stratDic["strat3"]["hedge2"][0],diffList[stratDic["strat3"]["hedge2"][3]],stratDic["strat3"]["hedge2"][1],stratDic["strat3"]["hedge2"][2])
        # print("")
        # print(diffList)
        # print("")
        if strat1 == max(strat1,strat2,strat3):
            return stratDic["strat1"]
        elif strat2 == max(strat1,strat2,strat3):
            return stratDic["strat2"]
        elif strat3 == max(strat1,strat2,strat3):
            return stratDic["strat3"]
        
        return None

    def changeStrat(self,changeValue,varList,optimalStrat,oldStrat,oldOptimalStrategyValue):
        
        posList = [0]
        secList = [0]
        directionList =[0]
        absPosList = [0]
        nList = [0]
        if  oldOptimalStrategyValue < 8000  or (tick > 295 and tick <305) :
           #and (optimalStrat["main"][0]!=oldStrat["main"][0]) and (optimalStrat["main"][0]!=oldStrat["hedge"][0]
            securities = self.getSecurities()
            pos ={security:securities[security]["position"] for security in securities.keys()}
            for i in range(0,len(varList)):
                if pos[varList[i]]!=0:
                    posList.extend([pos[varList[i]]])
                    absPosList.extend([abs(pos[varList[i]])])
                    secList.extend([varList[i]])
                    directionList.extend(["BUY" if pos[varList[i]]<0 else "SELL"])
                    nList.extend([(int(abs(pos[varList[i]])/100)+1) if i!=0 else (int(abs(pos[varList[i]])/10000)+1)])
            
        
            while max(absPosList)>0:
                for i in range(0,len(posList)): 
                    
                    if secList[i] != "RTM":
                        if absPosList[i]>=100:
                            self.postOrder(directionList[i],secList[i],100)
                            absPosList[i] -=100
                            
                        else : 
                            if absPosList[i]>0:
                                self.postOrder(directionList[i],secList[i],int(absPosList[i]))
                                absPosList[i] = 0
                                
                    else:
                        if absPosList[i]>=10000:
                            self.postOrder(directionList[i],secList[i],10000)
                            absPosList[i] -= 10000
                                
                        else : 
                            if absPosList[i]>0:
                                self.postOrder(directionList[i],secList[i],int(absPosList[i]))
                                absPosList[i]=0
                    time.sleep(0.1)   
                # oldPosList = posList  
                # posList = [0] 
                # absPosList= [0]
                # secList = [0]
                # directionList = [0]
                # pos ={security:securities[security]["position"] for security in securities.keys()}
                
                # for i in range(0,len(varList)):
                #     if pos[varList[i]]!=0:
                #         posList.extend([pos[varList[i]]])
                #         absPosList.extend([abs(pos[varList[i]])])
                #         secList.extend([varList[i]])
                #         directionList.extend(["BUY" if pos[varList[i]]<0 else "SELL"])                
                # print(directionList)
                # time.sleep(0.2)        
                
            # if way >=0 :                          
                    
            #     while min(posList) !=0 or RTMpos !=0:
            #         for i in range(0,len(posList)):
            #             if posList[i]<0:
            #                 if absPosList[i]>=100:
            #                     self.postOrder(directionList[i],secList[i],100)
            #                     absPosList[i] -= 100 
            #                     posList[i] += 100
            #                 else : 
            #                     if absPosList[i]>0:
            #                         self.postOrder(directionList[i],secList[i],absPosList[i])
            #                         absPosList[i] =0
            #                     posList[i]=0
            #             if pos[varList[0]] < 0 :        
            #                 if RTMpos<=-10000:
            #                         self.postOrder("BUY","RTM",10000)
            #                         RTMpos +=10000
            #                 else : 
            #                     if RTMpos < 0:
            #                         self.postOrder("BUY","RTM",-RTMpos)
            #                         RTMpos =0
                            
            #     while max(posList) !=0 or RTMpos !=0:
            #         for i in range(0,len(posList)):
            #             if posList[i]>0:
            #                 if absPosList[i]>=100:
            #                     self.postOrder(directionList[i],secList[i],100)
            #                     absPosList[i] -= 100 
            #                     posList[i] -= 100
            #                 else : 
            #                     if absPosList[i]>0:
            #                         self.postOrder(directionList[i],secList[i],absPosList[i])
            #                         absPosList[i] =0
            #                     posList[i]=0
            #         if pos[varList[0]] > 0 :        
            #                 if RTMpos>=10000:
            #                         self.postOrder("SELL","RTM",10000)
            #                         RTMpos -=10000
            #                 else : 
            #                     if RTMpos >0:
            #                         self.postOrder("SELL","RTM",RTMpos)
            #                         RTMpos =0
            # else :
            #     while max(posList) !=0 or RTMpos !=0:
            #         for i in range(0,len(posList)):
            #             if posList[i]>0:
            #                 if absPosList[i]>=100:
            #                     self.postOrder(directionList[i],secList[i],100)
            #                     absPosList[i] -= 100 
            #                     posList[i] -= 100
            #                 else : 
            #                     if absPosList[i]>0:
            #                         self.postOrder(directionList[i],secList[i],absPosList[i])
            #                         absPosList[i] =0
            #                     posList[i]=0
            #             if pos[varList[0]] > 0 :        
            #                 if RTMpos>=10000:
            #                         self.postOrder("SELL","RTM",10000)
            #                         RTMpos -=10000
            #                 else : 
            #                     if RTMpos >0:
            #                         self.postOrder("SELL","RTM",RTMpos)
            #                         RTMpos =0          
            #     while min(posList) !=0:
            #         for i in range(0,len(posList)):
            #             if posList[i]<0:
            #                 if absPosList[i]>=100:
            #                     self.postOrder(directionList[i],secList[i],100)
            #                     absPosList[i] -= 100 
            #                     posList[i] += 100
            #                 else : 
            #                     if absPosList[i]>0:
            #                         self.postOrder(directionList[i],secList[i],absPosList[i])
            #                         absPosList[i] =0
            #                     posList[i]=0
            #             if pos[varList[0]] < 0 :        
            #                 if RTMpos<=-10000:
            #                         self.postOrder("BUY","RTM",10000)
            #                         RTMpos +=10000
            #                 else : 
            #                     if RTMpos < 0:
            #                         self.postOrder("BUY","RTM",-RTMpos)
            #                         RTMpos =0
                            
            if optimalStrat["value"] >10000 :  
                    
                print("strategy change")
                print(optimalStrat["value"])
                print(changeValue)
                
                targetMain = optimalStrat["main"][1]
                targetHedge = optimalStrat["hedge"][1]
                targetHedge2 = optimalStrat["hedge2"][1]
                k = int(max(targetMain,targetHedge,targetHedge2)/100)+1
                for i in range(0,k):
                    if targetMain>=100:
                        self.postOrder(optimalStrat["main"][2],optimalStrat["main"][0],100)
                        targetMain = targetMain- 100
                        
                    elif targetMain<100 : 
                        if targetMain>0:
                            self.postOrder(optimalStrat["main"][2],optimalStrat["main"][0],int(targetMain))
                            
                            targetMain = 0  
                    if targetHedge2>=100:
                        self.postOrder(optimalStrat["hedge2"][2],optimalStrat["hedge2"][0],100)
                        
                        targetHedge2 -= 100
                    else : 
                        if targetHedge2>0:
                            self.postOrder(optimalStrat["hedge2"][2],optimalStrat["hedge2"][0],int(targetHedge2))
                            
                            targetHedge2 = 0                 
                    if optimalStrat["hedge"][3]!=0:
                        if targetHedge>=100:
                            self.postOrder(optimalStrat["hedge"][2],optimalStrat["hedge"][0],100)
                            
                            targetHedge -= 100
                        else : 
                            if targetHedge>0:
                                self.postOrder(optimalStrat["hedge"][2],optimalStrat["hedge"][0],int(targetHedge))
                                targetHedge = 0  
                                
                    else: 
                        if targetHedge>=10000:
                            self.postOrder(optimalStrat["hedge"][2],optimalStrat["hedge"][0],10000)
                            targetHedge -= 10000
                            
                        else : 
                            if targetHedge>0:
                                self.postOrder(optimalStrat["hedge"][2],optimalStrat["hedge"][0],int(targetHedge))
                                targetHedge = 0
                                
                    time.sleep(0.1)
            
            
            
                                
                        
 
if __name__ == "__main__":
    app = MyTradingApp("9999", "0CEN4JP9")
    realVol = app.newsExtract(2)  
    varList = app.varList()
    k =len(varList)
    priceList = [0]*k
    theoPriceList=[0]*k
    diffList = [0]*k 
    absDiffList = [0]*k 
    callList = [0]*int((k-1)/2)
    putList = [0]*int((k-1)/2)
    fees = 0.02
    hedgingSec2 = 0
    hedgingPos2 = 0 
    hedgingDelta2 = 0  
    hedgingNumber2 = 0
    hedgingDirection2 =0
    deltalimit = app.newsExtract(0) * 0.98
    quantityList = [0]*k
    oldOptimalStrategy = {'name': 0, 'value': 0, 'main': [0, 0, 0, 0], 'hedge': [0, 0, 0, 0], 'hedge2': [0, 0, 0, 0]}
    v = 0
    while True:
        tick =app.currentAbsoluteTick()
        
        if tick <298 or tick>302:
            maturity1M = (300-tick)/3600
            maturity2M = (600-tick)/3600
            posList=[]
            nList=[]
            secList=[]
            if tick >300 and tick <305: # refresh list of secuities when the 1st month option expires
                varList = app.varList() 
                
                k =len(varList)
                priceList = [0]*k
                posList = [0]*k
                theoPriceList=[0]*k
                diffList = [0]*k
                absDiffList = [0]*k
                callList = [0]*((k-1)/2)
                putList = [0]*((k-1)/2) 
            
            if tick >= 38:
                realVol = app.newsExtract(1) # extract the last news info about annualized volatility
            
            quantityList[0]=app.getSecurities(varList[0])[0]["position"]         
            priceList[0]= app.price(varList[0],2) # RTM price
            absDiffList[0]= -2*fees
            for i in range(1,k): # price list, theorical price list, differences list, call List and put list
                priceList[i]= app.price(varList[i],2)
                if (i%4 == 3 or i%4 ==0) or tick>=300 :
                    theoPriceList[i]=app.black_scholes(priceList[0],45+int((i-1)/4),maturity2M,0,realVol,(-1)**(1+i)) 
                else: 
                    theoPriceList[i]=app.black_scholes(priceList[0],(45+int((i-1)/4)),maturity1M,0,realVol,((-1)**(1+i)))
                quantityList[i] = app.getSecurities(varList[i])[0]["position"]      
                diffList[i] = theoPriceList[i]-priceList[i]
                absDiffList[i] = abs(diffList[i])-2*fees
                if i%2==1:
                    callList[int((i+1)/2)-1]=diffList[i]
                else:
                    putList[int(i/2)-1]=diffList[i]
            
          
             
            optimalStrategy = app.bestStrategy(varList,priceList,diffList,absDiffList,callList,putList,maturity1M,maturity2M,realVol,tick,fees,oldOptimalStrategy)
            oldOptimalStrategyValue = app.oldBestStrategy(varList,priceList,diffList,absDiffList,callList,putList,maturity1M,maturity2M,realVol,tick,fees,oldOptimalStrategy)
            changeValue= optimalStrategy["value"]-oldOptimalStrategyValue
            app.changeStrat(changeValue,varList,optimalStrategy,oldOptimalStrategy,oldOptimalStrategyValue)
            
            # if oldOptimalStrategy["main"][0] != optimalStrategy["main"][0] :
            print(oldOptimalStrategy)
            print(optimalStrategy)
            print(changeValue)
              
            oldOptimalStrategy = optimalStrategy
            
            
            
            
       

    
        