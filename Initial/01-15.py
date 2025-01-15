# region imports
from AlgorithmImports import *
# endregion

class MACD_Template(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2024, 12, 31)
        self.SetCash(100000)
        
        self.symbol = self.AddCfd("WTICOUSD", Resolution.Hour).Symbol

        self._macd = self.MACD(self.symbol, 12, 26, 9)
        self._daily_sma = self.SMA(self.symbol, 30, Resolution.Daily)
        self._daily_sma_window = RollingWindow[IndicatorDataPoint](5)
        self._daily_sma.Updated += self.OnDailySMAUpdated
        
        self._rsi = self.RSI(self.symbol, 14)
        
        self._atr = self.ATR(self.symbol, 14)
        
        self.window = RollingWindow[float](20)
        self.SetWarmUp(5000)
        
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.last_trade_time = datetime(1900, 1, 1)
        
        self.InitializePlotting()
        
    def InitializePlotting(self):
        chart = Chart("long_strategy")
        self.AddChart(chart)
        chart.AddSeries(Series("price", SeriesType.Line, "$", Color.Black))
        chart.AddSeries(Series("long", SeriesType.Scatter, "$", Color.Orange, ScatterMarkerSymbol.Triangle))
        chart.AddSeries(Series("tp", SeriesType.Scatter, "$", Color.Green, ScatterMarkerSymbol.TriangleDown))
        chart.AddSeries(Series("sl", SeriesType.Scatter, "$", Color.Red, ScatterMarkerSymbol.TriangleDown))
    
    def OnDailySMAUpdated(self, sender, updated):
        if updated is not None:
            self._daily_sma_window.Add(updated)
    
    def OnData(self, data: Slice):
        if not data.ContainsKey(self.symbol):
            return
            
        close = data[self.symbol].Close
        self.window.Add(close)
        
        if (self.IsWarmingUp or 
            not self._macd.IsReady or 
            not self._daily_sma.IsReady or 
            not self._daily_sma_window.IsReady or
            not self._rsi.IsReady or
            not self._atr.IsReady):
            return
            
        histogram = self._macd.Histogram.Current.Value
        daily_sma = self._daily_sma_window[0].Value
        rsi = self._rsi.Current.Value
        atr = self._atr.Current.Value
        curr_qty = self.Portfolio[self.symbol].Quantity
        
        hours_since_last_trade = (self.Time - self.last_trade_time).total_seconds() / 3600
        
        if curr_qty == 0:
            if (histogram >= 0 and                    
                close > daily_sma and               
                rsi >= 40 and rsi <= 70 and       
                hours_since_last_trade > 12):       
                
                self.entry_price = close
                self.stop_loss = self.entry_price - (2 * atr)
                self.take_profit = self.entry_price + (3 * atr)
                
                self.MarketOrder(self.symbol, 100, tag="long entry")
                self.Plot("long_strategy", "long", close)
                self.last_trade_time = self.Time  
        
        elif curr_qty > 0:
            if (close <= self.stop_loss or                   
                close >= self.take_profit or                   
                (histogram < 0 and close < daily_sma) or      
                rsi >= 80):                                   
                
                if close >= self.entry_price:
                    self.Plot("long_strategy", "tp", close)
                    tag = "tp"
                else:
                    self.Plot("long_strategy", "sl", close)
                    tag = "sl"
                    
                self.Liquidate(tag=tag)
                self.last_trade_time = self.Time
        
        self.Plot("MACD", "Histogram", histogram)
        self.Plot("RSI", "RSI", rsi)
        self.Plot("Curr_qty", "Curr_qty", curr_qty)
        self.Plot("long_strategy", "price", close)
        self.Plot("long_strategy", "daily_sma", daily_sma)
