"""
This algorithm was awful, to put it simply. Had consistently lower returns than the market while also being very volatile and had
a Sharpe ratio of around 1.87. However, was a good starting point and introduced me to coding algorithms. Tutorial I used for help
was titled Pipelines in Quantopian tutorials page.
"""
import quantopian.algorithm as algo
import quantopian.optimize as opt
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import SimpleMovingAverage, AverageDollarVolume
from quantopian.pipeline.filters import Q1500US
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.filters.fundamentals import IsPrimaryShare

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every week when the market opens.
    algo.schedule_function(
        rebalance,
        algo.date_rules.week_start(),
        algo.time_rules.market_open(),
    )

    # Record tracking variables at the end of each day.
    algo.schedule_function(
        record_vars,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(),
    )

    # Create our dynamic stock selector.
    algo.attach_pipeline(make_pipeline(), 'pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation
    on pipeline can be found here:
    https://www.quantopian.com/help#pipeline-title
    """

    # Set universe to our filter (the same as Q1500US())
    base_universe = filter_universe()

    # Basic mean reversion strategy
    # 10-day close price average
    mean_10 = SimpleMovingAverage(
        inputs = [USEquityPricing.close],
        window_length = 10,
        mask = base_universe
    )
    
    # 30-day close price average
    mean_30 = SimpleMovingAverage(
        inputs = [USEquityPricing.close],
        window_length = 30,
        mask = base_universe
    )
    
    percent_difference = (mean_10 - mean_30)/mean_30
    
    # Top and bottom 75 filters using percent_difference
    shorts = percent_difference.top(75)
    longs = percent_difference.bottom(75)
    
    # Combine these filters into a pipeline screen
    securities_to_trade = (shorts | longs)

    pipe = Pipeline(
        columns={
            'longs': longs,
            'shorts': shorts
        },
        screen = securities_to_trade
    )
    
    return pipe

def compute_target_weights(context, data):
    """
    Compute ordering weights
    """
    # Create empty target weights dict to map security weights to
    weights = {}
    
    # Compute even target weights for securities in longs/shorts lists
    if context.longs and context.shorts:
        long_weight = 0.5 / len(context.longs)
        short_weight = 0.5 / len(context.shorts)
    else:
        return weights
    
    # Exit positions in portfolio not in longs/shorts lists
    for security in context.portfolio.positions:
        if security not in context.longs and security not in context.shorts and data.can_trade(security):
            weights[security] = 0
            
    # Set weights for longs and shorts
    for security in context.longs:
        weights[security] = long_weight   
    for security in context.shorts:
        weights[security] = short_weight
        
    return weights

def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    # Output pipeline results
    context.output = algo.pipeline_output('pipeline')

    # Go long in securities where 'longs' value = 'True'
    context.longs = []
    for sec in context.output[context.output['longs']].index.tolist():
        if data.can_trade(sec):
            context.longs.append(sec)
            
    # Go short in securities where 'shorts' value = 'True'
    context.shorts = []
    for sec in context.output[context.output['shorts']].index.tolist():
        if data.can_trade(sec):
            context.shorts.append(sec)
    
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    
    # Calculate target weights to rebalance
    target_weights = compute_target_weights(context, data)
    
    # If we have target weights, rebalance portfolio
    if target_weights:
        algo.order_optimal_portfolio(
            objective=opt.TargetWeights(target_weights),
            constraints=[]
        )


def record_vars(context, data):
    """
    Record variables at the end of each day.
    """
    
    longs=shorts=0
    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
            longs += 1
        if position.amount < 0:
            shorts += 1
    
    # Record the variables
    record(
        leverage = context.account.leverage,
        long_count = longs,
        short_count = shorts
    )

def handle_data(context, data):
    """
    Called every minute.
    """
    pass

def filter_universe():
    """
    8 filters:
     - Is a primary share
     - Is listed as a common stock
     - Is not a depositary receipt (ADR/GDR)
     - Is not trading over-the-counter (OTC)
     - Is not when-issued (WI)
     - Doesn't have a name indicating it's a limited partnership (LP)
     - Doesn't have a company reference entry indicating it's a LP
     - Is not an ETF (has Morningstar fundamental data)  
    """
    
    primary_share = IsPrimaryShare()
    common_stock = Fundamentals.security_type.latest.eq('ST00000001')
    not_depositary = ~Fundamentals.is_depositary_receipt.latest
    not_otc = ~Fundamentals.exchange_id.latest.startswith('OTC')
    not_wi = ~Fundamentals.symbol.latest.endswith('.WI')
    not_lp_name = ~Fundamentals.standard_name.latest.matches('.* L[. ]?P.?$')
    not_lp_balance_sheet = Fundamentals.limited_partnership.latest.isnull()
    have_market_cap = Fundamentals.market_cap.latest.notnull()
    
    # Combine the filters
    tradeable_stocks = (primary_share & common_stock & not_depositary & not_otc & not_wi &
                        not_lp_name & not_lp_balance_sheet & have_market_cap)
    
    # Create final filter for top 30% of tradeable stocks by 20-day average dollar value
    tradeable_universe = AverageDollarVolume(
        window_length = 20,
        mask = tradeable_stocks
    ).percentile_between(70, 100)
    
    # THESE FILTER SETTINGS CAN BE REPLACED BY THE FILTER Q1500US() for tradeable_universe
    mask = tradeable_universe
    
    return mask
