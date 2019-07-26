from .base import AbstractRiskManager
from ..event import OrderEvent


class ExampleRiskManager(AbstractRiskManager):
    def refine_orders(self, portfolio, sized_order):
        """
        This ExampleRiskManager object simply lets the
        sized order through, creates the corresponding
        OrderEvent object and adds it to a list.
        """
        order_event = OrderEvent(
            sized_order.symbol,
            sized_order.order_type,
            sized_order.quantity,
            sized_order.action
        )
        return [order_event]
