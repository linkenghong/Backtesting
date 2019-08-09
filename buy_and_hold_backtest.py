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
        base_quantity=100
    ):
        self.symbol = symbol
        self.events_queue = events_queue
        self.base_quantity = base_quantity
        self.bars = 0
        self.invested = False


    def calculate_signals(self, event):
        if (
            event.type == EventType.BAR and
            event.symbol == self.symbol
        ):
            if not self.invested:
                signal = SignalEvent(
                    self.symbol, event.timestamp, "BUY",
                    suggested_quantity=self.base_quantity
                )
                self.events_queue.put(signal)
                self.invested = True
            else:
                signal = SignalEvent(
                    self.symbol, event.timestamp, "SELL",
                    suggested_quantity=self.base_quantity
                )
                self.events_queue.put(signal)
                self.invested = False


def run(testing, symbol_list, filename):
    # Backtest information
    title = ['Buy and Hold Example on %s' % symbol_list[0]]
    initial_equity = 100000.0
    start_date = datetime.datetime(2013, 1, 3)
    end_date = datetime.datetime(2013, 1, 30)

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
        #benchmark = symbol_list[1]
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Configuration data
    testing = False
    symbol_list = ["AAPL"]
    filename = None
    run(testing, symbol_list, filename)
