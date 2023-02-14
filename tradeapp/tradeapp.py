import requests
import pandas as pd
from colored import fg, bg, attr
import logging 
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

# Define color codes for each logging level
LOG_COLORS = {
    logging.DEBUG: '\033[36m',  # cyan
    logging.INFO: '\033[32m',  # green
    logging.WARNING: '\033[33m',  # yellow
    logging.ERROR: '\033[31m',  # red
    logging.CRITICAL: '\033[35m',  # magenta
}



############### Trading App class ###############

class TradingApp():
    logger = logging.getLogger('tradeapp')

    def __init__(self, host, API_KEY):
        self.host = str(host)
        self.logger.info(f"Program started with host and API KEY : {str(host)} {str(API_KEY)}")
        

        self.host = host
        self.url = 'http://localhost:' + host + '/v1'

        self.latestBid = {}
        self.latestAsk = {}
        self.tickers = []
        self.API_KEY = {'X-API-Key': API_KEY}
        self.getCaseDetails()
        self.getTraderDetails()
        self.getTradingLimits()
        self.getAssets()
        self.getSecurities()
        
        self.securities_book = {}
        self.securities_history = {}
        self.securities_tas = {}
    
    def getCaseDetails(self):
        """Gets the case details from the API and stores them in the class attributes. (period, tick & total_periods)
        """
        case = requests.get(self.url + '/case', headers=self.API_KEY).json()
        self.period = case["period"]
        self.tick = case["tick"]
        self.total_periods = case["total_periods"]

        return case

        
    def getTraderDetails(self):
        """Gets the trader details from the API and stores them in the class attributes. (trader_id, first_name & last_name)
        """
        trader = requests.get(self.url + '/trader', headers=self.API_KEY).json()
        self.trader_id = trader["trader_id"]
        self.first_name = trader["first_name"]
        self.last_name = trader["last_name"]

        return trader

    def getTradingLimits(self):
        """Gets the trading limits from the API and stores them in the class attributes. (limits)
        """
        limits = requests.get(self.url + '/limits', headers=self.API_KEY).json()
        self.limits = {}
        for asset in limits:
            name = asset["name"]
            del asset["name"]
            self.limits[name] = asset
        
        return self.limits

    def getNews(self, since : int = 0, limit: int = None, return_latest : bool = True) -> dict:
        """Gets the news from the API and stores them in the class attributes. (news)

        Parameters
        ----------
        since : int, optional
            Retrieve only news items after a particular news id.
        limit : int, optional
            Limit the number of news items returned.
        return_latest : bool, optional
            Only get newest news, by default True

        Returns
        -------
        dict
            dictionnary of news
        """
        news_head = {'since':since, 'limit':limit}
        self.news = requests.get(self.url + '/news', headers=self.API_KEY, params=news_head).json()
        
        if return_latest:
            return self.news[-1]
        else:
            return self.news

    def getAssets(self, ticker : str = None) -> dict:
        """Gets the assets from the API and stores them in the class attributes. (assets)

        Parameters
        ----------
        ticker : str, optional
            Only get specific asset, by default None

        Returns
        -------
        dict
            dictionnary of assets
        """
        if ticker == None:
            self.assets = requests.get(self.url + '/assets', headers=self.API_KEY).json()
            return self.assets
        else:
            asset_head = {'ticker': ticker}
            asset = requests.get(self.url + '/asset', headers=self.API_KEY, params=asset_head).json()
            return asset

        
    def getAssetsHistory(self, ticker: str, period: int = None, limit: int = None):
        """_summary_

        Parameters
        ----------
        ticker : str
            _description_
        period : int, optional
            _description_, by default None
        limit : int, optional
            _description_, by default None
        """
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
            self.tickers_data = {}
            for security in securities:
                name = security["ticker"]
                del security["ticker"]
                self.tickers_name += [name]
                self.tickers_data[name] = security
           
            return self.tickers_data
        
        else:
            security_head = {'ticker': ticker}
            security = requests.get(self.url + '/securities', headers=self.API_KEY, params=security_head).json()
            return security
    
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

        return self.securities_history[ticker]

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

    def postOrder(self, action : str, ticker : str, quantity : int, price : float = None, type : str = "MARKET", ignore_limit : bool = False):
        """This method sends a post request with the order to the server

        Parameters
        ----------
        action : str
            "BUY" or "SELL"
        ticker : str
            The name of the security
        quantity : int
            The quantity of shares in the order
        price : float, optional
            The price per share of the order (only if type is "LIMIT")
        type : str, optional
            "LIMIT" or "MARKET", by default "MARKET"
        ignore_limit : bool, optional
            If True, no error will be given even if the quantity is greater than the net limit, by default False
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

        if (order_.status_code == 200):
            if type == "LIMIT":
                self.logger.info(f"{type} {action} order for {ticker} was placed for {quantity} shares at {price}$ per share")
            else:
                self.logger.info(f"{type} {action} order for {ticker} was placed for {quantity} shares")
            return order

        elif (order_.status_code == 401):
            self.logger.info(f"Order for {ticker} is unauthorized")
            return None
        
        elif (order_.status_code == 429):
            self.logger.info(f"Order for {ticker} was declined wait {order['wait']} seconds before trying again")
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
        order_ = requests.delete(self.url + '/orders', headers=self.API_KEY, params=order_head)
        order = order_.json()

        if order_.status_code == 200:
            self.logger.info(f"Order {order_id} was successfully deleted")
            return order
        
        elif order_.status_code==401:
            self.logger.info(f"Order {order_id} is unauthorized")
            return None
    
    def getTenders(self):
        """Returns a list of all tenders

        Returns
        -------
        list
            list of all tenders
        """
        tenders_ = requests.get(self.url + '/tenders', headers=self.API_KEY)
        tenders = tenders_.json()
        
        if len(tenders) == 0:
                return None
        
        self.tenders = {}
        if tenders_.status_code == 200:
            for tender in tenders:
                name = tender["tender_id"]
                del tender["tender_id"]
                self.tenders[name] = tender
            
            return self.tenders
        
        elif tenders_.status_code == 401:
            self.logger.info("Unauthorized")
            return None

    def postTender(self, id : int, accept : bool = True, price : float = None):
        """Accepts or declines a tender

        Parameters
        ----------
        id : int
            The id of the tender
        accept : bool, optional
            If False, the tender will not be accepted, by default True
        price : float, optional
            The price per share to accept the tender at, by default None
        """
        if accept:
            tender_head = {'id': id}
            print(tender_head)
            tender = requests.post(self.url + '/tenders', headers=self.API_KEY, params=tender_head)
            print(tender.json())

        else:
            tender_head = {'id': id}
            tender = requests.delete(self.url + '/tenders', headers=self.API_KEY, params=tender_head)
        
        if tender.status_code == 200:
            self.logger.info(f"Tender {id} was accepted")
        
        elif tender.status_code == 401:
            self.logger.info(f"Tender {id} is unauthorized")

        return tender.status_code

    def getLeases(self):
        """Returns a list of all leases

        Returns
        -------
        list
            list of all leases
        """
        leases_ = requests.get(self.url + '/leases', headers=self.API_KEY)
        leases = leases_.json()
        
        if len(leases) == 0:
                return None
        
        self.leases = {}
        if leases_.status_code == 200:
            for lease in leases:
                name = lease["lease_id"]
                del lease["lease_id"]
                self.leases[name] = lease
            
            return self.leases
        
        elif leases_.status_code == 401:
            self.logger.warning("Unauthorized")
            return None


        

if __name__ == "__main__":
    print("Hello World")