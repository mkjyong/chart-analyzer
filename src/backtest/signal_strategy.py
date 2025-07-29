from __future__ import annotations

import backtrader as bt


class SignalTradeStrategy(bt.Strategy):
    params = dict(
        sl_pct=0.005,  # 0.5%
        rr=1.5,  # TP = SL * RR
    )

    def __init__(self):
        # 'signal' 라인 추가된 데이터 feed를 가정
        self.signal = self.datas[0].signal
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return

        sig = self.signal[0]
        if not self.position:
            if sig == 1:
                self._open_long()
            elif sig == -1:
                self._open_short()
        # 포지션 보유 중일 때는 SL/TP OCO 주문이 관리함

    def _open_long(self):
        self.entry_price = self.data.close[0]
        sl_price = self.entry_price * (1 - self.p.sl_pct)
        tp_price = self.entry_price + (self.entry_price - sl_price) * self.p.rr
        self.order = self.buy()
        self.sell(exectype=bt.Order.Stop, price=sl_price, parent=self.order)
        self.sell(exectype=bt.Order.Limit, price=tp_price, parent=self.order)

    def _open_short(self):
        self.entry_price = self.data.close[0]
        sl_price = self.entry_price * (1 + self.p.sl_pct)
        tp_price = self.entry_price - (sl_price - self.entry_price) * self.p.rr
        self.order = self.sell()
        self.buy(exectype=bt.Order.Stop, price=sl_price, parent=self.order)
        self.buy(exectype=bt.Order.Limit, price=tp_price, parent=self.order)

    def notify_order(self, order):
        # on complete/cancel reset
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None 