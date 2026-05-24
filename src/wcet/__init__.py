"""
wcet – Stufe 5 der Analyse-Pipeline
WCET-Berechnung, Hotspot-Erkennung, Pass/Fail-Bewertung.
"""
from .wcet_engine import WCETEngine, WCETResult
from .hotspot_detector import HotspotDetector, Hotspot
from .loop_bound import LoopBoundAnnotator

__all__ = [
    "WCETEngine", "WCETResult",
    "HotspotDetector", "Hotspot",
    "LoopBoundAnnotator",
]
