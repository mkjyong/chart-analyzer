from __future__ import annotations

import backtrader as bt


class MultiIndicatorStrategy(bt.Strategy):
    params = dict(
        rsi_period=3,
        rsi_overbought=80,
        rsi_oversold=20,
        st_atr_period=10,
        st_multiplier=3.0,
        sl_pct=0.005,  # 0.5%
        rr=1.5,  # TP = SL * RR
    )

    def __init__(self):
        # Indicators
        self.rsi = bt.ind.RSI(self.data.close, period=self.p.rsi_period)
        self.supertrend = bt.ind.SuperTrend(
            self.data.high, self.data.low, self.data.close, period=self.p.st_atr_period, multiplier=self.p.st_multiplier
        )
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return  # waiting for order fill

        # Entry Conditions
        long_signal = (
            self.rsi < self.p.rsi_oversold and self.supertrend[0] < self.data.close[0]
        )
        short_signal = (
            self.rsi > self.p.rsi_overbought and self.supertrend[0] > self.data.close[0]
        )
        if not self.position:
            if long_signal:
                self.entry_price = self.data.close[0]
                sl_price = self.entry_price * (1 - self.p.sl_pct)
                tp_price = self.entry_price + (self.entry_price - sl_price) * self.p.rr
                self.order = self.buy()
                self.sl_order = self.sell(exectype=bt.Order.Stop, price=sl_price, parent=self.order)
                self.tp_order = self.sell(exectype=bt.Order.Limit, price=tp_price, parent=self.order)
            elif short_signal:
                self.entry_price = self.data.close[0]
                sl_price = self.entry_price * (1 + self.p.sl_pct)
                tp_price = self.entry_price - (sl_price - self.entry_price) * self.p.rr
                self.order = self.sell()
                self.sl_order = self.buy(exectype=bt.Order.Stop, price=sl_price, parent=self.order)
                self.tp_order = self.buy(exectype=bt.Order.Limit, price=tp_price, parent=self.order)
        else:
            # No action; exits handled by SL/TP orders automatically
            pass

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None 