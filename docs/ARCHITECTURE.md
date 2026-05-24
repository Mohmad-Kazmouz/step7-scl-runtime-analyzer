# Architektur: SCL Runtime Analyzer

## Pipeline-Übersicht

```
SCL-FB-Datei (SIMATIC Manager Export)
        │
        ▼
┌─────────────────┐
│  1. Parser      │  src/parser/
│  Lexer → AST    │  SCLParser, ASTNode-Hierarchie
└────────┬────────┘
         │ FunctionBlockNode
         ▼
┌─────────────────┐
│  2. Semantik    │  src/semantic/
│  Symboltabelle  │  SemanticAnalyzer, SymbolTable
└────────┬────────┘
         │ SymbolTable (Typen, Speicherorte)
         ▼
┌─────────────────┐
│  3. IR-Erzeugung│  src/ir/
│  AST → IRBlöcke │  IRGenerator, IRBlock, IROpcode
└────────┬────────┘
         │ list[IRBlock]
         ▼
┌─────────────────┐
│  4. CFG-Aufbau  │  src/cfg/
│  Blöcke → Graph │  CFGBuilder, CFGGraph (networkx)
└────────┬────────┘
         │ CFGGraph (DAG nach Schleifenauflösung)
         ▼
┌─────────────────┐
│  5. WCET        │  src/wcet/
│  Kritischer Pfad│  WCETEngine, HotspotDetector
└────────┬────────┘
         │ WCETResult + list[Hotspot]
         ▼
┌─────────────────┐
│  6. Reporter    │  src/reporter/
│  JSON/HTML/CSV  │  Reporter
└─────────────────┘
```

## Schlüsselentscheidungen

### Warum kein Syntaxfehler-Reporting?
Der Analyzer setzt kompilierbaren SCL-Code voraus (Vorbedingung: SIMATIC Manager
hat den Code bereits erfolgreich kompiliert). Dies vereinfacht den Parser erheblich
und erlaubt es, den Fokus vollständig auf die Laufzeitcharakteristik zu legen.

### Warum ANTLR 4?
ANTLR erzeugt einen robusten LL(*)-Parser aus einer formalen Grammatik.
Im Vergleich zu handgeschriebenen Parsern oder Regex-Ansätzen ist die
SCL-Grammatik in `grammar/SCL.g4` wartbar, erweiterbar und testbar.

### Warum networkx für den CFG?
networkx bietet eingebaute Algorithmen für Longest-Path (DAG) und
Shortest-Path, die direkt für WCET bzw. BCET genutzt werden.

## S7-300 Speicherhierarchie (Latenzen, CPU 315-2 DP)

| Bereich       | Lesen   | Schreiben | Hinweis                    |
|---------------|---------|-----------|----------------------------|
| Lokalstack (L)| 50 ns   | 60 ns     | VAR_TEMP – schnellste Option|
| Merker (M)    | 150 ns  | 180 ns    | Globale Merker              |
| Instanz-DB    | 200 ns  | 250 ns    | VAR / VAR_INPUT / VAR_OUTPUT|
| Shared-DB     | 400 ns  | 500 ns    | Expliziter DB-Zugriff       |
