import requests
import pandas as pd
from colored import fg, bg, attr
import logging 
import logging.config
import time

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
    class_name = "TradingApp"

    def __init__(self, host, API_KEY):
        self.host = str(host)
        self.logger.info(f"Program started with host and API KEY : {str(host)} {str(API_KEY)}")
        

        self.host = host
        self.url = 'http://localhost:' + host + '/v1'

        self.latestBid = {}
        self.latestAsk = {}
        self.tickers = []
        self.API_KEY = {'X-API-Key': API_KEY}
        try:
            self.getCaseDetails()
        except requests.exceptions.ConnectionError:
            raise(ConnectionError(f"Connection not established Please verifiy that RIT is open and that the host & API key ({self.host} {self.API_KEY['X-API-Key']}) are correct."))
        self.getTraderDetails()
        self.getTradingLimits()
        self.getAssets()
        self.getSecurities()
        
        self.securities_book = {}
        self.securities_history = {}
        self.securities_tas = {}

    def currentTick(self) -> int:
        """Returns the current tick of the trading period. If the period is over, it will call the getCaseDetails method to update the period, tick & total_periods attributes and then call itself again to return the current tick.

        Returns
        -------
        int
            The current tick of the trading period.
        """
        self.logger.debug(f"Method currentTick called from {self.class_name} class")
        now = time.time()

        if now - self.starttime < self.ticks_per_period:
            self.logger.debug("Total periods reached, returning None")
            return int(round(now - self.starttime, 0))
        else:
            self.getCaseDetails()
            if self.tick != None:
                self.starttime = time.time() - self.tick
            else:
                time.sleep(1)
                return self.currentTick()
        
    def getAbsoluteTick(self) -> int:
        """Returns the current tick of the all trading periods. If the period is over, it will call the getCaseDetails method to update the period, tick & total_periods attributes and then call itself again to return the current tick.

        Returns
        -------
        int
            The current tick of the trading periods.
        """
        self.logger.debug(f"Method currentAbsoluteTick called from {self.class_name} class")
        tick = self.currentTick()
        return (self.period - 1) * self.ticks_per_period + tick


    def getCaseDetails(self) -> dict:
        """Gets the case details from the API and stores them in the class attributes. (period, tick & total_periods)

        Returns
        -------
        dict
            The case details.
        """
        self.logger.debug(f"Method getCaseDetails called from {self.class_name} class")
        case = requests.get(self.url + '/case', headers=self.API_KEY).json()
        self.period = case["period"]
        self.tick = case["tick"]
        if self.tick == 0:
            self.tick = None
        else:
            self.starttime = time.time() - self.tick
        self.total_periods = case["total_periods"]
        self.ticks_per_period = case["ticks_per_period"]
        self.logger.debug(f"Case details : period {self.period}, tick {self.tick}, total_periods {self.total_periods}")

        return case

        
    def getTraderDetails(self) -> dict:
        """Gets the trader details from the API and stores them in the class attributes. (trader_id, first_name & last_name)

        Returns
        -------
        dict
            The trader details.
        """
        self.logger.debug(f"Method getTraderDetails called from {self.class_name} class")
        trader = requests.get(self.url + '/trader', headers=self.API_KEY).json()
        self.trader_id = trader["trader_id"]
        self.first_name = trader["first_name"]
        self.last_name = trader["last_name"]
        self.logger.debug(f"Trader details : trader_id {self.trader_id}, first_name {self.first_name}, last_name {self.last_name}")

        return trader

    def getTradingLimits(self):
        """Gets the trading limits from the API and stores them in the class attributes. (limits)
        """
        self.logger.debug(f"Method getTradingLimits called from {self.class_name} class")
        limits = requests.get(self.url + '/limits', headers=self.API_KEY).json()
        self.limits = {}
        for asset in limits:
            name = asset["name"]
            del asset["name"]
            self.limits[name] = asset
        self.logger.debug(f"Trading limits called and created : self.limits which contains {'assets' if len(self.limits) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getNews called from {self.class_name} class with parameters since={since}, limit={limit}, return_latest={return_latest}")
        news_head = {'since':since, 'limit':limit}
        self.news = requests.get(self.url + '/news', headers=self.API_KEY, params=news_head).json()

        self.logger.debug(f"News called and created : self.news which contains {'news' if len(self.news) !=0 else 'nothing'}")

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
        self.logger.debug(f"Method getAssets called from {self.class_name} class with parameters ticker={ticker}")
        if ticker == None:
            self.assets = requests.get(self.url + '/assets', headers=self.API_KEY).json()
            self.logger.debug(f"Assets called and created : self.assets which contains {'assets' if len(self.assets) !=0 else 'nothing'}")
            return self.assets
        else:
            asset_head = {'ticker': ticker}
            asset = requests.get(self.url + '/asset', headers=self.API_KEY, params=asset_head).json()
            self.logger.debug(f"Asset called and created : self.asset which contains {'asset' if len(asset) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getAssets called from {self.class_name} class with parameters ticker={ticker}, period={period}, limit={limit}")
        if ((period == None) and (limit == None)):
            assets_history_head = {'ticker': ticker}
            assetshistory = requests.get(self.url + '/assets/history', headers=self.API_KEY, params=assets_history_head).json()

        self.logger.debug(f"Assets history called and created : self.assetshistory which contains {'assets history' if len(assetshistory) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getSecurities called from {self.class_name} class with parameter ticker={ticker}")
        if ticker == None :
            securities = requests.get(self.url + '/securities', headers=self.API_KEY).json()
            self.tickers_name = []
            self.tickers_data = {}
            for security in securities:
                name = security["ticker"]
                del security["ticker"]
                self.tickers_name += [name]
                self.tickers_data[name] = security

            self.logger.debug(f"Securities called and created : self.tickers_name which contains {'tickers' if len(self.tickers_name) !=0 else 'nothing'} and self.tickers_data which contains {'tickers data' if len(self.tickers_data) !=0 else 'nothing'}")
            return self.tickers_data
        
        else:
            security_head = {'ticker': ticker}
            security = requests.get(self.url + '/securities', headers=self.API_KEY, params=security_head).json()
            self.logger.debug(f"Security called and created : self.security which contains {'security' if len(security) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getSecuritiesBook called from {self.class_name} class with parameters ticker={ticker}, limit={limit}")
        assert ticker in self.tickers_name
        security_book_head = {'ticker': ticker, 'limit': limit}
        securitybook = requests.get(self.url + '/securities/book', headers=self.API_KEY, params=security_book_head).json()
        self.logger.debug(f"Security book called and created : self.securitybook which contains {'security book' if len(securitybook) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getSecuritiesHistory called from {self.class_name} class with parameters ticker={ticker}, period={period}, limit={limit}")
        assert ticker in self.tickers_name
        security_history_head = {'ticker': ticker, 'period' : period, 'limit': limit}
        securityhistory = requests.get(self.url + '/securities/history', headers=self.API_KEY, params=security_history_head).json()
        
        self.securities_history[ticker] = pd.DataFrame(securityhistory)
        
        self.logger.debug(f"Security history called and created : self.securities_history which contains {'securities history' if len(self.securities_history[ticker]) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method getSecuritiesTas called from {self.class_name} class with parameters ticker={ticker}, after={after}, period={period}, limit={limit}")
        assert ticker in self.tickers_name
        security_tas_head = {'ticker': ticker, 'after': after, 'period': after, 'limit': after}
        securitytas = requests.get(self.url + '/securities/tas', headers=self.API_KEY, params=security_tas_head).json()
        
        self.securities_tas[ticker] = pd.DataFrame(securitytas)
        self.securities_tas[ticker].set_index("id", inplace=True)
        self.logger.debug(f"Security tas called and created : self.securities_tas which contains {'securities tas' if len(self.securities_tas[ticker]) !=0 else 'nothing'}")

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
        self.logger.debug(f"Method getOrders called from {self.class_name} class with parameters status={status}")
        orders_head = {'status': status}
        self.orders = requests.get(self.url + '/orders', headers=self.API_KEY, params=orders_head).json()
        self.logger.debug(f"Orders called and created : self.orders which contains {'orders' if len(self.orders) !=0 else 'nothing'}")
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
        self.logger.debug(f"Method postOrder called from {self.class_name} class with parameters action={action}, ticker={ticker}, quantity={quantity}, price={price}, type={type}, ignore_limit={ignore_limit}")
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
        self.logger.debug(f"Order called and created")
        if (order_.status_code == 200):
            if type == "LIMIT":
                self.logger.info(f"{type} {action} order for {ticker} was placed for {quantity} shares at {price}$ per share")
            else:
                self.logger.info(f"{type} {action} order for {ticker} was placed for {quantity} shares")
            return order

        elif (order_.status_code == 401):
            self.logger.warning(f"Order for {ticker} is unauthorized")
            return None
        
        elif (order_.status_code == 429):
            self.logger.warning(f"Order for {ticker} was declined wait {order['wait']} seconds before trying again")
            return order
        else:
            print(order)

    
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
        self.logger.debug(f"Method getOrder called from {self.class_name} class with parameters order_id={order_id}")
        order_head = {'id': order_id} 
        order = requests.get(self.url + '/orders', headers=self.API_KEY, params=order_head).json()
        self.logger.debug(f"Orders retrieved and returns self.orders which contains {'orders' if len(self.orders) !=0 else 'nothing'}")
        return order

    def deleteOrder(self, order_id : str):
        """Deletes the order with the given id

        Parameters
        ----------
        order_id : str
            The id of the order
        """
        self.logger.debug(f"Method deleteOrder called from {self.class_name} class with parameters order_id={order_id}")
        order_head = {'id': order_id} 
        order_ = requests.delete(self.url + '/orders', headers=self.API_KEY, params=order_head)
        order = order_.json()

        if order_.status_code == 200:
            self.logger.warning(f"Order {order_id} was successfully deleted")
            return order
        
        elif order_.status_code==401:
            self.logger.warning(f"Order {order_id} is unauthorized")
            return None
    
    def getTenders(self):
        """Returns a list of all tenders

        Returns
        -------
        list
            list of all tenders
        """
        self.logger.debug(f"Method getTenders called from {self.class_name} class")
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
            
            self.logger.debug(f"Tenders called and created : self.tenders which contains {'tenders' if len(self.tenders) !=0 else 'nothing'}")
            return self.tenders
        
        elif tenders_.status_code == 401:
            self.logger.warning("Unauthorized")
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
        self.logger.debug(f"Method postTender called from {self.class_name} class with parameters id={id}, accept={accept}, price={price}")
        if accept:
            tender_head = {'price': price}
            tender = requests.post(self.url + '/tenders' + f'/{id}', headers=self.API_KEY, params=tender_head)

        else:
            tender = requests.delete(self.url + '/tenders' + f'/{id}', headers=self.API_KEY)
        
        if tender.status_code == 200:
            self.logger.info(f"Tender {id} was accepted")
        
        elif tender.status_code == 401:
            self.logger.warning(f"Tender {id} is unauthorized")


        return tender.status_code

    def getLeases(self):
        """Returns a list of all leases

        Returns
        -------
        list
            list of all leases
        """
        self.logger.debug(f"Method getLeases called from {self.class_name} class")
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
            self.logger.debug(f"Leases called and created : self.leases which contains {'leases' if len(self.leases) !=0 else 'nothing'}")
            return self.leases
        
        elif leases_.status_code == 401:
            self.logger.warning("Unauthorized")
            return None


        

if __name__ == "__main__":
    print("Hello World")