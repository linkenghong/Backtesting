# backtesting
此项目是基于[QuantStart](https://www.quantstart.com/articles)的系列文章并做了适当修改而来的。

参考：[qstrader](https://github.com/mhallsmoore/qstrader)

### 模块
* **data_handler_**：数据更新模块，产生新市场数据。
* **strategy**：策略模块，对市场数据进行分析，产生交易信号。
* **portfolio_handler**：投资组合模块，负责处理交易信号产生交易订单、根据新市场数据更新资产情况以及根据完成订单更新仓位及资产情况。对于交易信号产生的初始订单会经过仓位控制及风险控制两个模块最终产生交易订单。
* **execution_handler**：订单执行模块，模拟交易所完成交易订单，包括资金检查等。

### 基本逻辑
backtest.py是运行文件也是最基本的模块，它有内外两层循环，基本逻辑如下：
* 外层循环是更新数据的（stream_next()），用于记录股票实时价格。当continue_backtest为false表明没有新数据，回测结束
* 内层循环是以事件驱动方式处理事件，即事件队列不断出队直至为空后退回到外循环
* 当价格变化（stream_next()），会入队BarEvent事件
* 当价格变化后，strategy模块会判断是否做出买入、卖出或继续持有的信号，而portfolio_handler模块会根据实时价格更新现有资产总价格。即当出队事件是BarEvent，会触发strategy.calculate_signals()及portfolio_handler.update_portfolio_value()。如果发出操作信号，就会入队SignalEvent事件
* 当收到买卖信号，portfolio_handler模块会进行投资组合及风险控制，并产生订单order。即当出队事件是SignalEvent，会触发portfolio.on_signal()，入队OrderEvent事件
* 当收到订单，execution模块会执行订单，并发出完成信号，说明实际买卖股数、价格。即当出队事件是OrderEvent，会触发execution_handler.execute_order()，入队FillEvent事件
* 当收到订单执行完成信号，portfolio_handler模块会更新持有资产情况及总价格。即当出队事件是FillEvent，会触发portfolio.on_fill()


