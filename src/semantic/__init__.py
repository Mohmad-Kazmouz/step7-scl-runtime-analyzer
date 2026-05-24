"""
semantic – Stufe 2 der Analyse-Pipeline
Symboltabelle und Speicherzugriffs-Klassifikation.
Eingabe: AST
Ausgabe: annotierter AST + Symboltabelle
"""
from .symbol_table import SymbolTable, Symbol, SymbolKind, StorageLocation
from .semantic_analyzer import SemanticAnalyzer

__all__ = [
    "SymbolTable", "Symbol", "SymbolKind", "StorageLocation",
    "SemanticAnalyzer",
]
