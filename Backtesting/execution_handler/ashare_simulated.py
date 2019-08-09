import datetime
import os
import csv

from .base import AbstractExecutionHandler
from ..event import (FillEvent, EventType)


class AShareSimulatedExecutionHandler(AbstractExecutionHandler):

    def __init__(
        self, events_queue, data_handler, portfolio_handler,
        output_dir, slippage=0.01, record=True
        ):
        
        self.events_queue = events_queue
        self.data_handler = data_handler
        self.portfolio_handler = portfolio_handler
        self.output_dir = output_dir
        self.slippage = slippage
        self.record = record
        if self.record == True:
            now = datetime.datetime.utcnow().date()
            self.csv_filename = "tradelog_" + now.strftime("%Y-%m-%d") + ".csv"
            
            try:
                fname = os.path.expanduser(os.path.join(self.output_dir, self.csv_filename))
                os.remove(fname)
            except (IOError, OSError):
                pass
            # Write new file header
            fieldnames = [
                "Timestamp", "Symbol",
                "Action", "Quantity",
                "Exchange", "Price",
                "Commission"
            ]
            with open(fname, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    def calculate_ib_commission(self, quantity, fill_price, action):
        """
        Calculate the commission for a transaction. 
        commission = 0.0008
        tax ratio = 0.001 for SELL
        """
        commission = max(
            0.0008 * fill_price * quantity, 5
        )
        if action == "SELL":
            commission += 0.001 * fill_price * quantity
        return round(commission, 2)

    def execute_order(self, event):
        """
        default slippage = 0.01

        Parameters:
        event - An Event object with order information.
        """
        if event.type == EventType.ORDER:
            # Obtain values from the OrderEvent
            timestamp = self.data_handler.get_last_timestamp(event.symbol)
            symbol = event.symbol
            action = event.action
            try:
                cur_quantity = self.portfolio_handler.portfolio.positions[symbol].available_quantity
            except :
                cur_quantity = 0
            cur_cash = self.portfolio_handler.portfolio.cur_cash
            
            if action == 'SELL' and cur_quantity == 0:
                print(str(timestamp) + ": A share can't short!The order will be cancelled!")
                return
            
            if action == 'SELL' and event.quantity > cur_quantity:
                quantity = cur_quantity
                print(str(timestamp) + ": Trading volume(%i) is greater than holding amount(%i)! \
                    Will be traded by holding amount!" 
                      % (event.quantity,cur_quantity))
                
            else:
                quantity = event.quantity

            # Obtain the fill price
            close_price = self.data_handler.get_last_close(symbol)
            if action == 'BUY':
                fill_price = close_price + self.slippage
            elif action == 'SELL':
                fill_price = close_price - self.slippage
            

            # Set a dummy exchange and calculate trade commission
            exchange = "CN"
            commission = self.calculate_ib_commission(quantity, fill_price, action)

            if action == 'BUY' and quantity * fill_price + commission > cur_cash:
                print(str(timestamp) + ": Current cash is %.2f, the transaction cost is %.2f. \
                    Out of cash, the order will be cancelled!"
                     % (cur_cash, (quantity * fill_price + commission)))
                
            else:
                # Create the FillEvent and place on the events queue
                fill_event = FillEvent(
                    timestamp, symbol,
                    action, quantity,
                    fill_price, commission,
                    exchange,
                )
                self.events_queue.put(fill_event)
                
                if self.record == True:
                    self.record_trade(fill_event)

                
    def record_trade(self, fill_event):

        fname = os.path.expanduser(os.path.join(self.output_dir, self.csv_filename))

        with open(fname, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                fill_event.timestamp, fill_event.symbol,
                fill_event.action, fill_event.quantity,
                fill_event.exchange, fill_event.price,
                fill_event.commission
            ])
