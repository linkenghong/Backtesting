# coding=gbk
import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod
from math import floor

from event import FillEvent, OrderEvent
from performance import create_sharpe_ratio, create_drawdowns

class Portfolio(object):
	__metaclass__ = ABCMeta
	
	@abstractmethod
	def update_signal(self, event):
		raise NotImplementedError("Should implement update_signal()")
		
	@abstractmethod
	def update_fill(self, event):
		raise NotImplementedError("Should implement update_fill()")
		

class NaivePortfolio(Portfolio):
	def __init__(self, bars, events, start_date, initial_capital=100000.0):
		"""
		Parameters:
		bars - The DataHandler object with current market data.
        events - The Event Queue object.
        start_date - The start date (bar) of the portfolio.
        initial_capital - The starting capital in USD.
		"""
		self.bars = bars
		self.events = events
		self.symbol_list = self.bars.symbol_list
		self.start_date = start_date
		self.initial_capital = initial_capital
		
		# 仓位数组记录list: [dic: {symbol_1:0, symbol_2:0, ..., 'datetime':start_date}]
		self.all_positions = self.construct_all_positions()
		
		# 当前仓位dic: {symbol_1:0, symbol_2:0, ...}
		self.current_positions = dict( (k, v) for k, v in [(s, 0) for s in self.symbol_list] )
		
		# 组合市值记录list: [dic: {symbol_1:0, symbol_2:0, ..., 'datetime':start_date，
		#						 'cash':init, 'commission':0, 'total':init}]
		self.all_holdings = self.construct_all_holdings()
		
		# 当前市值情况情况dic： {symbol_1:0, symbol_2:0, ...,'cash':init, 'commission':0, 'total':init}
		self.current_holdings = self.construct_current_holdings()

		
	def construct_all_positions(self):
		d = dict( (k, v) for k, v in [(s, 0) for s in self.symbol_list] )
		d['datetime'] = self.start_date
		return [d]
		
	def construct_all_holdings(self):
		d = dict( (k, v) for k, v in [(s, 0.0) for s in	self.symbol_list] )
		d['datetime'] = self.start_date
		d['cash'] = self.initial_capital
		d['commission'] = 0.0
		d['total'] = self.initial_capital
		return [d]
		
	def construct_current_holdings(self):
		d = dict( (k, v) for k, v in [(s, 0.0) for s in self.symbol_list] )
		d['cash'] = self.initial_capital
		d['commission']	= 0.0
		d['total'] = self.initial_capital
		return d

		
	def update_timeindex(self, event):
		"""
		以下是根据不同时刻股价不同来更新持仓数及市值情况
		"""
		bars = {}
		for sym in self.symbol_list:
			bars[sym] = self.bars.get_latest_bars(sym, N=1)
		
		# Update positions
		dp = dict( (k, v) for k, v in [(s, 0) for s in self.symbol_list] )
		dp['datetime'] = bars[self.symbol_list[0]][0][1]
		
		for s in self.symbol_list:
			dp[s] = self.current_positions[s]
			
		# Append the current positions
		self.all_positions.append(dp)
		
		# Update holdings
		dh = dict( (k, v) for k, v in [(s, 0) for s in self.symbol_list] )
		dh['datetime'] = bars[self.symbol_list[0]][0][1]
		dh['cash'] = self.current_holdings['cash']
		dh['commission'] = self.current_holdings['commission']
		dh['total'] = self.current_holdings['cash']
		
		for s in self.symbol_list:
			# Approximation to the real value
			market_value = self.current_positions[s] * bars[s][0][5]
			dh[s] = market_value
			dh['total'] += market_value
			
		# Append the current holdings
		self.all_holdings.append(dh)
		
		
	def update_fill(self, event):
		if event.type == 'FILL':
			self.update_positions_from_fill(event)
			self.update_holdings_from_fill(event)
		
	def update_positions_from_fill(self, fill):
		"""
		Parameters:
		fill - The FillEvent object to update the positions with.
		"""
		# Check whether the fill is a buy or sell
		fill_dir = 0
		if fill.direction == 'BUY':
			fill_dir = 1
		if fill.direction == 'SELL':
			fill_dir = -1
			
		# Update positions list with new quantities
		self.current_positions[fill.symbol] += fill_dir * fill.quantity
		
	def update_holdings_from_fill(self, fill):
		"""
		Parameters:
		fill - The FillEvent object to update the positions with.
		"""
		# Check whether the fill is a buy or sell
		fill_dir = 0
		if fill.direction == 'BUY':
			fill_dir = 1
		if fill.direction == 'SELL':
			fill_dir = -1
			
		# Update holdings list with new quantities
		fill_cost = self.bars.get_latest_bars(fill.symbol)[0][5] # close price
		cost = fill_dir * fill_cost * fill.quantity
		self.current_holdings[fill.symbol] += cost
		self.current_holdings['commission'] += fill.commission
		self.current_holdings['cash'] -= (fill.fill_cost + fill.commission)
		self.current_holdings['total'] -= (fill.fill_cost + fill.commission)
		self.current_holdings['total'] += cost
	
	
	def update_signal(self, event):
		if event.type == 'SIGNAL':
			order_event = self.generate_naive_order(event)
			self.events.put(order_event)

						
	def generate_naive_order(self, signal):
		order = None
		
		symbol = signal.symbol
		direction = signal.signal_type
		
		# strength = signal.strength
		# mkt_quantity = floor(100 * strength)
		mkt_quantity = floor(100)
		cur_quantity = self.current_positions[symbol]
		
		# 'MKT' 市价交易，'LMT' 限价交易
		order_type = 'MKT'
		
		if direction == 'LONG' and cur_quantity == 0:
			order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
		if direction == 'SHORT' and cur_quantity == 0:
			order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
		
		# 平仓
		if direction == 'EXIT' and cur_quantity > 0:
			order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
		if direction == 'EXIT' and cur_quantity < 0:
			order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
			
		order.print_order()
		return order
	
	def create_equity_curve_dataframe(self):
		curve = pd.DataFrame(self.all_holdings)
		curve.set_index('datetime', inplace=True)
		curve['returns'] = curve['total'].pct_change()  # 计算百分比变化，也就是计算总市值的变化率
		curve['equity_curve'] = (1.0+curve['returns']).cumprod() #计算累计积，也就是从开始到此刻的市值总变化率
		self.equity_curve = curve # DataFrame
	
	def output_summary_stats(self):
		"""
		统计夏普率、最大回撤率等
		"""
		self.create_equity_curve_dataframe()
		
		total_return = self.equity_curve['equity_curve'][-1]
		returns = self.equity_curve['returns']
		pnl = self.equity_curve['equity_curve']
		
		sharpe_ratio = create_sharpe_ratio(returns) # 计算夏普率
		max_dd, dd_duration = create_drawdowns(pnl) # 计算最大回撤率及对应时间
		
		# %%是为了打出一个%
		stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),  
				 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
				 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
				 ("Drawdown Duration", "%d" % dd_duration)]
				 
				 
		return stats, self.equity_curve


