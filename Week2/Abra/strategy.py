from src.backtester import Order, OrderBook
from typing import List

class Trader:
    '''
    state:
    - state.timestamp: Int
    - state.order_depth: OrderBook
    current_position: Int
    '''
    def run(self, state, current_position):
        result = {}  # Stores orders by product
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        if not order_depth.buy_orders or not order_depth.sell_orders:
            result["PRODUCT"] = orders
            return result

        # Sort bids and asks to find best
        best_ask, ask_vol = min(order_depth.sell_orders.items(), key=lambda x: x[0])  # lowest sell
        best_bid, bid_vol = max(order_depth.buy_orders.items(), key=lambda x: x[0])  # highest buy

        spread = best_ask - best_bid
        mid = (best_ask + best_bid) / 2

        # If we think it's profitable, we buy at or below a small discount from the midpoint
        buy_price = int(mid - spread * 0.25)  # buy lower than midpoint by 25% of spread
        sell_price = int(mid + spread * 0.25)  # sell higher than midpoint by 25% of spread

        if best_ask <= buy_price:
            amount = ask_vol
            orders.append(Order("PRODUCT", best_ask, amount))  # buy all available at this price

        if best_bid >= sell_price:
            amount = bid_vol
            orders.append(Order("PRODUCT", best_bid, -amount))  # sell all we have to this buyer

        result["PRODUCT"] = orders
        return result
