###########################################################################################
# Pairs Trading
# Evan Kirkiles, 2018
###########################################################################################
# Based off of Ernie Chan's pairs trading with hedge ratio.
# Uses cointegrated healthcare company pairs found in the research environment.
# Initially used oil companies, but oil market far too volatile for pairs trading.

import numpy as np
import statsmodels.api as sm
import pandas as pd
from zipline.utils import tradingcalendar
import pytz

# Initialize all variables and schedule functions
def initialize(context):
    
    # Quantopian backtester specific variables:
    # Set slippage and commission costs to mimic real trading
    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=1))
    set_symbol_lookup_date('2014-01-01')
    
    # Set stock pairs to be traded from research
    context.stock_pairs = [(symbol('LPNT'), symbol('UHS'))]
    context.all_stocks=[]
    for pair in context.stock_pairs:
        context.all_stocks.append(pair[0])
        context.all_stocks.append(pair[1])
    
    context.num_pairs = len(context.stock_pairs)
    
    # Strategy specific variables:
    context.lookback = 20                # Used for regression
    context.z_window = 20                # Used for Z-score calculation, msut be <= lookback

    context.spread = np.ndarray((context.num_pairs, 0))
    context.inLong = [False] * context.num_pairs
    context.inShort = [False] * context.num_pairs
    
    # Schedule checking pairs for 30 minutes every day before market close
    schedule_function(func=check_pair_status, date_rule=date_rules.every_day(), time_rule=time_rules.market_close(minutes=30))
        
# Check data and rebalance if necessary
def check_pair_status(context, data):
    if get_open_orders():
        return
    
    prices = data.history(context.all_stocks, 'price', 35, '1d').iloc[-context.lookback:]
    new_spreads = np.ndarray((context.num_pairs, 1))

    for i in range(context.num_pairs):
        
        # Get the stocks from the pairs list
        (stock_y, stock_x) = context.stock_pairs[i]
        
        # Get the pricing data
        Y = prices[stock_y]
        X = prices[stock_x]
        
        # TRY to compute a hedge ratio
        try:
            hedge = hedge_ratio(Y, X, add_const=True)
        except ValueError as e:
            log.debug(e)
            return
        
        # Calculate the spread based on the new hedge ratio
        new_spreads[i, :] = Y[-1] - hedge * X[-1]
        
        # If there is enough lookback in spreads
        if context.spread.shape[-1] > context.z_window:
            
            # Keep only the z-score lookback period and use it to calculate the z-score
            spreads = context.spread[i, -context.z_window:]
            zscore = (spreads[-1] - spreads.mean()) / spreads.std()
            
            # TRADING LOGIC:
            
            # When going short in the pair and the zscore goes negative, exit the position
            if context.inShort[i] and zscore < 0.0 and all(data.can_trade([stock_x, stock_y])):
                exit_pair(context, stock_x, stock_y, i)
                return
            # When going long in the pair and the zscore goes positive, exit the position
            if context.inLong[i] and zscore > 0.0 and all(data.can_trade([stock_x, stock_y])):
                exit_pair(context, stock_x, stock_y, i)
                return
            
            # If zscore exceeds -1.0 and not already in a long position, enter the position
            if zscore < -1.0 and (not context.inLong[i]) and all(data.can_trade([stock_x, stock_y])):
                y_target_shares = 1
                x_target_shares = hedge
                context.inLong[i] = True
                context.inShort[i] = False
                
                (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_shares, x_target_shares, Y[-1], X[-1])
                order_target_percent(stock_y, y_target_pct * (1.0/context.num_pairs) / float(context.num_pairs))
                order_target_percent(stock_x, x_target_pct * (1.0/context.num_pairs) / float(context.num_pairs))
                record(Y_pct=y_target_pct, X_pct=x_target_pct)
                return
            # If zscore exceeds 1.0 and not already in a short position, enter the position
            if zscore > 1.0 and (not context.inShort[i]) and all(data.can_trade([stock_x, stock_y])):
                y_target_shares = -1
                x_target_shares = hedge
                context.inLong[i] = False
                context.inShort[i] = True
                
                (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_shares, x_target_shares, Y[-1], X[-1])
                order_target_percent(stock_y, y_target_pct * (1.0/context.num_pairs) / float(context.num_pairs))
                order_target_percent(stock_x, x_target_pct * (1.0/context.num_pairs) / float(context.num_pairs))
                record(Y_pct=y_target_pct, X_pct=x_target_pct)
                return
                
    context.spread = np.hstack([context.spread, new_spreads])
          
# Exit pair function
def exit_pair(context, stock_x, stock_y, i):
    order_target(stock_y, 0)
    order_target(stock_x, 0)
    context.inShort[i] = False
    context.inLong[i] = False
    record(X_pct = 0, Y_pct = 0)
    return

# Calculate hedge ratio
def hedge_ratio(Y, X, add_const=True):
    
    # Only get the multiplier
    if add_const:
        
        # Calculate hedge ratio by finding slope of linear regression
        X = sm.add_constant(X)
        model = sm.OLS(Y, X).fit()
        return model.params[1]
    
    # Get both the multiplier and the intercept
    model = sm.OLS(Y, X).fit()
    return model.params.values

# Compute the required holdings percents for each stock
def computeHoldingsPct(yShares, xShares, yPrice, xPrice):
    yDol = yShares * yPrice
    xDol = xShares * xPrice
    notionalDol = abs(yDol) + abs(xDol)
    y_target_pct = yDol / notionalDol
    x_target_pct = xDol / notionalDol
    return (y_target_pct, x_target_pct)
