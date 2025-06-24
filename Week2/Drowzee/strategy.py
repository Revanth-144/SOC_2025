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
        result = {}  # Stores your orders
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        if not order_depth.buy_orders or not order_depth.sell_orders:
            return {"PRODUCT": orders}

        # Best bid and ask
        best_bid, bid_vol = max(order_depth.buy_orders.items(), key=lambda x: int(x[0]))

        best_ask, ask_vol = min(order_depth.sell_orders.items(), key=lambda x: int(x[0]))

        # If the spread is reasonable (say <= 4), we consider adding liquidity
        if int(best_ask) - int(best_bid) <= 4:
            # If we have room to buy
            if current_position < 50:
                orders.append(Order("PRODUCT", int(best_bid), 10))  # buy 10 at best bid

            # If we have holdings to sell
            if current_position > -50:
                orders.append(Order("PRODUCT", int(best_ask), -10))  # sell 10 at best ask

        result["PRODUCT"] = orders
        return result
