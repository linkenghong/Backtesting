# coding=gbk
import datetime
import os, os.path
import pandas as pd

from abc import ABCMeta, abstractmethod
from event import MarketEvent

class DataHandler(object):
	__metaclass__ = ABCMeta
	
	@abstractmethod
	def get_latest_bars(self, symbol, N=1):
		raise NotImplementedError("Should implement get_latest_bars()")
		
	@abstractmethod
	def update_bars(self):
		raise NotImplementedError("Should implement update_bars()")
	
		
class HistoricCSVDataHandler(DataHandler):
	def __init__(self, events, csv_dir, symbol_list):
		"""
		ͨ������CSV�ļ�����Ʊ�����嵥����ʼ����ʷ����

        Parameters:
        events - The Event Queue.
        csv_dir - Absolute directory path to the CSV files.
        symbol_list - A list of symbol strings.
		"""
		self.events = events
		self.csv_dir = csv_dir
		self.symbol_list = symbol_list
		
		self.symbol_data = {} # �ֵ�:{symbol:DataFrame}
		self.latest_symbol_data = {} # ����bar���ֵ䣺{symbol:[bar1, bar2, barNew]}
		self.continue_backtest = True
		
		self._open_convert_csv_files()
		
	def _open_convert_csv_files(self):
		comb_index = None
		for s in self.symbol_list:
			"""
			��ȡCSV�ļ���index_col=0��ʾ�Ե�һ�У�datetime����Ϊ�����У�
			���������comb_index������ȫ��ʱ�����У�
			header=0��ʾ���������У�����names���ʾ��names�滻ԭ������
			parse_dates�ǽ�index����������
			"""
			self.symbol_data[s] = pd.io.parsers.read_csv(
									os.path.join(self.csv_dir, '%s.csv' % s),
									header=0, index_col=0, parse_dates=True,
									names=['datetime','open','low','high','close','volume','oi']
									).sort_index()
			if comb_index is None:
				comb_index = self.symbol_data[s].index
			else:
				comb_index.union(self.symbol_data[s].index)
			
			self.latest_symbol_data[s] = []
			
		for s in self.symbol_list:
			"""
			������������comb_index����ȫʱ�����У�����Щ��Ʊ��������Щʱ��û�±仯��
			����method='pad'������ǰһ�̵���Ϣд��ȱ�ٵ�����ʱ��
			����symbol_data[s]��Dataframe������iterrows()������generator
			Output - generator
			"""
			self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()
			# print(self.symbol_data[s])

			
	def _get_new_bar(self, symbol):
		# Output - tuple
		row = next(self.symbol_data[symbol])
		# Output - row[0]: str, row[1]: pandas.Series
		row_tuple = (symbol, row[0], row[1][0], row[1][1], row[1][2], row[1][3])
		return row_tuple
	
	def get_latest_bars(self, symbol, N=1):
		# 
		try:
			bars_list = self.latest_symbol_data[symbol]
		except KeyError:
			print("That symbol is not available in the historical data set.")
		else:
			return bars_list[-N:]
	
	def update_bars(self):
		for s in self.symbol_list:
			try:
				bar = self._get_new_bar(s) # tuple
				# print(bar)
			except StopIteration:
				self.continue_backtest = False
			else:
				if bar is not None:
					self.latest_symbol_data[s].append(bar)
		self.events.put(MarketEvent())
		
			
		
		
