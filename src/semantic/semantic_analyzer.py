"""
semantic_analyzer.py – Semantische Analyse des AST

Traversiert den AST (Visitor-Pattern) und baut die Symboltabelle auf.
Klassifiziert jeden Bezeichner nach Speicherort und ordnet CPU-Zugriffszeiten zu.
"""
from __future__ import annotations
from ..parser.ast_nodes import (
    ASTNode, FunctionBlockNode, VarSectionNode, VariableNode, IdentifierNode,
)
from .symbol_table import SymbolTable, Symbol, SymbolKind, StorageLocation


# Abbildung: VAR-Abschnittstyp → SymbolKind + StorageLocation
_SECTION_MAP: dict[str, tuple[SymbolKind, StorageLocation]] = {
    "VAR":        (SymbolKind.VAR_LOCAL,  StorageLocation.INSTANCE_DB),
    "VAR_INPUT":  (SymbolKind.VAR_INPUT,  StorageLocation.INSTANCE_DB),
    "VAR_OUTPUT": (SymbolKind.VAR_OUTPUT, StorageLocation.INSTANCE_DB),
    "VAR_IN_OUT": (SymbolKind.VAR_IN_OUT, StorageLocation.INSTANCE_DB),
    "VAR_TEMP":   (SymbolKind.VAR_TEMP,   StorageLocation.LOCAL_STACK),
}


class SemanticAnalyzer:
    """
    Führt die semantische Analyse durch und gibt eine befüllte Symboltabelle zurück.

    Verwendung::

        analyzer = SemanticAnalyzer(cpu_profile)
        table = analyzer.analyze(ast)
    """

    def __init__(self, cpu_profile) -> None:
        """
        :param cpu_profile: CPU-Profil-Objekt mit Zugriffszeiten pro StorageLocation
        """
        self._profile = cpu_profile
        self._table = SymbolTable()

    def analyze(self, fb_node: FunctionBlockNode) -> SymbolTable:
        """
        Analysiert den AST eines Funktionsbausteins.

        :param fb_node: Wurzelknoten des AST
        :return: Befüllte Symboltabelle
        """
        for section in fb_node.var_sections:
            self._process_var_section(section)
        return self._table

    def _process_var_section(self, section: VarSectionNode) -> None:
        kind, storage = _SECTION_MAP.get(
            section.kind, (SymbolKind.VAR_LOCAL, StorageLocation.INSTANCE_DB)
        )
        for var in section.variables:
            read_ns, write_ns = self._profile.get_access_times(storage)
            symbol = Symbol(
                name=var.name,
                type_name=var.type_name,
                kind=kind,
                storage=storage,
                read_time_ns=read_ns,
                write_time_ns=write_ns,
                line_declared=var.line,
            )
            self._table.define(symbol)
