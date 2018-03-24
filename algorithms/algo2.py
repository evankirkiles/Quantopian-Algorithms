"""
This algorithm rates stocks based on the StockTwits bull minus bear factor, and longs the top X% and shorts the bottom X%. Easily
better than the first algorithm as it was very non-volatile due to the implemented risk methods. However, the returns were still 
far below the market. Used the getting started tutorial for some help on this one.
"""
import quantopian.algorithm as algo
import quantopian.optimize as opt

from quantopian.pipeline import Pipeline
from quantopian.pipeline.experimental import risk_loading_pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data.psychsignal import stocktwits
from quantopian.pipeline.factors import SimpleMovingAverage
from quantopian.pipeline.filters import QTradableStocksUS


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every Monday when the market opens
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
    
    # Set constraints
    context.max_leverage = 1.0
    context.max_pos_size = 0.015
    context.max_turnover = 0.95

    # Create our dynamic stock selector.
    algo.attach_pipeline(make_pipeline(), 'pipeline')
    algo.attach_pipeline(risk_loading_pipeline(), 'risk_pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation
    on pipeline can be found here:
    https://www.quantopian.com/help#pipeline-title
    """

    # Base universe set to QTradableStocksUS()
    base_universe = QTradableStocksUS()

    # Sentiment score, based on a moving average of the bull minus bear factor
    sentiment_score = SimpleMovingAverage(
        inputs=[stocktwits.bull_minus_bear],
        window_length=3,
    )

    pipe = Pipeline(
        columns={
            'sentiment_score': sentiment_score
        },
        screen=(base_universe&sentiment_score.notnull()),
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline')
    context.risk_factor_betas = algo.pipeline_output('risk_pipeline')

    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index


def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    
    # Attempts to allocate capital to assets based on sentiment score
    objective = opt.MaximizeAlpha(
        context.output.sentiment_score
    )
    
    # Constrain positions
    constrain_pos_size = opt.PositionConcentration.with_equal_bounds(
        -context.max_pos_size,
        context.max_pos_size
    )
    
    # Constrain risk exposure
    factor_risk_constraints = opt.experimental.RiskModelExposure(
        context.risk_factor_betas,
        version = opt.Newest
    )
    
    # Ensure long and short books are roughly the same size
    dollar_neutral = opt.DollarNeutral()
    
    # Constrain target portfolio's leverage
    max_leverage = opt.MaxGrossExposure(context.max_leverage)
    
    # Constrain portfolio turnover
    max_turnover = opt.MaxTurnover(context.max_turnover)
    
    algo.order_optimal_portfolio(
        objective=objective,
        constraints=[max_leverage,
                     dollar_neutral,
                     max_turnover,
                     constrain_pos_size,
                     factor_risk_constraints]
    )

def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass


def handle_data(context, data):
    """
    Called every minute.
    """
    pass
