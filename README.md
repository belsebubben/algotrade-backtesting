# algotrade-backtesting
Test different TA strategies against a bunch of stocks and a bunch of different input settings and spit out the "best" results as csv

## Install
python 2.7+
install ta-lib (./configure ; make; make install) http://ta-lib.org/
virtualenv algotrader
. algotrader/bin/activate 
pip install TA-Lib
pip install pyalgotrade

## Usage
Change to import the correct strategy
edit ''' optimize_general.py '''
import strategy_Doji_Hammer as teststrategy
python optimize_general.py
