#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

def parameters_generator():
    aboveSMA = range(30, 201, 10)
    exitDays = (1,)
    
    return itertools.product(aboveSMA, exitDays)

class TestStrat(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, aboveSMA, exitDays):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)
        self.exitDays = exitDays
        
        self.STRATNAME = "Above_Ma"

        self.__instrument = instrument
        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        self.__priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()

        self.aboveSMA = ma.EMA(self.__priceDS, aboveSMA)

        self.aboveSMAMid = ma.EMA(self.__priceDS, 50)

        self.aboveSMALong = ma.EMA(self.__priceDS, 125)

        self.__longPos = None
        self.__shortPos = None
        self.getBroker().getFillStrategy().setVolumeLimit(None) # hack / CARL

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitOk(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        #if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
        if self.aboveSMA[-1] is None:
            return

        bar = bars[self.__instrument]
        if self.__longPos is not None: # We have a long position
            if self.exitLongSignal():
                self.__longPos.exitMarket()
#        elif self.__shortPos is not None: # We have a short position
#            if self.exitShortSignal():
#                self.__shortPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                #shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                shares = 10
                self.__longPos = self.enterLong(self.__instrument, shares, True)
                #self.__longPos = self.enterLongStop(instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False)
                #self.__longPos = self.enterLongStopLimit(instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False)

#            elif self.enterShortSignal(bar): # Exit short
#                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
#                self.__shortPos = self.enterShort(self.__instrument, shares, True)

    def enterLongSignal(self, bar): # Conditiond for long
        return bar.getPrice() > self.aboveSMA[-1]

    def exitLongSignal(self):
        # Ma cross
        # return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()
        #return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()

        # 3 periods exit
        return self.__longPos.getAge().days > self.exitDays and not self.__longPos.exitActive()


    def enterShortSignal(self, bar):
        return bar.getPrice() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

#    def exitShortSignal(self):
#        return cross.cross_below(self.__priceDS, self.__exitSMA) and not self.__shortPos.exitActive()
