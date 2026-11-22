from sources.aggregator import Buscape, Zoom
from sources.kabum import Kabum

REGISTRY = {c.name: c for c in (Zoom, Buscape, Kabum)}
