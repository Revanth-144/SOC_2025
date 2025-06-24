
from typing import List, Dict
from statistics import mean, stdev
from src.backtester import Order, OrderBook

class Trader:
    def __init__(self):
        self.mid_prices = []  # track mid-prices
        self.window_size = 20  # rolling window

    def run(self, state, current_position: int) -> Dict[str, List[Order]]:
        result = {}
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        # Compute mid-price and update history
        if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
            best_bid = max(order_depth.buy_orders.keys())
            mid_price = (best_ask + best_bid) / 2
            self.mid_prices.append(mid_price)
            if len(self.mid_prices) > self.window_size:
                self.mid_prices.pop(0)

        if len(self.mid_prices) < self.window_size:
            # Not enough data yet
            result["PRODUCT"] = []
            return result

        mean_price = mean(self.mid_prices)
        std_dev = stdev(self.mid_prices)

        # Thresholds for decision
        upper_threshold = mean_price + 1.5 * std_dev
        lower_threshold = mean_price - 1.5 * std_dev

        # Buy logic
        if len(order_depth.sell_orders) > 0:
            best_ask, best_ask_amount = sorted(order_depth.sell_orders.items())[0]
            if best_ask < lower_threshold and current_position < 50:
                buy_amount = min(-best_ask_amount, 50 - current_position)
                orders.append(Order("PRODUCT", best_ask, buy_amount))

        # Sell logic
        if len(order_depth.buy_orders) > 0:
            best_bid, best_bid_amount = sorted(order_depth.buy_orders.items(), reverse=True)[0]
            if best_bid > upper_threshold and current_position > -50:
                sell_amount = min(best_bid_amount, current_position + 50)
                orders.append(Order("PRODUCT", best_bid, -sell_amount))

        result["PRODUCT"] = orders
        return result
