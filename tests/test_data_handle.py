#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

import unittest
import queue
import sys
import os
import datetime

import testcommon
from Backtesting.data_handler.historic_csv_data_handler import HistoricCSVDataHandler


class TestDataHandler(unittest.TestCase):
    def setUp(self):
        events_queue = queue.Queue()
        data_dir = './data/'
        symbol_list = ["AAPL","SPY"]
        start_date = datetime.datetime(2003, 1 , 1)
        end_date = datetime.datetime(2014, 1, 30)
        #symbol_list = ["000001SZ_M"]
        #start_date = datetime.datetime(2018, 1, 2, 14, 59, 0)
        #end_date = datetime.datetime(2018, 1, 30)
        self.datahandler = HistoricCSVDataHandler(events_queue, data_dir, symbol_list, start_date, end_date)

    def test_stream_next(self):
        for i in range(5):
            self.datahandler.stream_next()

if __name__ == "__main__":
    unittest.main()