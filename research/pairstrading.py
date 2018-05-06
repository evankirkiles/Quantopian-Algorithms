# Imports
import numpy as np
import pandas as pd

import statsmodels
from statsmodels.tsa.stattools import coint
import seaborn

import matplotlib.pyplot as plt

# Set starting date and ending date
start_date = '2014-01-01'
end_date = '2015-01-01'

# Finds cointegrated pairs from given array of securities pricings
def find_cointegrated_pairs(securities_panel):
    n = len(securities_panel.minor_axis)
    score_matrix = np.zeros((n, n))
    pvalue_matrix = np.ones((n, n))
    keys = securities_panel.keys
    pairs = []
    
    # Cycles through all combinations of two securities and checks cointegration on each
    for i in range(n):
        for j in range(i+1, n):
            S1 = securities_panel.minor_xs(securities_panel.minor_axis[i])
            S2 = securities_panel.minor_xs(securities_panel.minor_axis[j])
            result = coint(S1, S2)
            score = result[0]
            pvalue = result[1]
            score_matrix[i, j] = score
            pvalue_matrix[i, j] = pvalue
            
            # Returns statistically significant pairs
            if pvalue < 0.05:
                pairs.append((securities_panel.minor_axis[i], securities_panel.minor_axis[j]))
                
    return score_matrix, pvalue_matrix, pairs
    
# Create symbols array of oil companies and the S&P 500
symbol_list = ['XOM', 'BP', 'RDS-B', 'COP', 'MRO', 'PXD', 'STO', 'PZE', 'SHI', 'COG', 'CLR', 'CRZO', 'SPY']
securities_panel = get_pricing(symbol_list, fields=['price'], start_date=start_date, end_date=end_date)
securities_panel.minor_axis = map(lambda x: x.symbol, securities_panel.minor_axis)

# Show a heatmap of the p-values of the cointegration tests between stock pairs.
# Only stock pairs above the upper-diagonal shown to improve visibility.
scores,pvalues, pairs = find_cointegrated_pairs(securities_panel)

seaborn.heatmap(pvalues, xticklabels=symbol_list, yticklabels=symbol_list, 
                cmap='RdYlGn_r', mask = (pvalues >= 0.95))
print pairs
