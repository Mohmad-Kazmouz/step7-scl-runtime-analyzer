# SCL Runtime Analyzer

Statische Laufzeitanalyse (WCET) für Siemens SCL-Funktionsbausteine (FB) auf der S7-300-Plattform.

## Voraussetzungen

- Python 3.10+
- ANTLR 4 Runtime
- Siehe `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Verwendung

```bash
python -m scl_analyzer analyze ./mein_fb.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms
```

## Projektstruktur

```
scl_runtime_analyzer/
├── src/               # Quellcode der Analyse-Engine
│   ├── parser/        # Lexer + Parser → AST
│   ├── semantic/      # Symboltabelle & Typanalyse
│   ├── ir/            # Intermediate Representation
│   ├── cfg/           # Kontrollflussgraph
│   ├── wcet/          # WCET-Berechnung (kritischer Pfad)
│   ├── profiles/      # CPU-Profil-Loader
│   ├── reporter/      # Ergebnis-Export (JSON, HTML, CSV)
│   └── cli/           # Kommandozeilen-Interface
├── tests/             # Unit- und Integrationstests
├── profiles/          # S7-300 CPU-Profile (JSON)
├── docs/              # Technische Dokumentation
└── scripts/           # Hilfsskripte (Batch-Analyse, Kalibrierung)
```
