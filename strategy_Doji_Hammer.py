#!/home/carl/Projects/algotrader/algotrader/bin/python2.7
'''
The number 2 version, not using talib
'''

import talib
import numpy
import itertools

from pyalgotrade import strategy
from pyalgotrade.technical import cross, macd


def parameters_generator(paramnames=False):
    if paramnames:
        return ("exitdays","daysLow") # to retreive these names, making caller agnostic !! always an array !! ORDER MATTER
    exitDays = (2,5,7,10)
    #belowzero = (True, False)
    daysLow = range(3,8)
    return itertools.product(exitDays,daysLow)

class TestStrat(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, exitDays,daysLow):
        super(TestStrat, self).__init__(feed,cash_or_brk=100000)

        self.TestShort = False # Test only short or long, not both.

        self.STRATNAME = "strategy_Doji_Hammer"
        self.STRATDESC = '''Tests what the edge the formation key reversal has, with different combos of days low'''

        self.exitDays = exitDays
        self.daysLow = daysLow

        self.__instrument = instrument

        # We'll use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)

        #self.BarDs = self.getFeed().getDataSeries(self.__instrument)
        self.__priceDS = self.getFeed().getDataSeries(self.__instrument).getPriceDataSeries()
        self.barDS = self.getFeed().getDataSeries(self.__instrument)

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
        barDs = self.getFeed().getDataSeries(self.__instrument)

        bar = bars[self.__instrument]
        bclose = bar.getClose()
        bopen = bar.getOpen()
        bhigh = bar.getHigh()
        blow = bar.getLow()

        # Doji formula
        # abs(bar.getOpen() - bar.getClose()) < ( (bar.getHigh() - bar.getLow()) * 0.1)

        # Hammer Formula
        # high - low = 3 times distance of open - close
        self.hammer = ( (bhigh - blow) > ( 3 * (bopen - bclose)) ) and ( bclose - blow / (.001 + bhigh - blow) > 0.75 ) and ( ( bopen - blow ) / (.001 + bhigh - blow ) > 0.75 )


        self.lowestBar = False # We test if this is the lowest bar in N bars
        if len(barDs) > self.daysLow + 1:
            lastbars = [b.getLow() for b in barDs[-self.daysLow-1:-1]]
            if barDs[-1].getLow() < min(lastbars):
                #print "Bar lowest %s from %s on:%s" % ( barDs[-1].getClose(), str(lastbars),self.daysLow ) # Debug
                self.lowestBar = True

        #self.lowestSince = bar.getLow() < min( [  ]  )

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
        #return self.lowestBar and bar.getClose() > self.barDS[-2].getHigh()
        return self.lowestBar and self.hammer

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
