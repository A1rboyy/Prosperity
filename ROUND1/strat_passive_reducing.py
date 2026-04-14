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

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = list(order_depth.buy_orders.items())[0][0]
                best_ask = list(order_depth.sell_orders.items())[0][0]
                mid = (best_bid + best_ask) / 2

        # --- Serialize (summary fields first) ---
        ordered_data = {
            "round_count": data["round_count"],
            "last_best_bid": best_bid,
            "last_best_ask": best_ask
        }
        traderData = json.dumps(ordered_data)


        # Orders to be placed on exchange matching engine
        result = {}
        POSITION_LIMIT = 25

        last_bid = data.get("last_best_bid")
        last_ask = data.get("last_best_ask")

        for product in state.order_depths:
            
            if product == "ASH_COATED_OSMIUM":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                print(f"Processing {product} with passive strategy.")
                orders.append(Order(product, 9980, 10))
                orders.append(Order(product, 10020, -10))


            # if product == "ASH_COATED_OSMIUM" and last_bid is not None and last_ask is not None:
            #     order_depth: OrderDepth = state.order_depths[product]
            #     orders: List[Order] = []
            #     if len(order_depth.sell_orders) != 0 and len(order_depth.buy_orders) != 0:
            #         best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            #         best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]

            #         # 2nd best bid/ask (if available)
            #         buy_orders  = list(order_depth.buy_orders.items())
            #         sell_orders = list(order_depth.sell_orders.items())
            #         second_best_bid = buy_orders[1][0]  if len(buy_orders)  >= 2 else None
            #         second_best_ask = sell_orders[1][0] if len(sell_orders) >= 2 else None

            #         position = state.position.get(product, 0)

            #         if best_bid - last_bid > 3 and position > 5:
            #             orders.append(Order(product, best_bid, max(-best_bid_amount, -position)))
            #             print(f"[ASH_COATED_OSMIUM] SELL Reducing position by {max(-best_bid_amount, -position)} at {best_bid}")

            #         orders.append(Order(product, best_bid + 1, 10))
            #         print(f"[ASH_COATED_OSMIUM] Placing BUY order at {best_bid + 1}")

            #         if last_ask - best_ask > 3 and position < -5:
            #             orders.append(Order(product, best_ask, min(-best_ask_amount, -position)))
            #             print(f"[ASH_COATED_OSMIUM] BUY Reducing position by {min(-best_ask_amount, -position)} at {best_ask}")
            #         orders.append(Order(product, best_ask - 1, -10))
            #         print(f"[ASH_COATED_OSMIUM] Placing SELL order at {best_ask - 1}")


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