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



