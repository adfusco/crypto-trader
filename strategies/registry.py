from strategies.mean_reversion.mr_basic import MeanReversionBasic
from strategies.mean_reversion.mr_multi import MeanReversionMulti
from strategies.mean_reversion.mr_pairs import PairsMeanReversion

# name -> class, so config files can reference strategies by string and stay
# free of direct class imports.
STRATEGY_REGISTRY = {
    'mr_basic': MeanReversionBasic,
    'mr_multi': MeanReversionMulti,
    'mr_pairs': PairsMeanReversion,
}
