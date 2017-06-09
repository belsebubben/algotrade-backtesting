#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi
from pyalgotrade.technical import cross
from pyalgotrade.talibext.indicator import BBANDS, RSI


def parameters_generator():
    entrySMA = (30,)
    exitDays = range(2, 4)
    rsiPeriod = range(2, 5)
    overBoughtThreshold = (90,)
    #overSoldThreshold = range(10, 20)
    overSoldThreshold = range(10, 20)
    
    return itertools.product(entrySMA, exitDays, rsiPeriod, overBoughtThreshold, overSoldThreshold)

class TestStrat(strategy.BacktestingStrategy):
    #def __init__(self, feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
    def __init__(self, feed, instrument, entrySMA, exitDays, rsiPeriod, overBoughtThreshold, overSoldThreshold):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)
        self.exitDays = exitDays
        
        self.STRATNAME = "RSI_oversold"

        self.__instrument = instrument
        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        #self.__priceDS = feed[self.__instrument].getPriceDataSeries()
        self.__priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()

        #self.__Ds = self.getFeed().getDataSeries(self.__instrument).getCloseDataSeries()

        #self.__closeDS = feed[instrument].

        self.__entrySMA = ma.SMA(self.__priceDS, entrySMA)
        #self.__exitSMA = ma.SMA(self.__priceDS, exitSMA)

        self.__rsi = rsi.RSI(self.__priceDS, rsiPeriod)
        #self.__rsi = RSI(self.__Ds, rsiPeriod) # CARL


        #self.Cad = talibext.indicator.AD(self.__priceDS,20 ) #     Chaikin A/D Line

        #self.ADX = talibext.indicator.ADX(self.__priceDS, 20, ) # ADX

        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold
        self.__longPos = None
        self.__shortPos = None
        self.getBroker().getFillStrategy().setVolumeLimit(None) # hack / CARL

    def getEntrySMA(self):
        return self.__entrySMA

#    def getExitSMA(self):
#        return self.__exitSMA

    def getRSI(self):
        return self.__rsi

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
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        #if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
        if self.__entrySMA[-1] is None or self.__rsi[-1] is None:
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
                shares = 100
                self.__longPos = self.enterLong(self.__instrument, shares, True)
                #self.__longPos = self.enterLongStop(instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False)
                #self.__longPos = self.enterLongStopLimit(instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False)

#            elif self.enterShortSignal(bar): # Exit short
#                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
#                self.__shortPos = self.enterShort(self.__instrument, shares, True)

    def enterLongSignal(self, bar): # Conditiond for long
        return bar.getPrice() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold

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
