#backtesting

This repository is based on the article series written by [QuantStart]()

a hand-written (no copying and pasting here, noob!), slightly modified code, of an eightseven-part* 

Event-Driven Backtesting with Python - Part I
Event-Driven Backtesting with Python - Part II
Event-Driven Backtesting with Python - Part III
Event-Driven Backtesting with Python - Part IV
Event-Driven Backtesting with Python - Part V
Event-Driven Backtesting with Python - Part VI
Event-Driven Backtesting with Python - Part VII
Event-Driven Backtesting with Python - Part VIII
###Purpose I wanted to put together the code from the articles to better understand the event-based part of the code. The basic logic of loop.py is:

update_data() puts a MarketEvent() into the queue
calculate_signals() processes the MarketEvent() and puts a SignalEvent() into the queue
update_signal() processes an OrderEvent()
execute_order() puts a FillEvent() into the queue
update_fill() emits NO event so queue is Empty which breaks inner While loop
return to outer While loop
continue looping until data.continue_backtest == False, at which time loop will end after next MarketEvent()
###Notes

I say eightseven-part article series because Part VIII is specifically for corresponding with Interactive Broker's API, which is beyond the scope of the academic exercise this repository represents.
It is important to note the aggregate of the code as-is from the series does not work. The code has missing logic and minor variable naming mismatches.
I tried to keep my variable/method naming conventions very similar to their originals so one can more easily compare my code to the articles
I took the liberty to make many minor logic changes (e.g. QuantStart's Portfolio() has dict((k,v) for k, v in [(s, 0) for s in self.symbol_list])) and I have {symbol: 0 for symbol in self.symbol_list}
The QuantStart code is full of opportunities for DRY and encapsulation improvements, some of which I made and plenty more I left alone
