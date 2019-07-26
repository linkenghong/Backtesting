
class Position(object):
    def __init__(
        self, action, symbol, init_quantity,
        init_price, init_commission,
        cur_price
    ):
        """
        Set up the initial "account" of the Position to be
        zero for most items, with the exception of the initial
        purchase/sale.

        Then calculate the initial values and finally update the
        market value of the transaction.
        """
        self.action = action
        self.symbol = symbol
        self.quantity = init_quantity
        self.init_price = init_price
        self.init_commission = init_commission
        self.total_commission = init_commission
        self.avg_price = 0
        if self.action == "BUY":
            self.avg_price = round((self.init_price * self.quantity + self.init_commission) / self.quantity , 2)        

        self.update_market_value(cur_price)


    def update_market_value(self, price):
        """
        The market value is tricky to calculate as we only have
        access to the top of the order book through Interactive
        Brokers, which means that the true redemption price is
        unknown until executed.

        However, it can be estimated via the mid-price of the
        bid-ask spread. Once the market value is calculated it
        allows calculation of the unrealised and realised profit
        and loss of any transactions.
        """
        self.market_value = self.quantity * price
        

    def transact_shares(self, action, quantity, price, commission):
        """
        Calculates the adjustments to the Position that occur
        once new shares are bought and sold.

        Takes care to update the average bought/sold, total
        bought/sold, the cost basis and PnL calculations,
        as carried out through Interactive Brokers TWS.
        """
        self.total_commission += commission
        direction = 1 if action == "BUY" else -1
        lastest_quantity = self.quantity + direction * quantity
        if lastest_quantity > 0:
            self.avg_price = round((
                self.quantity * self.avg_price + commission 
                + direction * quantity * price
            ) / lastest_quantity , 2)

        self.quantity = lastest_quantity

