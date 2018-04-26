#####################################################################
# Trend recognition algorithm
# Evan Kirkiles, 2018
#####################################################################
# This is a trend detecting algorithm for uncorrelated assets
# Universe: 
import quantopian.algorithm as algo
import pandas as pd
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS


def initialize(context):
    set_symbol_lookup_date('2015-01-01')      # Symbols retrieved from the date January 1, 2015
    
    # Assets to be traded by the algorithm, by asset class
    # TODO: Find low-drawdown assets to trade (these will perform the best, I think)
    context.equities = symbols(
        # Equities
        'AAPL',          # Google
        'TSLA',          # Tesla
        'QQQ'
    )
    context.fixedincomes = symbols(
        # Fixed incomes
        'LQD',           # Corporate bond
        'HYG'            # High yield
    )
    context.alternatives = symbols(
        # Alternatives
        'USO',           # Oil
        'GLD',           # Gold
        'UNG',           # Natural gas
        'DBA'            # Agriculture
    )
    context.secs = context.equities + context.fixedincomes + context.alternatives
    context.maxlever = 0.9                  # Always hold 10% cash
    context.lookback = 50                   # Look back 20 days for necessary maxs/mins
    context.ddlookback = 252                # Look back a year when calculating drawdown volatility
    context.critpointsfilled = False        # Fill critical points to get dict started
    
    # Dictionary holding the past 3 critical points and prices for each security
    context.past3critpoints = dict.fromkeys(context.secs, None)
    # Stopprice will stop losses, is set in ______ function
    context.stopprice = dict.fromkeys(context.secs, None)
    # Dictionary holding the trends of each security and its strength
    context.trendstrength = dict.fromkeys(context.secs, None)
    
    # Mock schedule because cannot call from init function, only happens once
    schedule_function(initcritpoints, date_rules.every_day(), time_rules.market_open(minutes = 1))
    
    # Schedule all functions in order: end pertinent trades, find trends, perform trades
    #schedule_function(trail_stop, date_rules.every_day(), time_rules.market_open(minutes = 10))
    schedule_function(trendanalysis, date_rules.every_day(), time_rules.market_open(minutes = 28))
    #schedule_function(trade, date_rules.every_day(), time_rules.market_open(minutes = 30))

# Calculate trend direction 
def trendanalysis(context, data):
    # Get price from past 1 day to get opening price of today
    prices = data.history(context.secs, 'open', context.ddlookback, '1d')
    
    # Check most recent price point to determine trend
    for s in context.secs:
        
        ## NEED TO CYCLE THROUGH THE CRITICAL POINTS TO KEEP UPDATING THE TRENDS
        
        # Calculate average drawdown volatility for past [context.lookback] days
        daily_drawdown = prices[s]/prices[s].rolling(context.lookback).max() - 1.0
        std_daily_drawdown = daily_drawdown.std()
        
        # If prevous critical points go min-max-min, must be increasing
        if (context.past3critpoints[s][0].values()[0] < context.past3critpoints[s][1].values()[0]) and (
            context.past3critpoints[s][2].values()[0] < context.past3critpoints[s][1].values()[0]):
                
                # When new price exceeds previous maximum, record trend strength
                if (prices[s][-1] > context.past3critpoints[s][1].values()[0]):
                    
                    # Trend strength is ARoC from min to new point divided by drawdown
                    context.trendstrength[s] = (prices[s][-1] - context.past3critpoints[s][1].values()[0]) / (
                        std_daily_drawdown * (prices.index[-1] - context.past3critpoints[s][1].keys()[0]).days)
        
        # If prevous critical points go max-min-max, must be decreasing
        elif (context.past3critpoints[s][0].values()[0] > context.past3critpoints[s][1].values()[0]) and (
            context.past3critpoints[s][2].values()[0] > context.past3critpoints[s][1].values()[0]):
                
                # When new price drops below previous minimum, record trend strength
                if (prices[s][-1] < context.past3critpoints[s][1].values()[0]):
                    
                    # Trend strength is ARoC from min to new point divided by drawdown
                    context.trendstrength[s] = (prices[s][-1] - context.past3critpoints[s][1].values()[0])/ (
                        std_daily_drawdown * (prices.index[-1] - context.past3critpoints[s][1].keys()[0]).days)
        
        # If there is no identifiable trend, trend will be None
        else:
            context.trendstrength[s] = None
            
# Initialize moving critical point array
def initcritpoints(context, data):
    if context.critpointsfilled:
        return
    
    # Get prices from past [context.lookback] days
    prices = data.history(context.secs, 'open', context.lookback, '1d')
    
    # Find highs and lows for each stock
    for s in context.secs:
        
        # Placeholder array for determining critical points
        allcritpoints = []

        for date in prices[1:-1].index:
            # Checking for maximums and minimums (critical points)
            if ((prices[s][date] < prices[s].iloc[prices[s].index.get_loc(date) - 1]) and (
                prices[s].iloc[prices[s].index.get_loc(date) - 2] < prices[s].iloc[prices[s].index.get_loc(date) - 1])) or (
                (prices[s][date] > prices[s].iloc[prices[s].index.get_loc(date) - 1]) and (
                prices[s].iloc[prices[s].index.get_loc(date) - 2] > prices[s].iloc[prices[s].index.get_loc(date) - 1])):
                    
                    # Add any found critical points
                    allcritpoints.append(prices.index[prices[s].index.get_loc(date)-1])
   
        # Add most recent 3 critical points to [context.past3critpoints]
        context.past3critpoints.update({
               s: [{allcritpoints[-1]: prices[s][allcritpoints[-1]]},
                   {allcritpoints[-2]: prices[s][allcritpoints[-2]]},
                   {allcritpoints[-3]: prices[s][allcritpoints[-3]]}]
               })                
            
    context.critpointsfilled = True
