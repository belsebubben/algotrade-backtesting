#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import cross, macd

def parameters_generator(paramnames=False):
    if paramnames:
        return ("exitdays","belowzero") # to retreive these names, making caller agnostic !! always an array !! ORDER MATTER
    exitDays = (2,5,10,15,20,25,30)
    belowzero = (True, False)
    return itertools.product(exitDays,belowzero)

class TestStrat(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, exitDays,belowzero):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)

        self.TestShort = True # Test only short or long, not both.

        self.STRATNAME = "Macd_Crossing"
        self.STRATDESC = '''Tests what the edge is when macd line crosses below macd-ema both when the macd is below and above the zero line'''

        self.exitDays = exitDays
        self.belowzero = belowzero

        self.__instrument = instrument

        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        #self.BarDs = self.getFeed().getDataSeries(self.__instrument)
        self.__priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()

        self.macd  = macd.MACD(self.__priceDS, 12,26,9)

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
        # We want to have at least N values 
        bar = bars[self.__instrument]


        if self.__longPos is not None: # We have a long position
            if self.exitLongSignal():
                self.__longPos.exitMarket()
        elif self.__shortPos is not None: # We have a short position
            if self.exitShortSignal():
                self.__shortPos.exitMarket()
        else:
            if not self.TestShort:
                if self.enterLongSignal(bar):
                    #shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                    shares = 10
                    self.__longPos = self.enterLong(self.__instrument, shares, True)
                    #self.__longPos = self.enterLongStop(instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False)
                    #self.__longPos = self.enterLongStopLimit(instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False)
            if self.TestShort:
                if self.enterShortSignal(bar): # Exit short
                    shares = 10
                    self.__shortPos = self.enterShort(self.__instrument, shares, True)

#            elif self.enterShortSignal(bar): # Exit short
#                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
#                self.__shortPos = self.enterShort(self.__instrument, shares, True)

    def enterLongSignal(self, bar): # Conditiond for long
        thismacd = self.macd[-1]
        macdsig = self.macd.getSignal()[-1]
        if self.belowzero:
            if cross.cross_below(self.macd, self.macd.getSignal()) and macdsig < 0:
                #print "Entering long trade below zero macd", thismacd, macdsig
                return True
        else:
            if cross.cross_below(self.macd, self.macd.getSignal()) and macdsig > 0:
                #print "Entering long trade above zero macd", thismacd, macdsig
                return True

    def exitLongSignal(self):
        # Ma cross
        # return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()
        #return cross.cross_above(self.__priceDS, self.__exitSMA) and not self.__longPos.exitActive()

        # N periods exit
        return self.__longPos.getAge().days > self.exitDays and not self.__longPos.exitActive()


    def enterShortSignal(self, bar):
        thismacd = self.macd[-1]
        macdsig = self.macd.getSignal()[-1]
        if self.belowzero:
            if cross.cross_above(self.macd, self.macd.getSignal()) and macdsig < 0:
                #print "Entering short trade below zero macd", thismacd, macdsig
                return True
        else:
            if cross.cross_above(self.macd, self.macd.getSignal()) and macdsig > 0:
                #print "Entering short trade above zero macd", thismacd, macdsig
                return True

    def exitShortSignal(self):
        return self.__shortPos.getAge().days > self.exitDays and not self.__shortPos.exitActive()
