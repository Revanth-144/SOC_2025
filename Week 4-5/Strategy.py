from typing import List, Dict
from statistics import mean, stdev
from collections import deque
import math
from src.backtester import Order, OrderBook

class BaseClass:
    def __init__(self, product_name, max_position):
        self.product_name = product_name
        self.max_position = max_position

    def get_orders(self, state, orderbook, position):
        return []

class SudowoodoStrategy(BaseClass):
    def __init__(self):
        super().__init__('SUDOWOODO', 50)
        self.fair_value = 10000
        self.tick_size = 1
        self.min_spread = 2

    def get_orders(self, state, orderbook, position):
        orders = []
        best_bid = max(orderbook.buy_orders.keys()) if orderbook.buy_orders else None
        best_ask = min(orderbook.sell_orders.keys()) if orderbook.sell_orders else None

        if best_bid is None or best_ask is None:
            return orders

        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        
        # Aggressive market making with tight spreads
        if spread > self.min_spread:
            # Place orders inside the spread
            buy_price = best_bid + self.tick_size
            sell_price = best_ask - self.tick_size
        else:
            # Widen spread slightly around mid
            buy_price = mid - 1
            sell_price = mid + 1

        # Dynamic position sizing based on current position
        max_order_size = 15
        position_factor = 1 - abs(position) / self.max_position
        order_size = int(max_order_size * position_factor)
        
        if position < self.max_position and order_size > 0:
            orders.append(Order(self.product_name, int(buy_price), min(order_size, self.max_position - position)))
        if position > -self.max_position and order_size > 0:
            orders.append(Order(self.product_name, int(sell_price), -min(order_size, position + self.max_position)))

        return orders

class DrowzeeStrategy(BaseClass):
    def __init__(self):
        super().__init__('DROWZEE', 50)
        self.history = deque(maxlen=50)  # Shorter window for faster signals
        self.volume_history = deque(maxlen=20)

    def get_orders(self, state, orderbook, position):
        orders = []
        best_bid = max(orderbook.buy_orders.keys()) if orderbook.buy_orders else None
        best_ask = min(orderbook.sell_orders.keys()) if orderbook.sell_orders else None

        if best_bid is None or best_ask is None:
            return orders

        mid = (best_bid + best_ask) / 2
        self.history.append(mid)
        
        # Track volume at best levels
        bid_volume = orderbook.buy_orders.get(best_bid, 0)
        ask_volume = orderbook.sell_orders.get(best_ask, 0)
        volume_imbalance = bid_volume - ask_volume
        
        if len(self.history) < 10:
            return orders

        # Use shorter-term and longer-term averages
        short_avg = mean(list(self.history)[-10:])
        long_avg = mean(self.history)
        std_dev = stdev(self.history)
        
        # Mean reversion with momentum confirmation
        momentum = mid - long_avg
        volatility_factor = std_dev / mid if mid > 0 else 0
        
        # Adjust thresholds based on volatility
        buy_threshold = -0.8 * std_dev
        sell_threshold = 0.8 * std_dev
        
        # Order sizing based on confidence
        base_size = 12
        confidence_multiplier = min(2.0, abs(momentum) / std_dev) if std_dev > 0 else 1.0
        order_size = int(base_size * confidence_multiplier)
        
        if momentum < buy_threshold and position < self.max_position:
            # Buy signal - price below short average
            price = best_bid + 1 if volume_imbalance > 0 else best_bid
            orders.append(Order(self.product_name, price, min(order_size, self.max_position - position)))
        elif momentum > sell_threshold and position > -self.max_position:
            # Sell signal - price above short average  
            price = best_ask - 1 if volume_imbalance < 0 else best_ask
            orders.append(Order(self.product_name, price, -min(order_size, position + self.max_position)))

        return orders

class AbraStrategy(BaseClass):
    def __init__(self):
        super().__init__('ABRA', 50)
        self.history = deque(maxlen=80)
        self.trend_history = deque(maxlen=20)

    def get_orders(self, state, orderbook, position):
        orders = []
        best_bid = max(orderbook.buy_orders.keys()) if orderbook.buy_orders else None
        best_ask = min(orderbook.sell_orders.keys()) if orderbook.sell_orders else None

        if best_bid is None or best_ask is None:
            return orders

        mid = (best_bid + best_ask) / 2
        self.history.append(mid)
        
        if len(self.history) < 20:
            return orders

        avg = mean(self.history)
        std_dev = stdev(self.history)
        z_score = (mid - avg) / std_dev if std_dev > 0 else 0
        
        # Calculate trend
        recent_prices = list(self.history)[-10:]
        trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        self.trend_history.append(trend)
        
        # Combine mean reversion with trend following
        trend_strength = abs(trend) / std_dev if std_dev > 0 else 0
        
        # Dynamic thresholds
        base_threshold = 1.2
        trend_adjustment = 0.3 * trend_strength
        
        buy_threshold = -(base_threshold + trend_adjustment)
        sell_threshold = base_threshold + trend_adjustment
        
        # Position sizing with risk management
        max_order = 15
        risk_factor = 1 - abs(position) / self.max_position
        order_size = int(max_order * risk_factor)
        
        if z_score < buy_threshold and position < self.max_position:
            # Strong buy signal
            price = best_bid + 1 if trend > 0 else best_bid
            orders.append(Order(self.product_name, price, min(order_size, self.max_position - position)))
        elif z_score > sell_threshold and position > -self.max_position:
            # Strong sell signal
            price = best_ask - 1 if trend < 0 else best_ask
            orders.append(Order(self.product_name, price, -min(order_size, position + self.max_position)))

        return orders

class PairsTradingStrategy(BaseClass):
    def __init__(self, name, max_position, pair_name):
        super().__init__(name, max_position)
        self.pair_name = pair_name
        self.spread_history = deque(maxlen=100)
        self.hedge_ratio = 1.0  # Will be dynamically calculated

    def calculate_hedge_ratio(self):
        """Calculate optimal hedge ratio using recent price movements"""
        if len(self.spread_history) < 30:
            return 1.0
        
        # Simple correlation-based hedge ratio
        recent_spreads = list(self.spread_history)[-30:]
        variance = stdev(recent_spreads) ** 2
        return max(0.5, min(2.0, 1.0 / (1.0 + variance)))

    def get_orders(self, state, orderbook, position):
        if self.pair_name not in state.order_depth:
            return []
        
        this_ob = orderbook
        pair_ob = state.order_depth[self.pair_name]
        
        if not (this_ob.buy_orders and this_ob.sell_orders and pair_ob.buy_orders and pair_ob.sell_orders):
            return []
        
        this_mid = (max(this_ob.buy_orders.keys()) + min(this_ob.sell_orders.keys())) / 2
        pair_mid = (max(pair_ob.buy_orders.keys()) + min(pair_ob.sell_orders.keys())) / 2
        
        spread = this_mid - self.hedge_ratio * pair_mid
        self.spread_history.append(spread)

        if len(self.spread_history) < 30:
            return []

        # Update hedge ratio periodically
        self.hedge_ratio = self.calculate_hedge_ratio()

        avg_spread = mean(self.spread_history)
        std_spread = stdev(self.spread_history)
        z_score = (spread - avg_spread) / std_spread if std_spread > 0 else 0

        orders = []
        
        # More aggressive thresholds for pairs trading
        entry_threshold = 1.5
        exit_threshold = 0.3
        
        # Entry signals
        if z_score > entry_threshold and position > -self.max_position:
            # Spread too high - sell this, buy pair
            orders.append(Order(self.product_name, min(this_ob.sell_orders.keys()), -12))
        elif z_score < -entry_threshold and position < self.max_position:
            # Spread too low - buy this, sell pair
            orders.append(Order(self.product_name, max(this_ob.buy_orders.keys()), 12))
        
        # Exit signals when spread normalizes
        elif abs(z_score) < exit_threshold and abs(position) > 5:
            # Close position
            if position > 0:
                orders.append(Order(self.product_name, min(this_ob.sell_orders.keys()), -min(8, position)))
            elif position < 0:
                orders.append(Order(self.product_name, max(this_ob.buy_orders.keys()), min(8, -position)))
        
        return orders

class IndexStrategy(BaseClass):
    def __init__(self, name, max_position, weights):
        super().__init__(name, max_position)
        self.weights = weights
        self.price_history = deque(maxlen=100)
        self.fair_value_history = deque(maxlen=50)

    def compute_fair_value(self, state):
        price = 0
        total_weight = 0
        for prod, weight in self.weights.items():
            orderbook = state.order_depth.get(prod)
            if orderbook and orderbook.buy_orders and orderbook.sell_orders:
                mid = (max(orderbook.buy_orders.keys()) + min(orderbook.sell_orders.keys())) / 2
                price += weight * mid
                total_weight += weight
        return price / total_weight if total_weight > 0 else 0

    def get_orders(self, state, orderbook, position):
        orders = []
        fair = self.compute_fair_value(state)
        
        if fair == 0:
            return orders
            
        best_bid = max(orderbook.buy_orders.keys()) if orderbook.buy_orders else None
        best_ask = min(orderbook.sell_orders.keys()) if orderbook.sell_orders else None

        if best_bid is None or best_ask is None:
            return orders

        mid = (best_bid + best_ask) / 2
        self.price_history.append(mid)
        self.fair_value_history.append(fair)

        premium = mid - fair
        
        # Dynamic threshold based on recent volatility
        if len(self.fair_value_history) > 20:
            fair_vol = stdev(self.fair_value_history)
            threshold = max(1.0, fair_vol * 2.0)
        else:
            threshold = 2.0
        
        # Larger position sizes for index arbitrage
        unit = min(15, self.max_position // 3)
        
        # Check if we have enough capital for hedging
        can_hedge = True
        for prod in self.weights.keys():
            if prod not in state.order_depth:
                can_hedge = False
                break
        
        if not can_hedge:
            return orders

        if premium > threshold and position > -self.max_position:
            # Index overpriced - sell index, buy components
            orders.append(Order(self.product_name, best_ask, -unit))
            
            # Hedge with components
            for prod, weight in self.weights.items():
                ref_ob = state.order_depth[prod]
                if ref_ob.sell_orders:
                    ask = min(ref_ob.sell_orders.keys())
                    hedge_size = max(1, int(weight * unit))
                    orders.append(Order(prod, ask, hedge_size))
                    
        elif premium < -threshold and position < self.max_position:
            # Index underpriced - buy index, sell components
            orders.append(Order(self.product_name, best_bid, unit))
            
            # Hedge with components
            for prod, weight in self.weights.items():
                ref_ob = state.order_depth[prod]
                if ref_ob.buy_orders:
                    bid = max(ref_ob.buy_orders.keys())
                    hedge_size = max(1, int(weight * unit))
                    orders.append(Order(prod, bid, -hedge_size))
        
        return orders

class Trader:
    MAX_LIMIT = 0

    def __init__(self):
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "DROWZEE": DrowzeeStrategy(),
            "ABRA": AbraStrategy(),
            "SHINX": PairsTradingStrategy("SHINX", 60, "JOLTEON"),
            "LUXRAY": PairsTradingStrategy("LUXRAY", 250, "JOLTEON"),
            "JOLTEON": PairsTradingStrategy("JOLTEON", 350, "LUXRAY"),
            "ASH": IndexStrategy("ASH", 60, {"LUXRAY": 0.6, "JOLTEON": 0.3, "SHINX": 0.1}),
            "MISTY": IndexStrategy("MISTY", 100, {"LUXRAY": 0.67, "JOLTEON": 0.33}),
            "PRODUCT": BaseClass("PRODUCT", 50),
        }

    def run(self, state):
        positions = getattr(state, 'positions', {})
        order_depth = getattr(state, 'order_depth', {})

        if len(order_depth) == 1 and "PRODUCT" in order_depth:
            product = "PRODUCT"
            strategy = self.strategies[product]
            current_position = positions.get(product, 0)
            product_orders = strategy.get_orders(state, order_depth[product], current_position)
            self.MAX_LIMIT = strategy.max_position
            return product_orders, self.MAX_LIMIT

        result = {}
        for product, orderbook in order_depth.items():
            current_position = positions.get(product, 0)
            strategy = self.strategies.get(product, BaseClass(product, 50))
            result[product] = strategy.get_orders(state, orderbook, current_position)

        return result, self.MAX_LIMIT