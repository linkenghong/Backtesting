import csv

class Position(object):
    def __init__(
        self, action, symbol, init_quantity,
        init_price, init_commission,
        cur_price
    ):
        """
        Set up the initial "account" of the Position.

        Then calculate the initial values and finally update the
        market value of the transaction.
        """
        self.action = action
        self.symbol = symbol
        self.quantity = init_quantity
        self.unavailable_quantity = init_quantity
        self.available_quantity = 0
        self.init_price = init_price
        self.price = round(init_price, 2)
        self.init_commission = init_commission
        self.total_commission = init_commission
        self.avg_price = 0
        if self.action == "BUY":
            self.avg_price = round((self.init_price * self.quantity + self.init_commission) / self.quantity , 2)        

        self.update_market_value(cur_price)


    def update_market_value(self, price):
        """
        Update market values with the latest price.
        """
        self.market_value = round(self.quantity * price, 2)
        

    def update_position(self):
        """
        At A share, trading rule is T+1, when it is a new day, the 
        available position should be update.
        """
        self.available_quantity += self.unavailable_quantity
        self.unavailable_quantity = 0


    def transact_shares(self, action, quantity, price, commission):
        """
        Calculates the adjustments to the Position that occur
        once new shares are bought and sold.
        """
        self.price = round(price, 2)
        self.total_commission += commission
        direction = 1 if action == "BUY" else -1
        self.unavailable_quantity += quantity
        lastest_quantity = self.quantity + direction * quantity
        if lastest_quantity > 0:
            self.avg_price = round((
                self.quantity * self.avg_price + commission 
                + direction * quantity * price
            ) / lastest_quantity , 2)

        self.quantity = lastest_quantity

    def record_position(self, fname, timestamp):
        with open(fname, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                timestamp, self.symbol, self.quantity,
                self.price, self.avg_price, self.market_value,
                self.total_commission
            ])

