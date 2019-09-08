import datetime
import queue

from Backtesting.strategy.base import AbstractStrategy
from Backtesting.event import SignalEvent, EventType
from Backtesting.backtest import Backtest


class BuyAndHoldStrategy(AbstractStrategy):
    """
    A testing strategy that simply purchases (longs) an asset
    upon first receipt of the relevant bar event and
    then holds until the completion of a backtest.
    """
    def __init__(
        self, symbol, events_queue,
        base_quantity=1000
    ):
        self.symbol = symbol
        self.events_queue = events_queue
        self.base_quantity = base_quantity
        self.invested = False
        self.pre_price = 0
        self.bar_count = 0

    def calculate_signals(self, event):
        if (
            event.type == EventType.BAR and
            event.symbol == self.symbol
        ):
            
            position = self.get_symbol_position(self.symbol)
            avg_price = position["avg_price"]
            if avg_price == 0:
                avg_price = self.pre_price
            if self.pre_price == 0 or (event.close_price <= avg_price * 0.9 and event.close_price >= avg_price * 0.85):
                signal = SignalEvent(
                    self.symbol, event.timestamp, "BUY",
                    suggested_quantity=self.base_quantity
                )
                self.events_queue.put(signal)
                self.pre_price = event.close_price
            elif event.close_price >= avg_price * 1.05 or event.close_price < avg_price * 0.8:
                signal = SignalEvent(
                    self.symbol, event.timestamp, "SELL",
                    suggested_quantity=self.base_quantity
                )
                self.pre_price = event.close_price
                self.events_queue.put(signal)


def run(testing, symbol_list, filename):
    # Backtest information
    title = ['Buy and Hold Example on %s' % symbol_list[0]]
    initial_equity = 100000.0
    start_date = datetime.datetime(2009, 1, 1)
    end_date = datetime.datetime(2010, 1, 1)

    # Use the Buy and Hold Strategy
    events_queue = queue.Queue()
    strategy = BuyAndHoldStrategy(symbol_list[0], events_queue)
    data_dir = './/data//'
    output_dir = './/out//'
    # Set up the backtest
    backtest = Backtest(
        strategy, symbol_list,
        initial_equity, start_date, end_date,
        events_queue, data_dir, output_dir, title=title,
        benchmark = symbol_list[1]
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Configuration data
    testing = False
    symbol_list = ["000001SZ_D", "000001SZ_D"]
    filename = None
    run(testing, symbol_list, filename)
