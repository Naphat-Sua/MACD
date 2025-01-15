# region imports
from AlgorithmImports import *
# endregion

class MACD_Template(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100000)
        self.symbol = self.add_cfd("WTICOUSD", Resolution.HOUR).symbol #WTICOUSD

        self._macd = self.macd(self.symbol, 12, 26, 9)
        self._daily_sma = self.sma(self.symbol, 200, Resolution.DAILY)

        self.window = RollingWindow[float](20)

        self.set_warm_up(5000)

        #Plot
        chart = Chart("long_strategy")
        self.add_chart(chart)
        chart.add_series(Series("price", SeriesType.LINE, "$", Color.Black))
        chart.add_series(Series("long", SeriesType.SCATTER, "$", Color.Orange, ScatterMarkerSymbol.TRIANGLE))
        chart.add_series(Series("tp", SeriesType.SCATTER, "$", Color.Green, ScatterMarkerSymbol.TRIANGLE_DOWN))
        chart.add_series(Series("sl", SeriesType.SCATTER, "$", Color.Red, ScatterMarkerSymbol.TRIANGLE_DOWN))

    def on_data(self, data: Slice):
        close = data[self.symbol].close
        self.window.add(close) # Save closing price to the window

        if self.is_warming_up and self._macd.is_ready and self.daily_sma.is_ready:
            return

        # Indicators
        fast = self._macd.fast.current.value
        slow = self._macd.slow.current.value
        macd = self._macd.current.value
        histogram = self._macd.histogram.current.value

        daily_sma = self._daily_sma[0].value

        curr_qty = self.portfolio[self.symbol].quantity

        # Strategy Logic
        adj_qty = 0
        if (histogram >= 0) and (curr_qty==0) and (close>daily_sma): #Long
            self.market_order(self.symbol, 100, tag="long entry")
            self.plot("long_strategy","long", close)
            self.entry_price = close
        elif ((histogram < 0) or (close<daily_sma)) and (curr_qty>0): #Exit
            if close>=self.entry_price: #profit
                self.plot("long_strategy","tp",close)
                tag = "tp"
            else: #loss
                self.plot("long_strategy","sl",close)
                tag = "sl"
            self.liquidate(tag=tag)

        # Plot
        self.plot("MACD", "Histogram", histogram)
        self.plot("Curr_qty", "Curr_qty", curr_qty)

        self.plot("long_strategy","price",close)
        self.plot("long_strategy","daily_sma",daily_sma)
