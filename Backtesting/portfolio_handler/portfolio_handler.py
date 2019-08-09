from ..order.suggested import SuggestedOrder
from .portfolio import Portfolio


class PortfolioHandler(object):
    def __init__(
        self, initial_cash, events_queue, data_handler,
         position_sizer, risk_manager, output_dir
    ):
        """
        Each PortfolioHandler contains a Portfolio object,
        which stores the actual Position objects.

        The PortfolioHandler takes a handle to a PositionSizer
        object which determines a mechanism, based on the current
        Portfolio, as to how to size a new Order.

        The PortfolioHandler also takes a handle to the
        RiskManager, which is used to modify any generated
        Orders to remain in line with risk parameters.
        """
        self.initial_cash = initial_cash
        self.events_queue = events_queue
        self.data_handler = data_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.output_dir = output_dir
        self.portfolio = Portfolio(data_handler, initial_cash, output_dir)

    def _create_order_from_signal(self, signal_event):
        """
        Take a SignalEvent object and use it to form a
        SuggestedOrder object. These are not OrderEvent objects,
        as they have yet to be sent to the RiskManager object.
        At this stage they are simply "suggestions" that the
        RiskManager will either verify, modify or eliminate.
        """
        if signal_event.suggested_quantity is None:
            quantity = 0
        else:
            quantity = signal_event.suggested_quantity
        order = SuggestedOrder(
            signal_event.symbol,
            signal_event.action,
            order_type = signal_event.order_type,
            quantity = quantity
        )
        return order

    def _place_orders_onto_queue(self, order_list):
        """
        Once the RiskManager has verified, modified or eliminated
        any order objects, they are placed onto the events queue,
        to ultimately be executed by the ExecutionHandler.
        """
        for order_event in order_list:
            self.events_queue.put(order_event)

    def _convert_fill_to_portfolio_update(self, fill_event):
        """
        Upon receipt of a FillEvent, the PortfolioHandler converts
        the event into a transaction that gets stored in the Portfolio
        object. This ensures that the broker and the local portfolio
        are "in sync".

        In addition, for backtesting purposes, the portfolio value can
        be reasonably estimated in a realistic manner, simply by
        modifying how the ExecutionHandler object handles slippage,
        transaction costs, liquidity and market impact.
        """
        timestamp = fill_event.timestamp
        action = fill_event.action
        symbol = fill_event.symbol
        quantity = fill_event.quantity
        price = fill_event.price
        commission = fill_event.commission
        # Create or modify the position from the fill info
        self.portfolio.transact_position(
            timestamp, action, symbol,
            quantity, price, commission
        )

    def on_signal(self, signal_event):
        """
        This is called by the backtester or live trading architecture
        to form the initial orders from the SignalEvent.

        These orders are sized by the PositionSizer object and then
        sent to the RiskManager to verify, modify or eliminate.

        Once received from the RiskManager they are converted into
        full OrderEvent objects and sent back to the events queue.
        """
        # Create the initial order list from a signal event
        initial_order = self._create_order_from_signal(signal_event)
        # Size the quantity of the initial order
        sized_order = self.position_sizer.size_order(
            self.portfolio, initial_order
        )
        # Refine or eliminate the order via the risk manager overlay
        order_events = self.risk_manager.refine_orders(
            self.portfolio, sized_order
        )
        # Place orders onto events queue
        self._place_orders_onto_queue(order_events)

    def on_fill(self, fill_event):
        """
        This is called by the backtester or live trading architecture
        to take a FillEvent and update the Portfolio object with new
        or modified Positions.

        In a backtesting environment these FillEvents will be simulated
        by a model representing the execution, whereas in live trading
        they will come directly from a brokerage (such as Interactive
        Brokers).
        """
        self._convert_fill_to_portfolio_update(fill_event)

    def update_portfolio_value(self):
        """
        Update the portfolio to reflect current market value.
        """
        self.portfolio._update_portfolio()

    def update_portfolio_position(self):
        """
        Update the available position.
        """
        self.portfolio._update_position()