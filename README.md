# CLR Parser Studio

> A complete Canonical LR(1) Parser implementation with interactive visualization for compiler construction education

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

---

## Overview

**CLR Parser Studio** is a full-featured Canonical LR(1) parser generator and visualizer. It implements the complete CLR parsing algorithm as described in the Dragon Book (Compilers: Principles, Techniques, and Tools), providing an intuitive graphical interface to understand one of the most powerful deterministic parsing techniques.

LR(1) parsers use **one token of lookahead** to make parsing decisions, enabling them to handle a broader class of context-free grammars than SLR(1) or LR(0) parsers. This tool makes the complex internals of CLR parsing accessible and visual.

---

## Features

### Core Parser Engine
- **LR(1) Item Generation** - Items with lookahead symbols: `[A -> alpha . beta, a]`
- **FIRST Set Computation** - Automatic calculation with epsilon propagation
- **Closure Operation** - Full LR(1) closure with lookahead computation using FIRST(beta a)
- **GOTO Function** - State transitions for both terminals and non-terminals
- **Canonical Collection** - Complete LR(1) automaton construction
- **Parsing Tables** - ACTION and GOTO table generation
- **Conflict Detection** - Identifies shift-reduce and reduce-reduce conflicts
- **Input Parsing** - Step-by-step parsing with detailed trace

### Interactive Visualization
- **Grammar Editor** - Input grammars with intuitive syntax
- **Augmented Grammar Display** - Shows augmented grammar with production numbering
- **FIRST Sets View** - Displays computed FIRST sets for all non-terminals
- **State Inspector** - Browse all LR(1) states with their complete item sets
- **Automaton Diagram** - Visual graph of the LR(1) automaton with:
  - Zoomable and pannable canvas
  - State nodes showing LR(1) items
  - Labeled transition arrows
  - Auto-layout algorithm
- **Parsing Table View** - Complete ACTION/GOTO table with conflict highlighting
- **Conflict Analyzer** - Detailed conflict explanations
- **Parsing Simulator** - Step-by-step or auto-run parsing simulation with:
  - Stack visualization
  - Input buffer display
  - Action trace table

---

## Screenshots

```
+------------------+     +------------------+     +------------------+
|   Grammar Tab    |     |   States Tab     |     |   Diagram Tab    |
|                  |     |                  |     |                  |
| Productions:     |     | I0: [S'->. S,$]  |     |   [I0]--a-->[I1] |
| 0: S' -> S       |     |     [S->. aAd,$] |     |    |             |
| 1: S -> a A d    |     |     ...          |     |    b             |
| ...              |     |                  |     |    v             |
|                  |     | I1: [S->a. Ad,$] |     |   [I2]--c-->[I3] |
| FIRST(S) = {a,b} |     |     [A->. c,d]   |     |                  |
+------------------+     +------------------+     +------------------+
```

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually included with Python)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/clr-parser-studio.git
cd clr-parser-studio

# Run the application
python LR1_Parser/main.py
```

No additional dependencies required - uses only Python standard library!

---

## Usage

### Grammar Syntax

```
NonTerminal -> symbol1 symbol2 symbol3
NonTerminal -> alternative1 | alternative2
```

**Rules:**
- Use `->` or `->` for production arrows
- Separate symbols with spaces
- Use `|` for alternatives on the same line
- Use `epsilon` or empty for epsilon productions
- First production's LHS becomes the start symbol

**Conventions:**
- Uppercase letters typically represent non-terminals (E, T, F, S)
- Lowercase letters/words typically represent terminals (id, +, *, num)
- The parser auto-detects terminal vs non-terminal status

### Example Grammars

**Classic Expression Grammar (LR(1) compatible):**
```
E -> E + T
E -> T
T -> T * F
T -> F
F -> ( E )
F -> id
```

**Grammar demonstrating LR(1) power over SLR(1):**
```
S -> a A d
S -> b B d
S -> a B e
S -> b A e
A -> c
B -> c
```
This grammar is LR(1) but NOT SLR(1) - the lookahead distinguishes `A -> c` from `B -> c`.

**Dangling Else (causes shift-reduce conflict):**
```
S -> if E then S else S
S -> if E then S
S -> a
E -> b
```

### Parsing Input

Enter space-separated tokens:
```
id + id * id
```

---

## Understanding LR(1) Parsing

### What Makes LR(1) Special?

LR(1) items have the form **[A -> alpha . beta, a]** where:
- `A -> alpha beta` is a grammar production
- The dot `.` indicates parsing progress
- `a` is a **lookahead terminal** for reduction decisions

The lookahead allows LR(1) to defer reduction decisions until seeing the next input symbol, resolving ambiguities that confuse simpler parsers.

### CLR vs Other LR Variants

| Parser | Items | States | Power |
|--------|-------|--------|-------|
| LR(0) | No lookahead | Fewest | Weakest |
| SLR(1) | Uses FOLLOW sets | Same as LR(0) | Medium |
| **CLR/LR(1)** | **Per-item lookahead** | **Most** | **Strongest** |
| LALR(1) | Merged LR(1) cores | Same as LR(0) | Near CLR |

### Parsing Table Actions

| Entry | Meaning |
|-------|---------|
| `sN` | **Shift** input symbol, go to state N |
| `rN` | **Reduce** by production N |
| `acc` | **Accept** - parsing complete |
| `N` | **GOTO** state N (for non-terminals) |
| (empty) | **Error** - syntax error |

---

## Project Structure

```
CLR-Parser-Studio/
|-- LR1_Parser/
|   |-- __init__.py
|   |-- lr1_parser.py    # Core CLR algorithm implementation
|   |-- ui.py            # Tkinter GUI application
|   |-- main.py          # Application entry point
|-- README.md
```

### Module Details

**`lr1_parser.py`** - Core Implementation
- `Production` - Immutable production rule representation
- `LR1Item` - LR(1) item with production, dot position, and lookahead
- `LR1State` - State containing item set and transitions
- `Grammar` - Grammar with FIRST set computation
- `LR1Parser` - Main parser class with closure, goto, automaton building
- `parse_grammar_text()` - Grammar text parser

**`ui.py`** - Visualization Interface
- `LR1ParserApp` - Main application window
- Grammar input with syntax highlighting
- Tabbed interface for different views
- Canvas-based automaton visualization
- Simulation controls and trace display

---

## Algorithm Implementation

### Closure Operation
```python
CLOSURE(I):
    repeat
        for each item [A -> alpha . B beta, a] in I:
            for each production B -> gamma:
                for each terminal b in FIRST(beta a):
                    add [B -> . gamma, b] to I
    until no new items added
    return I
```

### GOTO Function
```python
GOTO(I, X):
    J = {}
    for each item [A -> alpha . X beta, a] in I:
        add [A -> alpha X . beta, a] to J
    return CLOSURE(J)
```

### Canonical Collection Construction
```python
items(G'):
    C = {CLOSURE({[S' -> . S, $]})}
    repeat
        for each set I in C:
            for each grammar symbol X:
                if GOTO(I, X) is not empty and not in C:
                    add GOTO(I, X) to C
    until no new sets added
    return C
```

---

## Educational Value

This tool is designed for:
- **Compiler Design Courses** - Visualize abstract parsing concepts
- **Self-Study** - Learn CLR parsing interactively
- **Teaching** - Demonstrate parsing step-by-step in lectures
- **Research** - Analyze grammar properties and conflicts

### Learning Objectives
1. Understand LR(1) item structure and lookahead significance
2. Trace closure and goto operations visually
3. See how parsing tables are constructed from automata
4. Identify and understand parsing conflicts
5. Follow shift-reduce parsing step by step

---

## Technical Specifications

- **Parsing Power:** Full LR(1) / CLR
- **Grammar Type:** Context-Free Grammars (CFG)
- **Conflict Handling:** Detection and reporting (no automatic resolution)
- **GUI Framework:** Tkinter (cross-platform)
- **Dependencies:** Python Standard Library only

---

## Built-in Examples

1. **Simple Expression** - Classic operator precedence grammar
2. **Ambiguous Arithmetic** - Demonstrates shift-reduce conflicts
3. **Balanced Parentheses** - Grammar with epsilon production
4. **If-Then-Else** - Classic dangling else problem
5. **LR(1) vs SLR(1)** - Grammar that requires LR(1) power

---

## Contributing

Contributions are welcome! Areas for enhancement:
- [ ] Export parsing tables to various formats
- [ ] Additional grammar transformations (left factoring, left recursion elimination)
- [ ] LALR(1) parser generation
- [ ] Save/load grammar files
- [ ] Dark mode UI theme
- [ ] Parse tree visualization

---

## References

1. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2nd ed.). Pearson.
2. Knuth, D. E. (1965). On the translation of languages from left to right. *Information and Control*, 8(6), 607-639.
3. DeRemer, F. L. (1969). *Practical Translators for LR(k) Languages*. MIT PhD Thesis.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Dragon Book authors for the definitive parsing algorithms
- The Python and Tkinter communities
- Compiler construction educators worldwide

---

<p align="center">
  <b>CLR Parser Studio</b> - Making Canonical LR(1) Parsing Accessible
  <br>
  <i>Built for learning, designed for understanding</i>
</p>
