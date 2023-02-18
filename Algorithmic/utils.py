import pandas as pd

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