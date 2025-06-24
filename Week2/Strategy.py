
from src.backtester import Order, OrderBook
from typing import List
import pandas as pd
import numpy as np
import statistics

class BaseClass:
    def __init__(self, product_name, max_position):
        self.product_name = product_name
        self.max_position = max_position

    def get_orders(self, state, orderbook, position):
        return []

class SudowoodoStrategy(BaseClass):
    def __init__(self):
        super().__init__("SUDOWOODO", 50)
        self.fair_value = 10000

    def get_orders(self, state, orderbook, position):
        orders = []
        if not orderbook.buy_orders and not orderbook.sell_orders:
            return orders

        orders.append(Order(self.product_name, self.fair_value + 2, -10))
        orders.append(Order(self.product_name, self.fair_value - 2, 10))
        return orders

class DrowzeeStrategy(BaseClass):
    def __init__(self):
        super().__init__("DROWZEE", 50)

    def get_orders(self, state, orderbook, position):
        orders = []
        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_bid = max(orderbook.buy_orders.keys())
        best_bid_volume = orderbook.buy_orders[best_bid]
        best_ask = min(orderbook.sell_orders.keys())
        best_ask_volume = orderbook.sell_orders[best_ask]
        spread = best_ask - best_bid

        if spread <= 4:
            if position < self.max_position:
                orders.append(Order(self.product_name, best_bid, 10))
            if position > -self.max_position:
                orders.append(Order(self.product_name, best_ask, -10))

        return orders

class AbraStrategy(BaseClass):
    def __init__(self):
        super().__init__("ABRA", 50)
        self.reversion_window = 20
        self.mid_prices = []

    def get_orders(self, state, orderbook, position):
        orders = []

        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_ask = min(orderbook.sell_orders.keys())
        best_bid = max(orderbook.buy_orders.keys())
        mid_price = (best_ask + best_bid) / 2

        self.mid_prices.append(mid_price)
        if len(self.mid_prices) > self.reversion_window:
            self.mid_prices.pop(0)

        if len(self.mid_prices) < self.reversion_window:
            return orders

        mean_price = statistics.mean(self.mid_prices)
        std_dev = statistics.stdev(self.mid_prices)
        upper_threshold = mean_price + 1.5 * std_dev
        lower_threshold = mean_price - 1.5 * std_dev

        if best_ask < lower_threshold and position < self.max_position:
            buy_amount = min(-orderbook.sell_orders[best_ask], self.max_position - position)
            orders.append(Order(self.product_name, best_ask, buy_amount))

        if best_bid > upper_threshold and position > -self.max_position:
            sell_amount = min(orderbook.buy_orders[best_bid], position + self.max_position)
            orders.append(Order(self.product_name, best_bid, -sell_amount))

        return orders

class Trader:
    def __init__(self):
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "DROWZEE": DrowzeeStrategy(),
            "ABRA": AbraStrategy()
        }

    def run(self, state):
        result = {}
        positions = getattr(state, 'positions', {})
        
        for product, orderbook in state.order_depth.items():
            if product in self.strategies:
                current_position = positions.get(product, 0)
                product_orders = self.strategies[product].get_orders(state, orderbook, current_position)
                result[product] = product_orders

        return result
