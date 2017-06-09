#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi
from pyalgotrade.technical import cross
from pyalgotrade.technical import atr

def parameters_generator(paramnames=False):
    if paramnames:
        return ("exitDays","multiplier") # to retreive these names, making caller agnostic !! always an array !!
    multiplier = numpy.arange(1.2, 2, 0.1)
    exitDays = range(1, 20, 4)
    return itertools.product(exitDays, multiplier)

class TestStrat(strategy.BacktestingStrategy):
    #def __init__(self, feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
    def __init__(self, feed, instrument, exitDays, multiplier):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)
        self.exitDays = exitDays
        self.multiplier = multiplier
        
        self.STRATNAME = "Spike"

        self.__instrument = instrument
        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        self.barDS = self.getFeed().getDataSeries(self.__instrument)
        self.priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()
        self.volumeDS = self.getFeed().getDataSeries(self.__instrument).getVolumeDataSeries()

        self.atr = atr.ATR(self.barDS, 20)
        
        self.volumeSma = ma.SMA(self.volumeDS, 20)

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
        bar = bars[self.__instrument]

        try:
            self.ydaybar = self.barDS[-2]
        except:
            self.ydaybar  =  self.barDS[-1]

        self.tr = max(bar.getPrice() - bar.getLow(), bar.getPrice() - self.ydaybar.getPrice())

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
        #return bar.getPrice() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold
        priceToday, lowToday = bar.getPrice(), bar.getLow()
#        print
#        print "Tday close, low", priceToday, lowToday
#        print "Yday close", self.ydaybar.getPrice()
#        print "atr1", self.tr
#        print
        if not self.tr or not self.atr[-1]:
            return False
        return self.tr > self.atr[-1] * self.multiplier and self.tr <  (self.atr[-1] * ( self.multiplier + 0.1) )

    def exitLongSignal(self):
        # Ma cross
        # return cross.cross_above(self.priceDS, self.__exitSMA) and not self.__longPos.exitActive()
        #return cross.cross_above(self.priceDS, self.__exitSMA) and not self.__longPos.exitActive()

        # N periods exit
        return self.__longPos.getAge().days > self.exitDays and not self.__longPos.exitActive()


    def enterShortSignal(self, bar):
        pass
        #return bar.getPrice() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

#    def exitShortSignal(self):
#        return cross.cross_below(self.priceDS, self.__exitSMA) and not self.__shortPos.exitActive()
