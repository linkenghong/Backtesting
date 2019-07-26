# coding=gbk
from enum import Enum

# Enum 是个枚举类
EventType = Enum("EventType", "BAR SIGNAL ORDER FILL")


class Event(object):
    @property
    def typename(self):
        return self.type.name
    
class BarEvent(Event):
    """
    Handles the event of receiving a new market
    open-high-low-close-volume bar, as would be generated
    via common data providers.
    """
    def __init__(
        self, symbol, timestamp,
        open_price, high_price, low_price,
        close_price, volume, adj_close_price=None
    ):
        """
        Initialises the BarEvent.

        Parameters:
        symbol - The ticker symbol, e.g. 'GOOG'.
        timestamp - The timestamp of the bar
        open_price - The unadjusted opening price of the bar
        high_price - The unadjusted high price of the bar
        low_price - The unadjusted low price of the bar
        close_price - The unadjusted close price of the bar
        volume - The volume of trading within the bar
        adj_close_price - The vendor adjusted closing price
            (e.g. back-adjustment) of the bar

        Note: It is not advised to use 'open', 'close' instead
        of 'open_price', 'close_price' as 'open' is a reserved
        word in Python.
        """
        self.type = EventType.BAR
        self.symbol = symbol
        self.timestamp = timestamp
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.adj_close_price = adj_close_price

        
class SignalEvent(Event):
    def __init__(self, symbol, timestamp, action, suggested_quantity=None, order_type='MKT'):
        """
        Initialises the SignalEvent.

        Parameters:
        symbol - The ticker symbol, e.g. 'GOOG'.
        timestamp - The timestamp at which the signal was generated.
        order_type - 'MKT' or 'LMT' for Market or Limit.
        action - 'BUY' or 'SELL'.
        suggested_quantity - Optional positively valued integer
            representing a suggested absolute quantity of units
            of an asset to transact in, which is used by the
            PositionSizer and RiskManager.
        """
        
        self.type = EventType.SIGNAL
        self.symbol = symbol
        self.timestamp = timestamp
        self.action = action
        self.suggested_quantity = suggested_quantity
        self.order_type = order_type

       
class OrderEvent(Event):
    def __init__(self, symbol, order_type, quantity, action):
        """
        Initialises the order type, setting whether it is
        a Market order ('MKT') or Limit order ('LMT'), has
        a quantity (integral) and its action ('BUY' or
        'SELL').

        Parameters:
        symbol - The instrument to trade.
        order_type - 'MKT' or 'LMT' for Market or Limit.
        quantity - Non-negative integer for quantity.
        action - 'BUY' or 'SELL' for long or short.
        """
        self.type = EventType.ORDER
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.action = action
    
    def print_order(self):
        print("Order: Symbol=%s, Type=%s, Quantity=%s, Action=%s" % 
         (self.symbol, self.order_type, self.quantity, self.action))

    
class FillEvent(Event):
    def __init__(
        self, timestamp, symbol, action,
        quantity, price, commission, exchange):
        """
        Parameters:
        timestamp - The bar-resolution when the order was filled.
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled. 交易所
        quantity - The filled quantity.
        action - The action of fill ('BUY' or 'SELL')
        price - The holdings value in dollars.
        commission - An optional commission sent from IB.
        """
        self.type = EventType.FILL
        self.timestamp = timestamp
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.action = action
        self.price = price
        self.commission = commission
    
    
