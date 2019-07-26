# coding=gbk
from abc import ABC, abstractmethod

class DataHandler(ABC):

    def unsubscribe_symbol(self, symbol):
        """
        Unsubscribes the price handler from a current ticker symbol.
        """
        try:
            self.symbol_data.pop(symbol, None)
            self.latest_symbol_data.pop(symbol, None)
        except KeyError:
            print(
                "Could not unsubscribe symbol %s "
                "as it was never subscribed." % symbol
            )

    def get_last_timestamp(self, symbol):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if symbol in self.latest_symbol_data:
            timestamp = self.latest_symbol_data[symbol]["timestamp"]
            return timestamp
        else:
            print(
                "Timestamp for symbol %s is not "
                "available from the %s." % (symbol, self.__class__.__name__)
            )
            return None
            
    def _store_event_to_latest(self, event):
        """
        Store price event for closing price and adjusted closing price
        """
        symbol = event.symbol
        self.latest_symbol_data[symbol]["close"] = event.close_price
        self.latest_symbol_data[symbol]["adj_close"] = event.adj_close_price
        self.latest_symbol_data[symbol]["timestamp"] = event.timestamp

    def get_last_close(self, symbol):
        """
        Returns the most recent actual (unadjusted) closing price.
        """
        if symbol in self.latest_symbol_data:
            close_price = self.latest_symbol_data[symbol]["close"]
            return close_price
        else:
            print(
                "Close price for symbol %s is not "
                "available from the %s."  % (symbol, self.__class__.__name__)
            )
            return None
            