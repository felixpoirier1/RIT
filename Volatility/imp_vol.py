import numpy as np
from scipy.stats import norm

def newton_impl_vol(S, K, T, Price, r, sigma,IsCall):
# S, option price
# K Strike price
# T maturity
# Price, price of the underlying asset
# r risk free 
#sigma start volatility
#IsCall , 1 for a call and -1 for a put

    tolerance = 0.000001
    i = 0
    fx= 100  
    while (abs(Price - fx) > tolerance) or (i>200) :
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1-sigma*np.sqrt(T)
        fx = IsCall*S * norm.cdf(IsCall*d1, 0.0, 1.0) - IsCall*K * np.exp(-r * T) * norm.cdf(IsCall*d2, 0.0, 1.0) 
        vega = (1 / np.sqrt(2 * np.pi)) * S * np.sqrt(T) * np.exp(-(norm.cdf(d1, 0.0, 1.0) ** 2) * 0.5)  
        sigma = sigma + (fx - Price)/ vega
        i+=1
    return abs(sigma)
