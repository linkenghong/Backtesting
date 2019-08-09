# coding=gbk
import os, os.path
import pandas as pd


from ..event import BarEvent

from .base import DataHandler
    
    
class HistoricCSVDataHandler(DataHandler):
    def __init__(
        self, events_queue, data_dir, symbol_list,
        start_date=None, end_date=None):
        """
        通过本地CSV文件及股票代码清单来初始化历史数据

        Parameters:
        events_queue - The Event Queue.
        data_dir - Absolute directory path to the CSV files.
        symbol_list - A list of symbol strings.
        """
        self.events_queue = events_queue
        self.data_dir = data_dir
        self.symbol_list = symbol_list
        
        self.symbol_data = {} # 字典:{symbol:DataFrame}
        self.latest_symbol_data = {} # 最新bar，字典：{symbol:bar{close, adj_close, timestamp}}
        self.continue_backtest = True
        self.need_backtest = True

        if symbol_list is not None:
            for symbol in symbol_list:
                self.subscribe_symbol(symbol)        

        self.start_date = start_date
        self.end_date = end_date
        self.pre_day = None
        self.cur_day = None
        if self.need_backtest:
            self.bar_stream = self._merge_sort_symbol_data()


    def subscribe_symbol(self, symbol):
        """
        Subscribes the price handler to a new symbol_data.
        """
        if symbol not in self.symbol_data:
            try:
                self._open_convert_csv_files(symbol)
                dft = self.symbol_data[symbol]
                row0 = dft.iloc[0]

                symbol_prices = {
                    "close": row0["Close"],
                    "adj_close": row0["Adj Close"],
                    "timestamp": dft.index[0]
                }
                self.latest_symbol_data[symbol] = symbol_prices
            except OSError:
                print(
                    "Could not subscribe symbol %s "
                    "as no data CSV found for pricing." % symbol
                )
                self.need_backtest = False
        else:
            print(
                "Could not subscribe symbol %s "
                "as is already subscribed." % symbol
            )

    def stream_next(self):
        """
        Place the next BarEvent onto the event queue.
        """
        try:
            index, row = next(self.bar_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        # Obtain all elements of the bar from the dataframe
        symbol = row["Symbol"]

        cur_day = index.date()
        if self.pre_day == None:
            self.pre_day = cur_day       
        if self.cur_day == None:
            self.cur_day = cur_day
        
        self.pre_day = self.cur_day
        self.cur_day = cur_day
        
        # Create the bar event for the queue
        bev = self._create_event(index, symbol, row)
        # Store event
        self._store_event_to_latest(bev)
        # Send event to queue
        self.events_queue.put(bev)

        
    def _open_convert_csv_files(self, symbol):

        """
        Opens the CSV files containing the equities ticks from
        the specified CSV data directory, converting them into
        them into a pandas DataFrame, stored in a dictionary.
        """
        symbol_path = os.path.join(self.data_dir, "%s.csv" % symbol)
        self.symbol_data[symbol] = pd.io.parsers.read_csv(
            symbol_path, header=0, parse_dates=True,
            index_col=0, names=(
                "Date", "Open", "High", "Low",
                "Close", "Volume", "Adj Close"
            )
        )
        self.symbol_data[symbol]["Symbol"] = symbol

    def _merge_sort_symbol_data(self):
        """
        Concatenates all of the separate equities DataFrames
        into a single DataFrame that is time ordered, allowing tick
        data events to be added to the queue in a chronological fashion.

        Note that this is an idealised situation, utilised solely for
        backtesting. In live trading ticks may arrive "out of order".
        """
        df = pd.concat(self.symbol_data.values()).sort_index()

        start = self.start_date
        end = self.end_date

        df['colFromIndex'] = df.index
        df = df.sort_values(by=["colFromIndex", "Symbol"])

        if start is not None and end is not None:
            df = df.loc[start:end]
        elif start is not None and end is None:
            df = df.loc[start:]
        elif start is None and end is not None:
            df = df.loc[:end]

        if df.empty:
            print("The backtest period is not in the data!")
            self.need_backtest = False

        return df.iterrows()


    def _create_event(self, index, symbol, row):
        """
        Obtain all elements of the bar from a row of dataframe
        and return a BarEvent
        """
        timestamp = index
        
        if self.pre_day == self.cur_day:
            new_day = False
        else:
            new_day = True

        open_price = row["Open"]
        high_price = row["High"]
        low_price = row["Low"]
        close_price = row["Close"]
        adj_close_price = row["Adj Close"]
        volume = int(row["Volume"])
        bev = BarEvent(
            symbol, timestamp, new_day,
            open_price, high_price, low_price,
            close_price, volume, adj_close_price
        )
        return bev


