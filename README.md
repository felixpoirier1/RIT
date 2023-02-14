# How to setup system

### Download requirements
#### Using powershell
```
$ ritenv\Scripts\activate.ps1
```

if above command doesn't work try:
```
$ py -m pip install -r requirements.txt
```

## Download tradeapp module
```
$ py tradeapp/setup.py install
```

## import tradeapp in own project
```
# main.py

from tradeapp.tradeapp import TradingApp
```

## Create a trading app
```
#main.py

app = TradingApp("HOST", "ADDRESS")
```

## Modify TradeApp to your own liking using inheritance
```
class MyTradingApp(TradingApp):
    def __init__(self, host, API_KEY):
        super().__init__(host, API_KEY)
        # create your own variables
        self.my_own_variable = None
    
    # create a method
    def myMethod1(self, argument1, argument2, *args, **kwargs):
        # write you code here

        # return whatever you want 
        return None

    #
```
Using this method you will have access to all of the functionality inside of Trading App with your own touch

You can then call your own version of TradeApp called MyTradingApp using

```
app = MyTradingApp("HOST", "ADDRESS")
```
and you can delete whatever instances of TradingApp you previously used

## Start your program 
```
$ py main.py
```

You should see a green message 
```
Program started with host and API KEY : XXXX YYYYYYYY
```