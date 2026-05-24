"""
scl_parser.py – Haupteinstiegspunkt des Parsers

Koordiniert Lexer → Token-Stream → Parser → AST.
Setzt voraus, dass der SCL-Code bereits kompilierbar ist (kein Syntaxfehler-Reporting).
"""
from __future__ import annotations
from pathlib import Path
import antlr4
from .ast_nodes import FunctionBlockNode
from .generated.SCLLexer import SCLLexer
from .generated.SCLParser import SCLParser as _ANTLRParser
from .ast_builder import ASTBuilder


class SCLParser:
    """
    Liest eine SCL-FB-Quelldatei und erzeugt den AST.

    Verwendung::

        parser = SCLParser()
        ast = parser.parse_file(Path("FB10_Regelung.scl"))
        print(ast.name)  # 'FB10_Regelung'
    """

    def parse_file(self, path: Path) -> FunctionBlockNode:
        """
        Liest die Datei und gibt den AST-Wurzelknoten zurück.

        :param path: Pfad zur SCL-FB-Quelldatei
        :raises FileNotFoundError: Datei existiert nicht
        :raises ValueError: Datei enthält keinen gültigen FUNCTION_BLOCK
        :return: FunctionBlockNode als Wurzel des AST
        """
        if not path.exists():
            raise FileNotFoundError(f"SCL-Datei nicht gefunden: {path}")

        source = path.read_text(encoding="utf-8")
        return self.parse_string(source, source_name=path.name)

    def parse_string(self, source: str, source_name: str = "<string>") -> FunctionBlockNode:
        """
        Parst SCL-Quelltext aus einem String.

        :param source: SCL-Quelltext (muss FUNCTION_BLOCK ... END_FUNCTION_BLOCK enthalten)
        :param source_name: Bezeichnung der Quelle (für Fehlermeldungen)
        :return: FunctionBlockNode als Wurzel des AST
        """
        if "FUNCTION_BLOCK" not in source.upper():
            raise ValueError(
                f"'{source_name}' enthält keinen FUNCTION_BLOCK. "
                "Nur FB-Dateien aus dem SIMATIC Manager werden unterstützt."
            )

        input_stream = antlr4.InputStream(source)
        lexer = SCLLexer(input_stream)
        token_stream = antlr4.CommonTokenStream(lexer)
        parser = _ANTLRParser(token_stream)
        tree = parser.functionBlock()
        builder = ASTBuilder()
        return builder.visit(tree)
