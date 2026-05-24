"""
ir – Stufe 3 der Analyse-Pipeline
Intermediate Representation (IR): vereinfachte, hardwareunabhängige
Darstellung der FB-Logik als lineare Befehlssequenz.
"""
from .ir_nodes import IRInstruction, IROpcode, IRBlock
from .ir_generator import IRGenerator

__all__ = ["IRInstruction", "IROpcode", "IRBlock", "IRGenerator"]
