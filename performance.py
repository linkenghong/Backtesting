# coding=gbk
import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
	"""
	计算夏普率，假设无风险利率为0
	Parameters:
	returns - A pandas Series representing period percentage returns.
	periods - Daily(252), Hourly(252*6), Minutely(252*6*60)
	在中国交易天数不一定是252
	"""
	return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def create_drawdowns(equity_curve):
	"""
	计算最大回撤率及对应的时间周期
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



