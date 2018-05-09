#####################################################################
# Trend recognition algorithm
# Evan Kirkiles, 2018
#####################################################################
# This is a trend detecting algorithm for uncorrelated assets that is based
# around the idea that up trends are signified by higher highs & lows and 
# down trends are signified by lower highs & lows. Very bad predictive power so
# has awful returns but was a good learning experience as my first original algo.
import quantopian.algorithm as algo
import pandas as pd
import math
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS

def initialize(context):
    set_symbol_lookup_date('2015-01-01')      # Symbols retrieved from the date January 1, 2015
    
    # Assets to be traded by the algorithm, by asset class
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
    context.multiple = 2.0                  # Arbitrary amount to multiply weights by
    context.sigmoid_mult = 0.75             # k-value for sigmoid function; higher values means high ratios valued less
    context.ddlookback = 252                # Look back a year when calculating drawdown volatility
    context.critpointsfilled = False        # Fill critical points to get dict started
    
    # Dictionary holding the past 3 critical points and prices for each security
    context.past3critpoints = dict.fromkeys(context.secs, None)
    # Stopprice will stop losses, is set in ______ function
    context.stopprice = dict.fromkeys(context.secs, None)
    # Dictionary holding the trends of each security and its strength
    context.trendstrength = dict.fromkeys(context.secs, 0)
    
    # Mock schedule because cannot call from init function, only happens once
    schedule_function(initcritpoints, date_rules.every_day(), time_rules.market_open(minutes = 1))
    
    # Schedule all functions in order: end pertinent trades, find trends, perform trades
    schedule_function(trendanalysis, date_rules.every_day(), time_rules.market_open(minutes = 28))
    schedule_function(trade, date_rules.every_day(), time_rules.market_open(minutes = 30))

# Calculate trend direction 
def trendanalysis(context, data):
    # Get price from past year to get opening price of today
    prices = data.history(context.secs, 'open', context.ddlookback, '1d')
    
    # Check most recent price point to determine trend
    for s in context.secs:
        
        # Calculate average drawdown volatility for past [context.lookback] days
        daily_drawdown = prices[s]/prices[s].rolling(context.lookback).max() - 1.0
        std_daily_drawdown = daily_drawdown.std()
        
        # Update critical points
        updatecritpoints(context, data, prices, s)
        
        # If prevous critical points go min-max-min, must be increasing
        if (context.past3critpoints[s][0].values()[0] < context.past3critpoints[s][1].values()[0]) and (
            context.past3critpoints[s][2].values()[0] < context.past3critpoints[s][1].values()[0]):
                
                # When new price exceeds previous maximum and trend is going up, record trend strength
                if ((prices[s][-1] > context.past3critpoints[s][1].values()[0]) and (
                    context.past3critpoints[s][2].values()[0] < context.past3critpoints[s][0].values()[0])):
                    
                    # Trend strength metric is ratio of distance from 3 critpoints back to most recent critpoint 
                    # and distance from two critpoints back to most recent critpoint
                    context.trendstrength[s] = sigmoid_adjusted(context, (context.past3critpoints[s][0].values()[0] - context.past3critpoints[s][2].values()[0]) /
                                                (context.past3critpoints[s][1].values()[0] - context.past3critpoints[s][0].values()[0]))
                    
                # If on a down trend and price exceeds previous maximum, set trend strength to 0
                elif ((prices[s][-1] > context.past3critpoints[s][1].values()[0]) and (
                    context.past3critpoints[s][2].values()[0] > context.past3critpoints[s][0].values()[0])):
                    
                    context.trendstrength[s] = 0
        
        # If prevous critical points go max-min-max, must be decreasing
        elif (context.past3critpoints[s][0].values()[0] > context.past3critpoints[s][1].values()[0]) and (
            context.past3critpoints[s][2].values()[0] > context.past3critpoints[s][1].values()[0]):
                
                # When new price drops below previous minimum and trend is going down, record trend strength
                if ((prices[s][-1] < context.past3critpoints[s][1].values()[0])and (
                    context.past3critpoints[s][2].values()[0] > context.past3critpoints[s][0].values()[0])):
                    
                    # Trend strength metric is ratio of distance from 3 critpoints back to most recent critpoint 
                    # and distance from two critpoints back to most recent critpoint
                    # MULTIPLED BY -1 BECAUSE BOTH NEGATIVE VALUES WILL CANCEL OUT, THIS IS DOWN TREND THO
                    context.trendstrength[s] = (-1) * sigmoid_adjusted(context, (context.past3critpoints[s][0].values()[0] - context.past3critpoints[s][2].values()[0]) /
                                                       (context.past3critpoints[s][1].values()[0] - context.past3critpoints[s][0].values()[0]))
        
                # If on an up trend and price drops below previous minimum, set trend strength to 0
                elif ((prices[s][-1] < context.past3critpoints[s][1].values()[0]) and (
                    context.past3critpoints[s][2].values()[0] < context.past3critpoints[s][0].values()[0])):
                    
                    context.trendstrength[s] = 0
                    
        # If there is no identifiable trend and no trend is currently going, do not update trend
        else:
            continue
         
# Execute trades
def trade(context, data):
    
    # Get asset weights
    w = context.trendstrength
    
     # Record asset weights, leverage, and cash
    record(leverage = context.account.leverage)
    record(equities = sum(w[s] for s in context.equities))
    record(fixedincome = sum(w[s] for s in context.fixedincomes))
    record(alternative = sum(w[s] for s in context.alternatives))
    record(cash = max(0, context.portfolio.cash) / context.portfolio.portfolio_value)
    
    # Count how many securities have positions
    num_positions = 0
    for s in context.secs:
        if w[s] != 0:
            num_positions += 1
            
    # Perform trades
    for s in context.secs:
        if data.can_trade(s) and s not in get_open_orders():
            if w[s] == 0:
                order_target_percent(s, 0)
            elif w[s] > 0:
                order_target_percent(s, (min(w[s] * context.multiple, context.maxlever)/num_positions))
            elif w[s] < 0:
                order_target_percent(s, (max(w[s] * context.multiple, -context.maxlever)/num_positions))

# Sigmoid loss function so as not to overweight unusual trend strengths
def sigmoid_adjusted(context, t):
    # Ceiling is +1 and floor is -1 centered at 0; k is defined in initalize()
    return 2 / (1 + math.exp(-context.sigmoid_mult * t)) - 1
    
    
# Update moving critical point array (called every day in trendanalysis)
def updatecritpoints(context, data, prices, s):
    
    # If prevous critical points go min-max-min, must be increasing
    if (context.past3critpoints[s][0].values()[0] < context.past3critpoints[s][1].values()[0]) and (
            context.past3critpoints[s][2].values()[0] < context.past3critpoints[s][1].values()[0]):
        
        # Detect new maximums
        if prices[s][-2] > prices[s][-1]:
            context.past3critpoints.update({
               s: [{prices.index[-2]: prices[s][-2]},
                   context.past3critpoints[s][0],
                   context.past3critpoints[s][1]]
               })
        
    # If prevous critical points go max-min-max, must be decreasing
    elif (context.past3critpoints[s][0].values()[0] > context.past3critpoints[s][1].values()[0]) and (
        context.past3critpoints[s][2].values()[0] > context.past3critpoints[s][1].values()[0]):
        
        # Detect new minimums
        if prices[s][-2] < prices[s][-1]:
            context.past3critpoints.update({
               s: [{prices.index[-2]: prices[s][-2]},
                   context.past3critpoints[s][0],
                   context.past3critpoints[s][1]]
               })
        
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
