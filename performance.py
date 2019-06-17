# coding=gbk
import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
	"""
	���������ʣ������޷�������Ϊ0
	Parameters:
	returns - A pandas Series representing period percentage returns.
	periods - Daily(252), Hourly(252*6), Minutely(252*6*60)
	���й�����������һ����252
	"""
	return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def create_drawdowns(equity_curve):
	"""
	�������س��ʼ���Ӧ��ʱ������
	Parameters:
	pnl - A pandas Series representing period percentage returns.
	
	Returns:
	drawdown, duration - Highest peak-to-trough drawdown and duration.
	"""
	
	# HWM(current high water mark)
	hwm = [0]
	eq_idx = equity_curve.index
	drawdown = pd.Series(index = eq_idx)
	duration = pd.Series(index = eq_idx)
	
	for t in range(1, len(eq_idx)):
		cur_hwm = max(hwm[t-1], equity_curve[t])
		hwm.append(cur_hwm)
		drawdown[t] = hwm[t] - equity_curve[t]
		duration[t] = 0 if drawdown[t] == 0 else duration[t-1] + 1
	return drawdown.max(), duration.max()



