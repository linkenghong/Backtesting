# coding=gbk
from abc import ABC, abstractmethod

class AbstractRiskManager(ABC):
    """
    The AbstractRiskManager abstract class lets the
    sized order through, creates the corresponding
    OrderEvent object and adds it to a list.
    """

    def __init__(self):
        pass

    @abstractmethod
    def refine_orders(self, portfolio, sized_order):
        raise NotImplementedError("Should implement refine_orders()")
