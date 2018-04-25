# Imports
from quantopian.research import prices, symbols
from quantopian.pipeline.factors import SimpleMovingAverage

import pandas as pd
import datetime

# Research environment

# Select a time range to inspect
period_start = pd.Timestamp('2014-01-01')
period_end = pd.Timestamp('2015-12-31')

# Select a security ticker to inspect
# Top choices: GOOG and GLD both perform well
stock_symbol = 'QQQ'

stock_close = prices(
    assets=symbols(stock_symbol),
    start=period_start,
    end=period_end
)

extremadataframe = pd.DataFrame({
    'price': [],
    'type': [],
    'trend': [],
    }, index=[])
orders = pd.DataFrame({
    'type': [],
    'prev_exitgain': [],
    'marker': []
    }, index=[])
increasing = False
decreasing = False

for date in stock_close.index:
    if date == stock_close.index[1] or date == stock_close.index[0]:
        previousdate=date
        continue
    if stock_close[date] < stock_close[previousdate]:
        if increasing:
            extremadataframe = pd.concat([pd.DataFrame({
                'price': [stock_close[previousdate]],
                'type': ['maximum'],
                'trend': ['incomplete']
            }, index=[previousdate]), extremadataframe],
                     axis=0,join='outer')
            if date > stock_close.index[5]:
                if ((extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] < extremadataframe['price'].shift(-2).loc[pd.Timestamp(previousdate, tz='UTC')]) and 
               (extremadataframe['price'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] < extremadataframe['price'].shift(-3).loc[pd.Timestamp(previousdate, tz='UTC')])):
                    extremadataframe.at[pd.Timestamp(previousdate, tz='UTC'),'trend']='down'
                    # Currently using extrema but in real algorithm should enter position when any point
                    # Goes above the previous trend bracket (previous high or previous low)
                    if (extremadataframe[extremadataframe['trend'] != 'incomplete']['trend'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] == 'up'):
                        orders = pd.concat([pd.DataFrame({
                            'type': ['short'],
                            'prev_exitgain': [0],
                            'marker': 166
                        }, index=[previousdate]), orders],
                             axis=0,join='outer')
                        if (previousdate > orders.iloc[-1].name):
                            orders.at[pd.Timestamp(previousdate, tz='UTC'), 'prev_exitgain'] = extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] - extremadataframe['price'].loc[orders.iloc[orders.index.get_loc(pd.Timestamp(previousdate, tz='UTC'))+1].name]
                if ((extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] > extremadataframe['price'].shift(-2).loc[pd.Timestamp(previousdate, tz='UTC')]) and 
               (extremadataframe['price'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] > extremadataframe['price'].shift(-3).loc[pd.Timestamp(previousdate, tz='UTC')])):
                    extremadataframe.at[pd.Timestamp(previousdate, tz='UTC'),'trend']='up'
                    # Currently using extrema but in real algorithm should enter position when any point
                    # Goes above the previous trend bracket (previous high or previous low)
                    if (extremadataframe[extremadataframe['trend'] != 'incomplete']['trend'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] == 'down'):
                        orders = pd.concat([pd.DataFrame({
                            'type': ['long'],
                            'prev_exitgain': [0],
                            'marker': 162
                        }, index=[previousdate]), orders],
                             axis=0,join='outer')
                        if (previousdate > orders.iloc[-1].name):
                            orders.at[pd.Timestamp(previousdate, tz='UTC'), 'prev_exitgain'] = -1 * (extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] - extremadataframe['price'].loc[orders.iloc[orders.index.get_loc(pd.Timestamp(previousdate, tz='UTC'))+1].name])
        increasing = False
        decreasing = True
    elif stock_close[date] > stock_close[previousdate]:
        if decreasing:
            extremadataframe = pd.concat([pd.DataFrame({
                'price': [stock_close[previousdate]],
                'type': ['minimum'],
                'trend': ['incomplete']
            }, index=[previousdate]), extremadataframe],
                     axis=0,join='outer')
            if date > stock_close.index[5]:
                if ((extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] < extremadataframe['price'].shift(-2).loc[pd.Timestamp(previousdate, tz='UTC')]) and 
               (extremadataframe['price'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] < extremadataframe['price'].shift(-3).loc[pd.Timestamp(previousdate, tz='UTC')])):
                    extremadataframe.at[pd.Timestamp(previousdate, tz='UTC'),'trend']='down'
                    # Currently using extrema but in real algorithm should enter position when any point
                    # Goes above the previous trend bracket (previous high or previous low)
                    if (extremadataframe[extremadataframe['trend'] != 'incomplete']['trend'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] == 'up'):
                        orders = pd.concat([pd.DataFrame({
                            'type': ['short'],
                            'prev_exitgain': [0],
                            'marker': 166
                        }, index=[previousdate]), orders],
                             axis=0,join='outer')
                        if (previousdate > orders.iloc[-1].name):
                            orders.at[pd.Timestamp(previousdate, tz='UTC'), 'prev_exitgain'] = extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] - extremadataframe['price'].loc[orders.iloc[orders.index.get_loc(pd.Timestamp(previousdate, tz='UTC'))+1].name]
                if ((extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] > extremadataframe['price'].shift(-2).loc[pd.Timestamp(previousdate, tz='UTC')]) and 
               (extremadataframe['price'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] > extremadataframe['price'].shift(-3).loc[pd.Timestamp(previousdate, tz='UTC')])):
                    extremadataframe.at[pd.Timestamp(previousdate, tz='UTC'),'trend']='up'
                    # Currently using extrema but in real algorithm should enter position when any point
                    # Goes above the previous trend bracket (previous high or previous low)
                    if (extremadataframe[extremadataframe['trend'] != 'incomplete']['trend'].shift(-1).loc[pd.Timestamp(previousdate, tz='UTC')] == 'down'):
                        orders = pd.concat([pd.DataFrame({
                            'type': ['long'],
                            'prev_exitgain': [0],
                            'marker': 162
                        }, index=[previousdate]), orders],
                             axis=0,join='outer')
                        if (previousdate > orders.iloc[-1].name):
                            orders.at[pd.Timestamp(previousdate, tz='UTC'), 'prev_exitgain'] = -1 * (extremadataframe['price'].loc[pd.Timestamp(previousdate, tz='UTC')] - extremadataframe['price'].loc[orders.iloc[orders.index.get_loc(pd.Timestamp(previousdate, tz='UTC'))+1].name])
        increasing = True
        decreasing = False
        
    previousdate = date

pd.DataFrame({
    stock_symbol: stock_close,
    'z1: UP': extremadataframe[extremadataframe['trend']=='up']['price'],
    'z2: DOWN': extremadataframe[extremadataframe['trend']=='down']['price'],
    #'z3: LONG': orders[orders['type']=='long']['marker'],
    #'z4: SHORT': orders[orders['type']=='short']['marker']
}).plot(style=['-', '^', 'v'], markersize=10)

print("Total gain: $" + str(orders['prev_exitgain'].sum()))
