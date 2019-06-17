# backtesting
此项目是基于[QuantStart](https://www.quantstart.com/articles)的系列文章并做了适当修改而来的。

### 模块
* data.py：更新数据
* strategy.py：策略模块
* portfolio.py：投资组合模块及风险控制
* execution.py：订单执行模块

### 基本逻辑
backtest.py是运行文件也是最基本的模块，它有内外两层循环，基本逻辑如下：
* 外层循环是更新数据的（update_bars()），用于记录股票实时价格。当continue_backtest为false表明没有新数据，回测结束
* 内层循环是以事件驱动方式处理事件，即事件队列不断出队直至为空后退回到外循环
* 当价格变化（update_bars()），会入队MarketEvent事件
* 当价格变化后，strategy模块会判断是否做出买入、卖出或继续持有的信号，而portfolio模块会根据实时价格更新现有资产总价格。即当出队事件是MarketEvent，会触发strategy.calculate_signals()及portfolio.update_timeindex()。如果发出操作信号，就会入队SignalEvent事件
* 当收到买卖信号，portfolio模块会进行投资组合及风险控制，并产生订单order，在本程序中则只是简单的买100股操作信号所指定的股票。即当出队事件是SignalEvent，会触发portfolio.update_signal()，入队OrderEvent事件
* 当收到订单，execution模块会执行订单，并发出完成信号，说明实际买卖股数、价格。即当出队事件是OrderEvent，会触发execution.execute_order()，入队FillEvent事件
* 当收到订单执行完成信号，portfolio模块会更新持有资产情况及总价格。即当出队事件是FillEvent，会触发portfolio.update_fill()


