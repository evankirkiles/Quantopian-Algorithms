# Quantopian-Algorithms
Algorithms and research used on the Quantopian platform. These files are only runnable through Quantopian's Jupyter notebooks (for research) or Algorithm API (for algorithms)–you will not be able to import the quantopian library through a normal compiler.

### Tested Strategies
#### 1. Pairs trading
Algorithms: pairstrading_hedgeratio.py

Initially used cointegrated oil companies found in the research environment, but the oil market is so volatile that pairs trading didn't perform well. The strategy requires the difference in stock prices to mean revert, which highly random stock patterns do not satisfy well. I transitioned the algorithm to healthcare companies Lifepoint Health Inc. and Universal Health Services CLS-B, also cointegrated securities identified with the research environment and immediately saw a much better performance. Major industry announcements seem to play a large factor in the success of pairs trading; for example, the strategy tanks in October 2017 after the president announces his executive healthcare plan. Would probably need to use active algorithm management to guard against such irregularities.

#### 2. Higher/lower extrema
Algorithms: trendrecognition.py

This trend recognition strategy revolves around the notion that up trends are identified by higher highs and higher lows, while down trends are identified by lower highs and lower lows. Unfortunately, this trend recognition technique most definitely should not be used in algorithms–it is successful only under very specific trend patterns, which if not met result in terrible negative returns. However, gave me a lot of good experience as my first original trend research and implementation into algorithm form.
