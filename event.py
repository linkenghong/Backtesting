# coding=gbk
class Event(object):
	pass

	
class MarketEvent(Event):
	def __init__(self):
		self.type = 'MARKET'

		
class SignalEvent(Event):
	def __init__(self, symbol, datetime, signal_type):
		"""
        Initialises the SignalEvent.

        Parameters:
        symbol - The ticker symbol, e.g. 'GOOG'.
        datetime - The timestamp at which the signal was generated.
        signal_type - 'LONG' or 'SHORT'.
        """
        
		self.type = 'SIGNAL'
		self.symbol = symbol
		self.datetime = datetime
		self.signal_type = signal_type

       
class OrderEvent(Event):
	def __init__(self, symbol, order_type, quantity, direction):
		"""
        Initialises the order type, setting whether it is
        a Market order ('MKT') or Limit order ('LMT'), has
        a quantity (integral) and its direction ('BUY' or
        'SELL').

        Parameters:
        symbol - The instrument to trade.
        order_type - 'MKT' or 'LMT' for Market or Limit.
        quantity - Non-negative integer for quantity.
        direction - 'BUY' or 'SELL' for long or short.
        """
		self.type = 'ORDER'
		self.symbol = symbol
		self.order_type = order_type
		self.quantity = quantity
		self.direction = direction
	
	def print_order(self):
		print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" % 
		 (self.symbol, self.order_type, self.quantity, self.direction))

	
class FillEvent(Event):
	def __init__(self, timeindex, symbol, exchange, quantity,
				 direction, fill_cost, commission=None):
		"""
        Initialises the FillEvent object. Sets the symbol, exchange,
        quantity, direction, cost of fill and an optional 
        commission.

        If commission is not provided, the Fill object will
        calculate it based on the trade size and Interactive
        Brokers fees.

        Parameters:
        timeindex - The bar-resolution when the order was filled.
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled. 交易所
        quantity - The filled quantity.
        direction - The direction of fill ('BUY' or 'SELL')
        fill_cost - The holdings value in dollars.
        commission - An optional commission sent from IB.
        """
		self.type = 'FILL'
		self.timeindex = timeindex
		self.symbol = symbol
		self.exchange = exchange
		self.quantity = quantity
		self.direction = direction
		self.fill_cost = fill_cost
		# Calculate commission
		if commission is None:
			self.commission = self.calculate_ib_commision()
		else:
			self.commission = commision
	
	def calculate_ib_commision(self):
		"""
        Calculates the fees of trading based on an Interactive
        Brokers fee structure for API, in USD.

        This does not include exchange or ECN fees.

        Based on "US API Directed Orders":
        https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        """
		commision = max(5, 0.03 / 100.0 * self.quantity * self.fill_cost)
		return commision
	
