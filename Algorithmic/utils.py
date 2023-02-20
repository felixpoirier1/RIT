import pandas as pd
import timeit
import numpy as np

def enoughLiquidty(book: dict[pd.DataFrame, pd.DataFrame], slack: float, quantity: int, price: float, direction: str) -> bool:
    """Determines if there is enough liquidity in the order book to fill a given order

    Parameters
    ----------
    book : pd.DataFrame
        dict of pd.DataFrames for bids and asks
    slack : float
        the slack to add to the quantity to be filled 
    quantity : int
        the quantity to be filled
    price : float
        the price at which the order is to be filled at minimum
    direction : str
        the direction of the order, either "BUY" or "SELL"

    Returns
    -------
    bool
        True if there is enough liquidity, False otherwise

    Raises
    ------
    ValueError
        if direction is not "BUY" or "SELL"
    """
    if direction == "SELL":
        book = book["asks"]
        book = book.loc[book["price"] >= price]
        quantity_book = (book["quantity"] - book["quantity_filled"])*(1+slack)


        if quantity_book.sum() >= quantity:
            return True
        else:
            return False

    elif direction == "BUY":
        book = book["bids"]
        book = book.loc[book["price"] <= price]
        quantity_book = (book["quantity"] - book["quantity_filled"])*(1+slack)

        if quantity_book.sum() >= quantity:
            return True
        else:
            return False
        
    else:
        raise ValueError("Direction must be either BUY or SELL")
    
def optimalPrice(book: dict[pd.DataFrame, pd.DataFrame], quantity: int, direction: str) -> float:
    """Determines the optimal price to fill a given quantity

    Parameters
    ----------
    book : dict[pd.DataFrame, pd.DataFrame]
        dict of pd.DataFrames for bids and asks
    quantity : int
        the quantity to be filled
    direction : str
        the direction of the order, either "BUY" or "SELL"

    Returns
    -------
    float
        the optimal price to fill the given quantity

    Raises
    ------
    ValueError
        if direction is not "BUY" or "SELL"
    """
    if direction == "SELL":
        book = book["asks"]
        quantity_book = book["quantity"] - book["quantity_filled"]
        quantity_book = quantity_book.cumsum()
        price = book.loc[quantity_book >= quantity, "price"].iloc[0]
        return price

    elif direction == "BUY":
        book = book["bids"]
        quantity_book = book["quantity"] - book["quantity_filled"]
        quantity_book = quantity_book.cumsum()
        price = book.loc[quantity_book >= quantity, "price"].iloc[0]
        return price
        
    else:
        raise ValueError("Direction must be either BUY or SELL")
    
import pandas as pd

def createSyntheticETF(books: dict[str, dict[pd.DataFrame, pd.DataFrame]], direction: str):
    """
    This function takes books for two securities and creates a synthetic book for an ETF consiting of the two securities

    Parameters
    ----------
    books : dict[str, dict[pd.DataFrame, pd.DataFrame]]
        dict of books for two securities

    Returns
    -------
    pd.DataFrame
        The book with the proper formatting for comparison to the ETF
    """

    # initialize the synthetic book
    synth_book = []

    # create a list of the two book names
    books_name = list(books.keys())

    # keep iterating until there are no more orders in either book
    while len(books[books_name[0]][direction]) > 0 and len(books[books_name[1]][direction]) > 0:
        # find the lowest volume for the first orders on the books
        min_quantity = min(books[books_name[0]][direction].iloc[0]["quantity"], books[books_name[1]][direction].iloc[0]["quantity"])

        # calculate the price of the synthetic order
        price = books[books_name[0]][direction].iloc[0]["price"] + books[books_name[1]][direction].iloc[0]["price"]

        # create the new order
        synth_book.append([min_quantity, price])

        # subtract the quantity from both books
        books[books_name[0]][direction].iloc[0]["quantity"] -= min_quantity
        books[books_name[1]][direction].iloc[0]["quantity"] -= min_quantity

        # remove the order from the book if it's completely filled
        if books[books_name[0]][direction].iloc[0]["quantity"] == 0:
            books[books_name[0]][direction] = books[books_name[0]][direction].iloc[1:]

        if books[books_name[1]][direction].iloc[0]["quantity"] == 0:
            books[books_name[1]][direction] = books[books_name[1]][direction].iloc[1:]

    return np.array(synth_book)


def findOptimalArbitrageQty(books: dict[str, dict[np.ndarray, np.ndarray]], direction: str, prices: list[float, float], slack: float = 0.02) -> int:
    """_summary_

    Parameters
    ----------
    books : dict[str, dict[list, pd.DataFrame]]
        _description_
    direction : str
        _description_
    prices : list[float, float]
        _description_
    slack : float, optional
        _description_, by default 0.02

    Returns
    -------
    int
        _description_
    """

    

if __name__ == "__main__":
    #create BULL book
    BULL = {
        "bids": pd.DataFrame({
            "price": [100, 99, 98, 97, 96, 95, 94, 93, 92, 91],
            "quantity": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            "quantity_filled": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }), 
        "asks": pd.DataFrame({
            "price": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "quantity": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            "quantity_filled": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        })

    }   

    #create BEAR book
    BEAR = {
        "bids": pd.DataFrame({
            "price": [100, 99, 98, 97, 96, 95, 94, 93, 92, 91],
            "quantity": [130, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            "quantity_filled": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }),     
        "asks": pd.DataFrame({
            "price": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "quantity": [120, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            "quantity_filled": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        })  
    }

    print()


    print(createSyntheticETF({"security1": BULL, "security2": BEAR}, "asks"))
        
    def TESTcreateSyntheticETF():
        np.array(BEAR["asks"][["price", "quantity"]])
        #return createSyntheticETF({"security1": BULL, "security2": BEAR}, "bids")

    #generate synthetic ETF book
    print(timeit.timeit(TESTcreateSyntheticETF, number=1000))