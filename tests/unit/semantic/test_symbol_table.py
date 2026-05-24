"""Unit-Tests: Symboltabelle"""
import pytest
from src.semantic.symbol_table import SymbolTable, Symbol, SymbolKind, StorageLocation


def _make_sym(name="rTemp", kind=SymbolKind.VAR_TEMP, storage=StorageLocation.LOCAL_STACK):
    return Symbol(name=name, type_name="REAL", kind=kind, storage=storage)


def test_define_and_resolve():
    table = SymbolTable()
    sym = _make_sym("rTemp")
    table.define(sym)
    assert table.resolve("rTemp") is sym


def test_resolve_case_insensitive():
    table = SymbolTable()
    table.define(_make_sym("rTemp"))
    assert table.resolve("RTEMP") is not None
    assert table.resolve("rtemp") is not None


def test_resolve_unknown_returns_none():
    table = SymbolTable()
    assert table.resolve("doesNotExist") is None


def test_len():
    table = SymbolTable()
    table.define(_make_sym("a"))
    table.define(_make_sym("b"))
    assert len(table) == 2


def test_overwrite_same_name():
    table = SymbolTable()
    table.define(_make_sym("x"))
    sym2 = _make_sym("x", kind=SymbolKind.VAR_INPUT)
    table.define(sym2)
    assert table.resolve("x").kind == SymbolKind.VAR_INPUT
