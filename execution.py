# coding=gbk
import datetime
import queue

from abc import ABCMeta, abstractmethod

from event import FillEvent, OrderEvent

class ExecutionHandler(object):
	__metaclass__ = ABCMeta
	
	@abstractmethod
	def execute_order(self, event):
		raise NotImplementedError("Should implement execute_order()")
		
		
class SimulatedExecutionHandler(ExecutionHandler):
	def __init__(self, bars, events):
		"""
		Parameters:
		events - The Queue of Event objects.
		"""
		self.bars = bars
		self.events = events
		
	def execute_order(self, event):
		"""
		以ARCA交易所作为交易地
		Parameters:
		event - Contains and Event object with order information.
		"""
		
		if event.type == 'ORDER':
			fill_cost = self.bars.get_latest_bars(event.symbol)[0][5] # close price
			cost = fill_cost * event.quantity
			fill_event = FillEvent(datetime.datetime.utcnow(), event.symbol,
									'ARCA', event.quantity, event.direction, cost, )
			self.events.put(fill_event)
