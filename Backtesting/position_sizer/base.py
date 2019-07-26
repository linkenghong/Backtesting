# coding=gbk
from abc import ABC, abstractmethod


class AbstractPositionSizer(ABC):
    """
    The AbstractPositionSizer abstract class modifies
    the quantity (or not) of any share transacted
    """

    @abstractmethod
    def size_order(self, portfolio, initial_order):
        """
        This TestPositionSizer object simply modifies
        the quantity to be 100 of any share transacted.
        """
        raise NotImplementedError("Should implement size_order()")
    
    def check_short(self, portfolio, initial_order):
        pass