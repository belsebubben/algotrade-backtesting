#!/home/carl/Projects/algotrader/algotrader/bin/python2.7
''' 
Accumulation Distribution strategy. This strategy tests what the edge is when the percentual change is > x in y days time.
'''

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.talibext.indicator import AD

def parameters_generator(paramnames=False):
    if paramnames:
        return ("prcntchg","indays","exitdays") # to retreive these names, making caller agnostic !! always an array !! ORDER MATTER
    prcntchg = numpy.arange(5, 31, 5)
    exitDays = (10,31,5)
    indays = (10,31,5)
    return itertools.product(prcntchg, indays, exitDays)

class TestStrat(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, prcntchg, indays, exitDays):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)

        self.STRATNAME = "AccumulationDistribution"

        self.indays = indays
        self.exitDays = exitDays
        self.prcntchg = prcntchg

        self.__instrument = instrument

        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        self.__priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()

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
        barDs = self.getFeed().getDataSeries(self.__instrument)
        self.AD = AD(barDs, 100)

        # debug
        #if self.AD != None:
        #    print "AD %s, len %s" % (self.AD[-1], len(self.AD))

        # We want to have at least N values 
        if len(self.AD) < 50:
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
        thischange = float(self.AD[-1] - self.AD[-self.indays]) / float(self.AD[-1]) * 100
        if thischange > self.prcntchg:
            #print "AD today: %s ; AD N days ago %s" % (self.AD[-1], self.AD[-self.indays])
            #print "Change = %s%%" % thischange
            return True

    def exitLongSignal(self):
        # Ma cross
        # return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()
        #return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()

        # N periods exit
        return self.__longPos.getAge().days > self.exitDays and not self.__longPos.exitActive()


    def enterShortSignal(self, bar):
        return bar.getPrice() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

#    def exitShortSignal(self):
#        return cross.cross_below(self.__priceDS, self.__exitSMA) and not self.__shortPos.exitActive()
