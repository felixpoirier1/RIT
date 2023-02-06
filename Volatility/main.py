from tradeapp import TradingApp
import matplotlib.pyplot as plt

app = TradingApp("9999", "74IAGTEB")

app.trading_limit = 200

securitybook = app.getSecuritiesBook(app.tickers_name[0])

app.getSecuritiesTas("RTM")

print(app.securities_tas["RTM"].groupby("tick").mean())


#plt.hist(app.securities_history["RTM"][list_col].pct_change(), bins=20)

#plt.plot(app.securities_history["RTM"][list_col].pct_change().cumsum())
#plt.show()




