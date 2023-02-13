from scipy.stats import norm
from math import log, sqrt, exp


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
        price_diff = black_scholes(S, K, T, r, sigma, IsCall) - price
        if abs(price_diff) < tolerance:
            if delta==None:
                return sigma
            else:
                return norm.cdf((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))) + 1*min(0,IsCall)
        sigma -= price_diff / vega
    
    return None


def var_list(month):
    """This method returns the list of indices for month 1 or month 2

        Parameters
        ----------
        months : int
            1 for the first month """
            
    nb_var = 11
    list_var=[40]
    list_var[0]="RTM"
    if month ==1 :
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

     
def price(self,ticker,type):
    """This method sends the bid/ask price of a ticker

        Parameters
        ----------
        type : int
            0 for bid price, 1 for ask price"""
            
    if __name__ == "__main__": 
        app=TradingApp("9999","EG6SMVYC") # La fonction doit rentrer dans le classe trading app. 
        list_var = var_list(1)
        dic_var ={}
        for i in range(0,len(list_var)):
            bid = TradingApp.getSecuritiesBook(app,list_var[i]).get("bids")["price"]
            ask = TradingApp.getSecuritiesBook(app,list_var[i]).get("asks")["price"]
            dic_var[list_var[i]]=[bid,ask]
    return dic_var[ticker][type]

