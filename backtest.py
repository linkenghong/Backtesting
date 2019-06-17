import queue
import time
import matplotlib
import matplotlib.pyplot as plt

from event import MarketEvent, SignalEvent, OrderEvent, FillEvent
from data import HistoricCSVDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import NaivePortfolio
from execution import SimulatedExecutionHandler


events = queue.Queue()
csv_dir = 'E://GitHub//quantstart-backtester//backtester//csv//'
symbol_list = ['AAPL','BRK-B','CVX','KO']

data = HistoricCSVDataHandler(events, csv_dir, symbol_list)
strategy = BuyAndHoldStrategy(data, events)
portfolio = NaivePortfolio(data, events, '12/1/14')
execution = SimulatedExecutionHandler(data, events)

while True:
	if data.continue_backtest is True:
		data.update_bars()
	else:
		break
		
	while True:
		try:
			event = events.get(block=False)
		except queue.Empty:
			break
			
		if event:
			if isinstance(event, MarketEvent):
				strategy.calculate_signals(event)
				portfolio.update_timeindex(event)
			elif isinstance(event, SignalEvent):
				portfolio.update_signal(event)
			elif isinstance(event, OrderEvent):
				execution.execute_order(event)
			elif isinstance(event, FillEvent):
				portfolio.update_fill(event)



results, curve = portfolio.output_summary_stats()

curve[['equity_curve','total']].plot()
plt.show()
	


