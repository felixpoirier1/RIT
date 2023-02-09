import requests
import pandas as pd
from colored import fg, bg, attr
import time
import multiprocessing as mp

                                                

############### Trading App class ###############

class TradingApp():
    def __init__(self, host, API_KEY):
        self.host = str(host)
        print(f"{fg(2)}Program started with host and API KEY : {attr(1)}{host} {API_KEY}{attr(0)}")
        

        self.host = host
        self.url = 'http://localhost:' + host + '/v1'

        self.number = mp.Value('i', 0)
        self.latestBid = {}
        self.latestAsk = {}
        self.tickers = []
        self.API_KEY = {'X-API-Key': API_KEY}
        self.getCaseDetails()
        self.getTraderDetails()
        self.getTradingLimits()
        self.getAssets()
        self.getSecurities()
        self.trading_limit = None
        
        self.securities_book = {}
        self.securities_history = {}
        self.securities_tas = {}

    
    def getCaseDetails(self):
        case = requests.get(self.url + '/case', headers=self.API_KEY).json()
        self.period = case["period"]
        self.tick = case["tick"]
        self.total_periods = case["total_periods"]

        
    def getTraderDetails(self):
        trader = requests.get(self.url + '/trader', headers=self.API_KEY).json()
        self.trader_id = trader["trader_id"]
        self.first_name = trader["first_name"]
        self.last_name = trader["last_name"]

    def getTradingLimits(self):
        limits = requests.get(self.url + '/limits', headers=self.API_KEY).json()
        self.limits = {}
        for asset in limits:
            name = asset["name"]
            del asset["name"]
            self.limits[name] = asset

    def getNews(self, since : int, limit: int, return_latest : bool = True) -> dict:
        news_head = {'since':since, 'limit':limit}
        self.news = requests.get(self.url + '/news', headers=self.API_KEY, params=news_head).json()
        
        if return_latest:
            return self.news[-1]
        else:
            return self.news

    def getAssets(self, ticker : str = None):
        if ticker == None:
            self.assets = requests.get(self.url + '/assets', headers=self.API_KEY).json()
            return self.assets
        else:
            asset_head = {'ticker': ticker}
            asset = requests.get(self.url + '/asset', headers=self.API_KEY, params=asset_head).json()
            return asset

        
    def getAssetsHistory(self, ticker: str, period: int = None, limit: int = None):
        if ((period == None) and (limit == None)):
            assets_history_head = {'ticker': ticker}
            assetshistory = requests.get(self.url + '/assets/history', headers=self.API_KEY, params=assets_history_head).json()


        # JC programme la methode comme tu veux, tu es le seul qui en aura de besoin ("NG")
    
    def getSecurities(self, ticker : str = None):
        """Retrieves a dictionary of all securities with their name as key and their data as value

        Parameters
        ----------
        ticker : str, optional
            The name of the security, by default all securities

        Returns
        -------
        dict
            dictionary of all securities with their name as key and their data as value
        """
        if ticker == None :
            securities = requests.get(self.url + '/securities', headers=self.API_KEY).json()
            self.tickers_name = []
            print(self.tickers_name)
            self.tickers_data = {}
            for security in securities:
                name = security["ticker"]
                del security["ticker"]
                self.tickers_name += [name]
                self.tickers_data[name] = security
           
            return self.tickers_data
    
    def getSecuritiesBook(self, ticker: str, limit : int = None):
        """Returns the security book which is a dataframe of bid and asks for a specific period

        Parameters
        ----------
        ticker : str
            The name of the security
        limit : int, optional
            Maximum number of orders to return for each side of the order book. by default 20

        Returns
        -------
        dict        
            dictionary with two keys "bids" and "asks" which are dataframes of bids and asks
        """
        assert ticker in self.tickers_name
        security_book_head = {'ticker': ticker, 'limit': limit}
        securitybook = requests.get(self.url + '/securities/book', headers=self.API_KEY, params=security_book_head).json()

        return {
            "bids" : 
                pd.DataFrame(securitybook["bids"]).set_index("order_id").sort_values("price", ascending=False), 
            "asks": 
                pd.DataFrame(securitybook["asks"]).set_index("order_id").sort_values("price", ascending=True)
            }
    
    def getSecuritiesHistory(self, ticker : str, period : int = None, limit : int = None):
        """Fetches the trading history of a given security for a given period of time or a given number of trades.

        Parameters
        ----------
        ticker : str
            The name of the security
        period : int, optional
            The period where data must be fetched from, by default current period
        limit : int, optional
            Amount of trades to record starting from current tick, by default equal to tick
        """
        assert ticker in self.tickers_name
        security_history_head = {'ticker': ticker, 'period' : period, 'limit': limit}
        securityhistory = requests.get(self.url + '/securities/history', headers=self.API_KEY, params=security_history_head).json()
        
        self.securities_history[ticker] = pd.DataFrame(securityhistory)

    def getSecuritiesTas(self, ticker : str, after : int = None, period : int = None, limit : int = None):
        """Reutrns all  trades that were filled by all the participants for a given security

        Parameters
        ----------
        ticker : str
            The name of the security
        after : int, optional
            The starting tick, by default first tick of the period
        period : int, optional
            The period where data must be fetched from, by default current period
        limit : int, optional
            Amount of trades to record starting from current tick, by default equal to tick
        """
        assert ticker in self.tickers_name
        security_tas_head = {'ticker': ticker, 'after': after, 'period': after, 'limit': after}
        securitytas = requests.get(self.url + '/securities/tas', headers=self.API_KEY, params=security_tas_head).json()
        
        self.securities_tas[ticker] = pd.DataFrame(securitytas)
        self.securities_tas[ticker].set_index("id", inplace=True)
    

    def getOrders(self, status : str = None):
        """Returns a list of all orders

        Parameters
        ----------
        status : str, optional
            The status of the orders to return, by default all OPEN orders

        Returns
        -------
        list
            list of all orders
        """
        orders_head = {'status': status}
        self.orders = requests.get(self.url + '/orders', headers=self.API_KEY, params=orders_head).json()
        
        return self.orders

    def postOrder(self, action : str, ticker : str, quantity : int, price : float = None, type : str = "MARKET"):
        """This method sends a post request with the order to the server

        Parameters
        ----------
        action : str
            "BUY" or "SELL"
        ticker : str
            The name of the security
        quantity : int
            The quantity of shares in the order
        price : float
            The price per share of the order (only if type is "LIMIT")
        type : str, optional
            "LIMIT" or "MARKET", by default "MARKET"
        """
        assert action in ["BUY", "SELL"]
        assert type in ["LIMIT", "MARKET"]
        assert ticker in self.tickers_name
        assert quantity > 0

        if price is None:
            assert type == "MARKET"
        else:
            assert type == "LIMIT"
            assert price > 0

        order_head = {'ticker': ticker, 'quantity': quantity, 'type': type, 'action': action, 'price': price}
        order_ = requests.post(self.url + '/orders', headers=self.API_KEY, params=order_head)
        order = order_.json()

        if order_.status_code == 200:
            print(f"{type} {action} order for {ticker} was placed for {quantity} shares at {price}$ per share")
            return order

        elif order_.status_code==401:
            print(f"Order for {ticker} is unauthorized")
            return None
        
        elif order_.status_code==429:
            print(f"Order for {ticker} was declined wait {order['wait']} seconds before trying again")
            return order

    
    def getOrder(self, order_id : str):
        """Returns the order with the given id

        Parameters
        ----------
        order_id : str
            The id of the order

        Returns
        -------
        dict
            The order with the given id
        """
        order_head = {'id': order_id} 
        order = requests.get(self.url + '/orders', headers=self.API_KEY, params=order_head).json()
        return order

    def deleteOrder(self, order_id : str):
        """Deletes the order with the given id

        Parameters
        ----------
        order_id : str
            The id of the order
        """
        order_head = {'id': order_id} 
        order = requests.delete(self.url + '/orders', headers=self.API_KEY, params=order_head).json()
        return order
    
    def getTenders(self):
        """Returns a list of all tenders

        Returns
        -------
        list
            list of all tenders
        """
        tenders = requests.get(self.url + '/tenders', headers=self.API_KEY).json()
        for tender in tenders:
            name = tender["tender_id"]
            del tender["tender_id"]
            self.tenders[name] = tender

        return self.tenders



        

if __name__ == "__main__":
    print("Hello World")