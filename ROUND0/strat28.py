from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import json

class Trader:

    def bid(self):
        return 15
    
    def run(self, state: TradingState):
        """Only method required. It takes all buy and sell orders for all
        symbols as an input, and outputs a list of orders to be sent."""

        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        print("Position: " + str(state.position))
        print("Own Trades: " + str(state.own_trades))
        print("Market Trades: " + str(state.market_trades))


               # --- Deserialize ---
        if state.traderData:
            data = json.loads(state.traderData)
        else:
            data = {
                "tomatoes_ma20": None,
                "tomatoes_ma20_trend": None,
                "tomatoes_ma50": None,
                "tomatoes_ma50_trend": None,
                "price_history": {},
                "ma20_history": [],
                "ma50_history": [],
                "trend_history": [],
                "round_count": 0,
                "last_best_bid": None,
                "last_best_ask": None,
            }

        # --- Update mid price history ---
        data["round_count"] += 1

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = list(order_depth.buy_orders.items())[0][0]
                best_ask = list(order_depth.sell_orders.items())[0][0]
                mid = (best_bid + best_ask) / 2

                if product not in data["price_history"]:
                    data["price_history"][product] = []

                data["price_history"][product].append(mid)
                data["price_history"][product] = data["price_history"][product][-50:]

        tomatoes_prices = data["price_history"].get("TOMATOES", [])

        # --- MA20 ---
        if len(tomatoes_prices) >= 1:
            last20 = tomatoes_prices[-20:]
            data["tomatoes_ma20"] = sum(last20) / len(last20)

            data["ma20_history"].append(data["tomatoes_ma20"])
            data["ma20_history"] = data["ma20_history"][-10:]


        # --- MA50 ---
        if len(tomatoes_prices) >= 1:
            last50 = tomatoes_prices[-50:]
            data["tomatoes_ma50"] = sum(last50) / len(last50)

            data["ma50_history"].append(data["tomatoes_ma50"])
            data["ma50_history"] = data["ma50_history"][-10:]

        # --- Compute trend: linear regression slope over last 10 MA20 values ---
        ma20_hist = data["ma20_history"]
        if len(ma20_hist) >= 2:
            n = len(ma20_hist)
            x_mean = (n - 1) / 2
            y_mean = sum(ma20_hist) / n
            numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(ma20_hist))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            data["tomatoes_ma20_trend"] = numerator / denominator if denominator != 0 else 0
        else:
            data["tomatoes_ma20_trend"] = None

        if data["tomatoes_ma20_trend"] is not None:
            data["trend_history"].append(data["tomatoes_ma20_trend"])
            data["trend_history"] = data["trend_history"][-10:]

        ma50_hist = data["ma50_history"]

        if len(ma50_hist) >= 2:
            n = len(ma50_hist)
            x_mean = (n - 1) / 2
            y_mean = sum(ma50_hist) / n
            numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(ma50_hist))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            data["tomatoes_ma50_trend"] = numerator / denominator if denominator != 0 else 0
        else:
            data["tomatoes_ma50_trend"] = None

        trend_hist = data["trend_history"]

        trend_change = None
        if len(trend_hist) >= 3:
            trend_change = trend_hist[-1] - trend_hist[-3]

        # --- Serialize (summary fields first) ---
        ordered_data = {
            "tomatoes_ma20": data["tomatoes_ma20"],
            "tomatoes_ma20_trend": data["tomatoes_ma20_trend"],
            "tomatoes_ma50": data["tomatoes_ma50"],
            "tomatoes_ma50_trend": data["tomatoes_ma50_trend"],
            "price_history": data["price_history"],
            "ma20_history": data["ma20_history"],
            "ma50_history": data["ma50_history"],
            "round_count": data["round_count"],
            "trend_history": data["trend_history"],
            "last_best_bid": best_bid,
            "last_best_ask": best_ask
        }
        traderData = json.dumps(ordered_data)


        # Orders to be placed on exchange matching engine
        result = {}
        POSITION_LIMIT = 25

        for product in state.order_depths:

            if product == "TOMATOES":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                if len(order_depth.sell_orders) != 0 and len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]

                    # 2nd best bid/ask (if available)
                    buy_orders  = list(order_depth.buy_orders.items())
                    sell_orders = list(order_depth.sell_orders.items())
                    second_best_bid = buy_orders[1][0]  if len(buy_orders)  >= 2 else None
                    second_best_ask = sell_orders[1][0] if len(sell_orders) >= 2 else None

                    last_bid = data.get("last_best_bid")
                    last_ask = data.get("last_best_ask")
                    trend = data.get("tomatoes_ma50_trend")

                    position = state.position.get(product, 0)

                    # --- Deviation orders ---
                    if last_bid is not None and last_ask is not None:

                        # Ask dropped significantly — cheap supply appeared, buy it then dime 2nd best bid
                        if last_ask - best_ask > 3:
                            qty = min(5, POSITION_LIMIT - position, -best_ask_amount)
                            if qty > 0 and trend is not None and trend > 0.02 and state.timestamp > 5_000:
                                if position < -20:
                                    orders.append(Order(product, best_ask, -best_ask_amount))
                                    print(f"[TOMATOES] Ask dropped {last_ask} -> {best_ask}, hitting ask for limit {-best_ask_amount}")
                                else:
                                    orders.append(Order(product, best_ask, qty))
                                    print(f"[TOMATOES] Ask dropped {last_ask} -> {best_ask}, hitting ask for {qty}")
                            if second_best_bid is not None and position + qty < POSITION_LIMIT:
                                orders.append(Order(product, second_best_bid + 1, min(5, POSITION_LIMIT - position - qty)))
                                print(f"[TOMATOES] Diming 2nd best bid at {second_best_bid + 1}")
                        else:
                            orders.append(Order(product, best_ask - 1, -10))
                            print(f"[TOMATOES] Placing SELL order at {best_ask - 1} because trend_change is {trend_change}")


                        # Bid jumped significantly — expensive buyer appeared, sell to them then dime 2nd best ask
                        if best_bid - last_bid > 3:
                            qty = min(5, position + POSITION_LIMIT, best_bid_amount)
                            if qty > 0 and trend is not None and trend < -0.02 and state.timestamp > 5_000:
                                if position > 20:
                                    orders.append(Order(product, best_bid, -best_bid_amount))
                                    print(f"[TOMATOES] Bid jumped {last_bid} -> {best_bid}, hitting bid for limit {-best_bid_amount}")
                                else:
                                    orders.append(Order(product, best_bid, -qty))
                                    print(f"[TOMATOES] Bid jumped {last_bid} -> {best_bid}, hitting bid for {qty}")
                            if second_best_ask is not None and position - qty > -POSITION_LIMIT:
                                orders.append(Order(product, second_best_ask - 1, -min(5, position + POSITION_LIMIT - qty)))
                                print(f"[TOMATOES] Diming 2nd best ask at {second_best_ask - 1}")
                        else:
                            orders.append(Order(product, best_bid + 1, 10))
                            print(f"[TOMATOES] Placing BUY order at {best_bid + 1} because trend_change is {trend_change}") 


            if product == "EMERALDS":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                print("[EMERALDS] Best bid : " + str(best_bid) + ", Best ask : " + str(best_ask))
        
                if len(order_depth.sell_orders) != 0 and best_ask > 10_000:
                    orders.append(Order(product, best_ask - 1, -10))
        
                if len(order_depth.buy_orders) != 0 and best_bid < 10_000:
                    orders.append(Order(product, best_bid + 1, 10))
            
            result[product] = orders
    
        conversions = 0
        return result, conversions, traderData