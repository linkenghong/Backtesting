from abc import ABCMeta, abstractmethod


class AbstractStrategy(object):
    """
    AbstractStrategy is an abstract base class providing an interface for
    all subsequent (inherited) strategy handling objects.

    The goal of a (derived) Strategy object is to generate Signal
    objects for particular symbols based on the inputs of ticks
    generated from a PriceHandler (derived) object.

    This is designed to work both with historic and live data as
    the Strategy object is agnostic to data location.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, event):
        """
        Provides the mechanisms to calculate the list of signals.
        """
        raise NotImplementedError("Should implement calculate_signals()")

    def set_portfolio(self, portfolio_handler):
        self.portfolio_handler = portfolio_handler
    
    def get_symbol_position(self, symbol):

        key = ["symbol", "quantity", "unavailable_quantity",
        "available_quantity", "price", "total_commission",
        "avg_price", "market_value"]

        position_dict = {k:0 for k in key}
        position_dict["symbol"] = symbol
        try:
            position = self.portfolio_handler.portfolio.positions[symbol]
        except:
            pass
        else:
            position_dict["quantity"] = position.quantity
            position_dict["unavailable_quantity"] = position.unavailable_quantity
            position_dict["available_quantity"] = position.available_quantity
            position_dict["price"] = position.price
            position_dict["total_commission"] = position.total_commission
            position_dict["avg_price"] = position.avg_price
            position_dict["market_value"] = position.market_value
        
        return position_dict



class Strategies(AbstractStrategy):
    """
    Strategies is a collection of strategy
    """
    def __init__(self, *strategies):
        self._lst_strategies = strategies

    def calculate_signals(self, event):
        for strategy in self._lst_strategies:
            strategy.calculate_signals(event)
