import queue
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt



from .event import EventType
from .data_handler.historic_csv_data_handler import HistoricCSVDataHandler
from .position_sizer.fixed import FixedPositionSizer
from .risk_manager.example import ExampleRiskManager
from .portfolio_handler.portfolio_handler import PortfolioHandler
from .execution_handler.ashare_simulated import AShareSimulatedExecutionHandler
from .statistics.tearsheet import TearsheetStatistics


class Backtest(object):
    def __init__(
        self, strategy, symbol_list,init_equity,
        start_date, end_date, events_queue,
        data_dir, output_dir,
        data_handler=None, portfolio_handler=None,
        position_sizer=None, execution_handler=None,
        risk_manager=None, statistics=None,
        title=None, benchmark=None
    ):
        self.strategy = strategy
        self.symbol_list = symbol_list
        self.init_equity = init_equity
        self.start_date = start_date
        self.end_date = end_date
        self.events_queue = events_queue
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.data_handler = data_handler
        self.portfolio_handler = portfolio_handler
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.statistics = statistics
        self.title = title
        self.benchmark = benchmark
        self._config_session()
        self.cur_time = None
    
    def _config_session(self):
        if self.data_handler is None:
            self.data_handler = HistoricCSVDataHandler(
                self.events_queue,
                self.data_dir,
                self.symbol_list,
                start_date=self.start_date,
                end_date=self.end_date
            )

        if self.position_sizer is None:
            self.position_sizer = FixedPositionSizer()

        if self.risk_manager is None:
            self.risk_manager = ExampleRiskManager()

        if self.portfolio_handler is None:
            self.portfolio_handler = PortfolioHandler(
                self.init_equity,
                self.events_queue,
                self.data_handler,
                self.position_sizer,
                self.risk_manager,
                self.output_dir
            )

        if self.execution_handler is None:
            self.execution_handler = AShareSimulatedExecutionHandler(
                self.events_queue,
                self.data_handler,
                self.portfolio_handler,
                self.output_dir
            )

        if self.statistics is None:
            self.statistics = TearsheetStatistics(
                self.output_dir,
                self.portfolio_handler,
                self.title, self.benchmark
            )

        self.strategy.set_portfolio(self.portfolio_handler)

    def _continue_loop_condition(self):
        return self.data_handler.continue_backtest

    def _need_backtest_condition(self):
        return self.data_handler.need_backtest
            
    def _run_session(self):
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop continue until the event queue has been
        emptied.
        """
        print("Running Backtest...")
        print("------------------------------------------------")

        while self._continue_loop_condition():
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                self.data_handler.stream_next()
            else:
                if event is not None:
                    if event.type == EventType.BAR:
                        if event.new_day == True:
                            self.portfolio_handler.update_portfolio_position()
                        self.cur_time = event.timestamp
                        self.strategy.calculate_signals(event)
                        self.portfolio_handler.update_portfolio_value()
                        self.statistics.update(event.timestamp, self.portfolio_handler)
                    elif event.type == EventType.SIGNAL:
                        self.portfolio_handler.on_signal(event)
                    elif event.type == EventType.ORDER:
                        self.execution_handler.execute_order(event)
                    elif event.type == EventType.FILL:
                        self.portfolio_handler.on_fill(event)
                    else:
                        raise NotImplemented("Unsupported event.type '%s'" % event.type)

    def start_trading(self, testing=False):

        if self._need_backtest_condition():
            self._run_session()
            results = self.statistics.get_results()
            print("------------------------------------------------")
            print("Backtest complete.")
            print("Sharpe Ratio: %0.2f" % results["sharpe"])
            print(
                "Max Drawdown: %0.2f%%" % (
                    results["max_drawdown_pct"] * 100.0
                )
            )
            print(
                "Cum Returns: %0.2f%%" % (
                    results["total_return"] * 100.0
                )
            )
            if not testing:
                self.statistics.save()
                #self.statistics.plot_results()
            return results
        else:
            return None
 

