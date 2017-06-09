#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

def parameters_generator(paramnames=False):
    if paramnames:
        return ("EMACombo","multiplier", "exitDays") # to retreive these names, making caller agnostic !! always an array !! ORDER MATTER
    EMACombo = range(75,201,15)
    multiplier = numpy.arange(0.5, 1, 0.1)
    exitDays = (40,60,70,)
    return itertools.product(EMACombo, multiplier, exitDays)

class TestStrat(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, EMACombo, multiplier, exitDays):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)

        self.TestShort = False # Test only short or long, not both.
        self.STRATNAME = "Ema Order"
        self.STRATDESC = '''Tests the filter edge of ordered emas'''

        self.instrument = instrument
        self.priceDS = self.getFeed().getDataSeries(self.instrument).getPriceDataSeries()

        self.exitDays = exitDays
        self.ShorterEmaSetting = int(EMACombo * multiplier)
        self.LongerEmaSetting = EMACombo

        self.ema10 =  ma.EMA(self.priceDS,10)
        self.ema20 =  ma.EMA(self.priceDS,20)

        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        self.LongerEma = ma.EMA(self.priceDS, self.LongerEmaSetting)
        self.ShorterEma = ma.EMA(self.priceDS, self.ShorterEmaSetting)

        self.longPos = None
        self.shortPos = None
        self.getBroker().getFillStrategy().setVolumeLimit(None) # hack / CARL

    def onEnterCanceled(self, position):
        if self.longPos == position:
            self.longPos = None
        elif self.shortPos == position:
            self.shortPos = None
        else:
            assert(False)

    def onExitOk(self, position):
        if self.longPos == position:
            self.longPos = None
        elif self.shortPos == position:
            self.shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        #if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
        #if self.longEMA[-1] is None:
        #    return

        bar = bars[self.instrument]
        if self.longPos is not None: # We have a long position
            if self.exitLongSignal():
                self.longPos.exitMarket()
#        elif self.shortPos is not None: # We have a short position
#            if self.exitShortSignal():
#                self.shortPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                #shares = int(self.getBroker().getCash() * 0.9 / bars[self.instrument].getPrice())
                shares = 10
                self.longPos = self.enterLong(self.instrument, shares, True)
                #self.longPos = self.enterLongStop(instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False)
                #self.longPos = self.enterLongStopLimit(instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False)

#            elif self.enterShortSignal(bar): # Exit short
#                shares = int(self.getBroker().getCash() * 0.9 / bars[self.instrument].getPrice())
#                self.shortPos = self.enterShort(self.instrument, shares, True)

    def enterLongSignal(self, bar): # Conditiond for long
        return self.ShorterEma > self.LongerEma and cross.cross_below(self.ema10, self.ema20)
        #if self.ShorterEma[-1] > self.LongerEma[-1] and cross.cross_below(self.ema10, self.ema20):
        #    print "Short ema:%s above Long ema:%s" % (self.ShorterEmaSetting, self.LongerEmaSetting )
        #    print "Short ema:%s above Long ema:%s and ema10:%s cross ema20:%s" % ( self.ShorterEma[-1], self.LongerEma[-1], self.ema10[-1],self.ema20[-1])

    def exitLongSignal(self):
        # Ma cross
        # return cross.cross_above(self.priceDS, self.__exitSMA) and not self.longPos.exitActive()
        #return cross.cross_above(self.priceDS, self.__exitSMA) and not self.longPos.exitActive()

        # N periods exit
        return self.longPos.getAge().days > self.exitDays and not self.longPos.exitActive()


    def enterShortSignal(self, bar):
        return bar.getPrice() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

#    def exitShortSignal(self):
#        return cross.cross_below(self.priceDS, self.__exitSMA) and not self.shortPos.exitActive()
