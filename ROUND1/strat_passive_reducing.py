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
                "round_count": 0,
            }

        # --- Update mid price history ---
        data["round_count"] += 1

        ## Save best bid per product for next round comparison

        for product in state.order_depths:
            if product == "ASH_COATED_OSMIUM":
                order_depth = state.order_depths[product]
                if order_depth.buy_orders:
                    best_bid_osmium = list(order_depth.buy_orders.items())[0][0]
                else:
                        best_bid_osmium = None
                if order_depth.sell_orders:
                        best_ask_osmium = list(order_depth.sell_orders.items())[0][0]
                else:
                    best_ask_osmium = None
                if best_bid_osmium is not None and best_ask_osmium is not None:
                    mid = (best_bid_osmium + best_ask_osmium) / 2

            if product == "INTARIAN_PEPPER_ROOT":
                order_depth = state.order_depths[product]
                if order_depth.buy_orders:
                    best_bid_pepper = list(order_depth.buy_orders.items())[0][0]
                else:
                    best_bid_pepper = None
                if order_depth.sell_orders:
                    best_ask_pepper = list(order_depth.sell_orders.items())[0][0]
                else:
                    best_ask_pepper = None
                if best_bid_pepper is not None and best_ask_pepper is not None:
                    mid = (best_bid_pepper + best_ask_pepper) / 2


        # --- Serialize (summary fields first) ---
        ordered_data = {
            "round_count": data["round_count"],
            "last_best_bid_pepper": best_bid_pepper,
            "last_best_ask_pepper": best_ask_pepper,
            "last_best_bid_osmium": best_bid_osmium,
            "last_best_ask_osmium": best_ask_osmium,
        }
        traderData = json.dumps(ordered_data)


        # Orders to be placed on exchange matching engine
        result = {}
        POSITION_LIMIT = 25

        last_bid_pepper = data.get("last_best_bid_pepper")
        last_ask_pepper = data.get("last_best_ask_pepper")
        last_bid_osmium = data.get("last_best_bid_osmium")
        last_ask_osmium = data.get("last_best_ask_osmium")

        for product in state.order_depths:
            
            if product == "ASH_COATED_OSMIUM":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                position = state.position.get(product, 0)


                ## Standard Market Making
                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                else:
                    best_ask = None
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                else:
                    best_bid = None

                if best_bid is not None and best_bid < 10_000:
                    orders.append(Order(product, best_bid + 1, 10))
                    print(f"Processing {product} with passive strategy. Placing BUY order at {best_bid + 1}")

                if best_ask is not None and best_ask > 10_000:
                    orders.append(Order(product, best_ask - 1, -10))
                    print(f"Processing {product} with passive strategy. Placing SELL order at {best_ask - 1}")


                ## Taking Big Candles that jump over the Mid Price by 10 or more aggressively.
                if best_bid is not None and last_bid_osmium is not None and best_bid - last_bid_osmium > 10:
                    orders.append(Order(product, best_bid, -best_bid_amount))
                    print(f"SELL aggresive {max(-best_bid_amount, -position)} at {best_bid}")

                if best_ask is not None and last_ask_osmium is not None and last_ask_osmium - best_ask > 10:
                    print(f"last_ask: {last_ask_osmium}, best_ask: {best_ask}")
                    print(f"Spread: {last_ask_osmium - best_ask}")
                    orders.append(Order(product, best_ask, -best_ask_amount))
                    print(f"BUY aggresive {-best_ask_amount} at {best_ask}")

                    
                ## Big Offset for Large Order that break all normal Order Book Levels
                print(f"Processing {product} with big offset.")
                orders.append(Order(product, 9950, 10))
                orders.append(Order(product, 10050, -10))

            


            if product == "INTARIAN_PEPPER_ROOT":
                print(f"Processing {product} with passive strategy.")
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]

                orders.append(Order(product, best_bid + 1, 10))
            
            result[product] = orders
    
        conversions = 0
        return result, conversions, traderData