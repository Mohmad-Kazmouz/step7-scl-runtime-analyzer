"""
cfg – Stufe 4 der Analyse-Pipeline
Kontrollflussgraph (CFG) aus IR-Blöcken aufbauen und analysieren.
"""
from .cfg_builder import CFGBuilder
from .cfg_graph import CFGGraph

__all__ = ["CFGBuilder", "CFGGraph"]
