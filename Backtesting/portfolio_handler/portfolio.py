# coding=gbk
import datetime
import os
import csv

from .position import Position

class Portfolio(object):
    def __init__(self, data_handler, cash, output_dir):
        """
        On creation, the Portfolio object contains no
        positions and all values are "reset" to the initial cash.
        """
        self.data_handler = data_handler
        self.equity = cash
        self.cur_cash = cash
        self.output_dir = output_dir
        self.positions = {}
        self.closed_positions = []

        now = datetime.datetime.utcnow().date()
        self.csv_filename = "positionlog_" + now.strftime("%Y-%m-%d") + ".csv"
            
        try:
            self.fname = os.path.expanduser(os.path.join(self.output_dir, self.csv_filename))
            os.remove(self.fname)
        except (IOError, OSError):
            pass
        # Write new file header
        fieldnames = [
            "Timestamp", "Symbol","Position",
            "Price", "Avg_price", "Market_value",
            "Commission"
        ]
        with open(self.fname, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()



    def _update_portfolio(self):
        """
        Updates the value of all positions that are currently open.
        """
        self.equity = self.cur_cash

        for symbol in self.positions:
            pt = self.positions[symbol]
            cur_price = self.data_handler.get_last_close(symbol)
            pt.update_market_value(cur_price)
            self.equity += pt.market_value
            
    def _update_position(self):
        """
        Update the available position of all symbol.
        """
        for symbol in self.positions:
            self.positions[symbol].update_position()

    def _add_position(
        self, action, symbol,
        quantity, transact_price, commission
    ):
        """
        Adds a new Position object to the Portfolio. This
        requires getting the current price from the
        price data handler in order to calculate a reasonable
        "market value".

        Once the Position is added, the Portfolio values
        are updated.
        """
        if symbol not in self.positions:
            cur_price = self.data_handler.get_last_close(symbol)
            position = Position(
                action, symbol, quantity,
                transact_price, commission, cur_price
            )
            self.positions[symbol] = position
            self._update_portfolio()
        else:
            print(
                "Ticker symbol %s is already in the positions list. "
                "Could not add a new position." % symbol
            )

    def _modify_position(
        self, action, symbol,
        quantity, transact_price, commission
    ):
        """
        Modifies a current Position object to the Portfolio.
        This requires getting the current price from the
        price data handler in order to calculate a reasonable
        "market value".

        Once the Position is modified, the Portfolio values
        are updated.
        """
        if symbol in self.positions:
            self.positions[symbol].transact_shares(
                action, quantity, transact_price, commission
            )
            cur_price = self.data_handler.get_last_close(symbol)
            self.positions[symbol].update_market_value(cur_price)

            self._update_portfolio()
        else:
            print(
                "Ticker symbol %s not in the current position list. "
                "Could not modify a current position." % symbol
            )

    def transact_position(
        self, timestamp, action, symbol,
        quantity, transact_price, commission
    ):
        """
        Handles any new position or modification to
        a current position, by calling the respective
        _add_position and _modify_position methods.

        Hence, this single method will be called by the
        PortfolioHandler to update the Portfolio itself.
        """
        if action == "BUY":
            self.cur_cash -= ((quantity * transact_price) + commission)
        elif action == "SELL":
            self.cur_cash += ((quantity * transact_price) - commission)
   
        if symbol not in self.positions:
            self._add_position(
                action, symbol, quantity,
                transact_price, commission
            )
        else:
            self._modify_position(
                action, symbol, quantity,
                transact_price, commission
            )
        self.positions[symbol].record_position(self.fname, timestamp)
        
        if self.positions[symbol].quantity == 0:
            closed = self.positions.pop(symbol)
            self.closed_positions.append(closed)

