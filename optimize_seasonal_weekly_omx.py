#!/home/carl/Projects/algotrader/algotrader/bin/python2.7

from pyalgotrade.optimizer import local
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.tools.yahoofinance import build_feed
from pyalgotrade.feed import csvfeed
from pyalgotrade import bar
from pyalgotrade.barfeed.csvfeed import GenericBarFeed

from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
#from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
import csv
import sys
from time import sleep, localtime

#import strategy_seasonal_weekly as teststrategy 
import strategy_Spike as teststrategy 
'''  Strategy to test should have a class named --  TestStrat -- with the constant property STRATNAME 
and a function called -- parameters_generator -- '''

YEARSOFDATA = 10
DATAPATH = "stockdata"

def instrumentListGetter():
    ifile = open("instrument_list")
    lines = [line.strip() for line in ifile.readlines()]
    ifile.close()
    #return ("abb.st",) # for a single instrument
    #return ("sp500 quandl",) # for a single instrument
    #return ("omxs30 quandl",) # for a single instrument
    return lines

iterations = len([ it for it in teststrategy.parameters_generator()]) * len(instrumentListGetter())
# The if __name__ == '__main__' part is necessary if running on Windows.
#@profile
def main():
    filedir = "testresults"
    iteration = 0
    resultsdict = {}
    
    for instrument in instrumentListGetter():
        if len(instrument.split()) > 1:
            instrument, instrumentSource = instrument.split()
            print "instrument: %s, source: %s" % ( instrument, instrumentSource)
        else:
            instrumentSource = ""

        #feed = yahoofeed.Feed()
        #feed.addBarsFromCSV("hm",  DATAPATH + "/hm_table.csv")

        # Load the feed from the CSV files.

        #for params in parameters_generator():
        faileddataforinstrument = False
        for params in teststrategy.parameters_generator():

            # Do not move to outer loop or severe performance problems arise # take the data we have and use
            yiter = 0
            if "quandl" in instrumentSource: # https://www.quandl.com/data/
                '''/home/carl/Projects/algotrader/algotrader/lib64/python2.7/site-packages/pyalgotrade/barfeed/csvfeed.py:171 needs try hack '''
                try:
                    feed = GenericBarFeed(frequency=bar.Frequency.DAY)
                    feed.setDateTimeFormat("%Y-%m-%d")
                    feed.setColumnName("datetime", "Date")
                    feed.setColumnName("adj_close", "Adjusted Close")
                    #feed.addBarsFromCSV(instrument, DATAPATH)
                    feed.addBarsFromCSV(instrument, DATAPATH + "/" + instrument + ".csv")
                except:
                    print sys.exc_info()
                    faileddataforinstrument = True
            
            else:
                for year in range(YEARSOFDATA,0,-1):
                    startyear = localtime().tm_year - (YEARSOFDATA - yiter)
                    try:
                        feed = build_feed([instrument], startyear, 2016, DATAPATH, frequency=86400, timezone=None, skipErrors=False)
                    except:
                        print "\n\nFailed downloading %s for year %d yiter %d \n\n" % (instrument, startyear, yiter)
                        yiter +=1
                        if year == (YEARSOFDATA - 1):
                            faileddataforinstrument = True

            if faileddataforinstrument:
                break

            strat = teststrategy.TestStrat(feed, instrument, *params)
            iteration += 1

            paramnames = teststrategy.parameters_generator(paramnames=True)
            paramsarray =  zip(paramnames, [str(p) for p in params] )
            paramsstring =  str([":".join(t) for t in  zip(paramnames, [str(p) for p in params] )])

            print "\n\nIteration %d / %d; Instrument %s ; Params %s" % (iteration, iterations,  instrument, paramsstring )

            #retAnalyzer = returns.Returns()
            #strat.attachAnalyzer(retAnalyzer)
            sharpeRatioAnalyzer = sharpe.SharpeRatio()
            strat.attachAnalyzer(sharpeRatioAnalyzer)
            #drawDownAnalyzer = drawdown.DrawDown()
            #strat.attachAnalyzer(drawDownAnalyzer)
            tradesAnalyzer = trades.Trades()
            strat.attachAnalyzer(tradesAnalyzer)

            # with instrument
            #csvdict["Params"] = [":".join(t) for t in  zip(("instrument", "entrySMA", "exitDays", "rsiPeriod", "overBoughtThreshold", "overSoldThreshold"), [str(p) for p in params] )]
            # without instrument
            
            print paramsstring
            strat.run()
            tradetotal = 0

            tradetotal = sum([t*100.00 for t in tradesAnalyzer.getAllReturns()])
            nr_of_trades = tradesAnalyzer.getCount()
            try:
                profitable_tradeprcnt = "%.2f" % ((float(tradesAnalyzer.getProfitableCount()) / float(tradesAnalyzer.getCount())) * 100)
                trade_avg_result_prcnt = "%.2f" % ( tradetotal / float(tradesAnalyzer.getCount()) )
            except ZeroDivisionError:
                profitable_tradeprcnt = "0.0"
                trade_avg_result_prcnt = "0.0"

            sharpe_ratio = "%.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05))

            #print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)

            print "Trade stats"
            print "Nr of trades:\t\t\t%d" % (nr_of_trades)
            print "Trade avg:\t\t\t%s%%" % ( trade_avg_result_prcnt ) 
            print "Profitable trades:\t\t%s%%" % (profitable_tradeprcnt)
            print "Sharpe ratio:\t\t\t", sharpe_ratio 
            print
            returns = tradesAnalyzer.getAllReturns()

            if tradesAnalyzer.getProfitableCount() > 0:
                trade_max = "%.2f" % (returns.max() * 100)
                trade_min = "%.2f" % (returns.min() * 100)
                trade_stddev = "%.2f" % (returns.std() * 100)
            else:
                trade_max = "%.2f" % 0
                trade_min = "%.2f" % 0
                trade_stddev = "%.2f" % 0


            print "Returns std. dev.: %s %%\t\t\t" % trade_stddev
            print "Max. return: %s %%\t\t\t" % trade_max
            print "Min. return: %s %%\t\t\t" % trade_min
            #print "Trade total:	    %.2f" % ( tradetotal )
            #print "Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100)

            #if tradesAnalyzer.getProfitableCount() > 0:
                #profits = tradesAnalyzer.getProfits()
                #losses = tradesAnalyzer.getLosses()
                #print "Avg. profit: $%2.f" % (profits.mean())
                #print "Avg. loss: $%2.f" % (losses.mean())

                #returns = tradesAnalyzer.getPositiveReturns()
                #returns = tradesAnalyzer.getAllReturns()
                #print "Avg. return: %2.f %%" % (returns.mean() * 100) # too much rounding
                #print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
                #print "Max. return: %2.f %%" % (returns.max() * 100)
                #print "Min. return: %2.f %%" % (returns.min() * 100)

                #print "Trades std. dev.: $%2.f" % (profits.std())
                #print "Max. profit: $%2.f" % (profits.max())
                #print "Min. profit: $%2.f" % (profits.min())

            if paramsstring in resultsdict.keys():
                try:
                    resultsdict[paramsstring]['nr_of_trades'] = int(resultsdict[paramsstring]['nr_of_trades']) + int(nr_of_trades)
                    resultsdict[paramsstring]['profitable_tradeprcnt'] = "%.2f" % ( ( float(resultsdict[paramsstring]['profitable_tradeprcnt']) + float(profitable_tradeprcnt)) / 2.00 )
                    resultsdict[paramsstring]['trade_avg_result_prcnt'] = "%.2f" % ( ( float(resultsdict[paramsstring]['trade_avg_result_prcnt']) + float(trade_avg_result_prcnt) ) / 2.00 )
                    resultsdict[paramsstring]['sharpe_ratio'] = "%.2f" % ( ( float(resultsdict[paramsstring]['sharpe_ratio']) + float(sharpe_ratio) ) / 2.00 )
                    resultsdict[paramsstring]['trade_max'] = "%.2f" % ( float(resultsdict[paramsstring]['trade_max']) + float(trade_max) / 2.00)
                    resultsdict[paramsstring]['trade_min'] = "%.2f" % ( float(resultsdict[paramsstring]['trade_min']) + float(trade_min) / 2.00)
                    resultsdict[paramsstring]['trade_stddev'] = "%.2f" % ( float(resultsdict[paramsstring]['trade_stddev']) + float(trade_stddev) / 2.00)
                except ZeroDivisionError:
                    print "\nError (ZeroDivisionError) trying averaging with: %s\n" % paramsstring
            else: # First time with params
                resultsdict[paramsstring] = dict(paramsarray)
                resultsdict[paramsstring]['params'] = paramsstring
                resultsdict[paramsstring]['nr_of_trades'] = nr_of_trades
                resultsdict[paramsstring]['profitable_tradeprcnt'] = profitable_tradeprcnt
                resultsdict[paramsstring]['trade_avg_result_prcnt'] = trade_avg_result_prcnt
                resultsdict[paramsstring]['sharpe_ratio'] = sharpe_ratio
                resultsdict[paramsstring]['trade_max'] = trade_max
                resultsdict[paramsstring]['trade_min'] = trade_min
                resultsdict[paramsstring]['trade_stddev'] = trade_stddev

            feed.reset() # feed must be reset

            del sharpeRatioAnalyzer
            del tradesAnalyzer
        
    with open(filedir + "/" + strat.STRATNAME + '.csv', 'wb') as csvfile:
        fieldnames = ['params']
        fieldnames.extend(paramnames)
        fieldnames.extend(('nr_of_trades', 'profitable_tradeprcnt', 'trade_avg_result_prcnt', 'sharpe_ratio', 'trade_max', 'trade_min', 'trade_stddev'))

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #csvheader = {'params':'Params: ' + strat.STRATNAME, paramnames, 'nr_of_trades':'Nr of trades',\
        #        'profitable_tradeprcnt':'Profitable trades%', 'trade_avg_result_prcnt':'Trade avg %', 'sharpe_ratio': 'Sharpe Ratio'}
        csvheader = {'params':'Params: ' + strat.STRATNAME}
        for n in  paramnames: csvheader[n] = n 
        csvheader['nr_of_trades'] = 'Nr of trades'
        csvheader['profitable_tradeprcnt'] = 'Profitable trades%'
        csvheader['trade_avg_result_prcnt']= 'Trade avg %'
        csvheader['sharpe_ratio'] = 'Sharpe Ratio'
        csvheader['trade_max'] = 'Trade Max'
        csvheader['trade_min'] = 'Trade Min'
        csvheader['trade_stddev'] = 'Trade Stddev'
        writer.writerow(csvheader)
        for result in resultsdict.keys():
            writer.writerow(resultsdict[result])

    #local.run(test_strategy1_carl.RSI2, feed, parameters_generator() )
    #local.run(rsi2.RSI2, feed, parameters_generator() )

if __name__ == '__main__':
    main()
