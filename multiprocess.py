import multiprocessing
from multiprocessing import Queue
import time
import requests

class TradingApp():
    def __init__(self, host, API_KEY):
        self.host = host
        self.url = 'http://localhost:' + host + '/v1'

        self.latestBid = {}
        self.latestAsk = {}
        self.tickers = ["fun", "lol"]
        self.API_KEY = API_KEY
    
    def getCompDetail():
        pass

    def getAssetsInfo():
        pass

    def streamPrice(self):
        while True:
            securities = requests.get(self.url + '/securities', headers=self.API_KEY).json()
            for security in securities:
                ticker = security["ticker"]
                self.latestBid[ticker] = security["bid"]
                self.latestAsk[ticker] = security["ask"]



global cnt
cnt = 0

def count1(num):
    print("counter 1 startedgit ")
    for i in range(num):
        cnt += 1
        print("counter 1", end = "\r")
    
    print("counter 1 done")

def count2(num):
    print("counter 2 started")
    for i in range(num):
        cnt += 1
        print("counter 2", end = "\r")
    print("counter 2 done")



if __name__ == "__main__":
    N = 2 * 10**4

    p1 = multiprocessing.Process(target=count1, args=(N,))
    p2 = multiprocessing.Process(target=count2, args=(N,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()