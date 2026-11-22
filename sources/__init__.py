from sources.aggregator import Buscape, Zoom
from sources.aliexpress import AliExpress
from sources.amazon import Amazon
from sources.havan import Havan
from sources.kabum import Kabum
from sources.terabyte import Terabyte
from sources.mercadolivre import MercadoLivre

REGISTRY = {c.name: c for c in (Zoom, Buscape, Kabum, Amazon, Havan, AliExpress, MercadoLivre, Terabyte)}
