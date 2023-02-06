import requests
import pandas as pd

class TradingApp():
    def __init__(self, host, API_KEY):
        self.host = str(host)
        print(f"Program started with host : {host} and API KEY {API_KEY}")
        

        self.host = host
        self.url = 'http://localhost:' + host + '/v1'

        self.latestBid = {}
        self.latestAsk = {}
        self.tickers = ["fun", "lol"]
        self.API_KEY = {'X-API-Key': API_KEY}
        self.getCaseDetails()
        self.getTraderDetails()
        self.getTradingLimits()
        self.getAssets()
        self.getSecurities()
        self.trading_limit = None

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
    
    def getSecuritiesBook(self, ticker: str, limit : int = None):
        assert ticker in self.tickers_name
        security_book_head = {'ticker': ticker}
        securitybook = requests.get(self.url + '/securities/book', headers=self.API_KEY, params=security_book_head).json()

        return securitybook
    
    def getSecuritiesHistory(self, ticker : str, period : int = None, limit : int = None):
        assert ticker in self.tickers_name
        security_history_head = {'ticker': ticker, 'period' : period, 'limit': limit}
        securityhistory = requests.get(self.url + '/securities/history', headers=self.API_KEY, params=security_history_head).json()
        
        self.securities_history[ticker] = pd.DataFrame(securityhistory)
        self.securities_history[ticker].set_index("tick", inplace=True)

    def getSecuritiesTas(self, ticker : str, after : int = None, period : int = None, limit : int = None):
        """Reutrns all  trades that were filled by all the participants for a given security

        Args:
            ticker (str): name of the security
            after (int, optional): start tick. Defaults to None.
            period (int, optional):period to retrieve data from. Defaults to None.
            limit (int, optional): last tick. Defaults to None.
        """
        assert ticker in self.tickers_name
        security_tas_head = {'ticker': ticker, 'after': after, 'period': after, 'limit': after}
        securitytas = requests.get(self.url + '/securities/tas', headers=self.API_KEY, params=security_tas_head).json()
        
        self.securities_tas[ticker] = pd.DataFrame(securitytas)
        print(self.securities_tas[ticker])
        self.securities_tas[ticker].set_index("id", inplace=True)


    def streamPrice(self):
        while True:
            securities = requests.get(self.url + '/securities', headers=self.API_KEY).json()
            for security in securities:
                ticker = security["ticker"]
                self.latestBid[ticker] = security["bid"]
                self.latestAsk[ticker] = security["ask"]

if __name__ == "__main__":
    print("Hello World")