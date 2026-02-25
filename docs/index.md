# LOS — Language for Optimization Specification

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Security: Hardened](https://img.shields.io/badge/security-hardened-green.svg)](security.md)

**LOS** is a **Language for Optimization Specification**. It compiles human-readable model definitions into executable Python code (currently using **PuLP** as the primary engine), keeping your business logic clean and your data pipeline separate.

> **"Write Math, Run Python."**

---

## Installation

```bash
pip install los-lang
```

Or install from source:
```bash
git clone https://github.com/jowpereira/los.git
cd los
pip install -e .
```

---

## Quick Start

### 1. Write a Model (`production.los`)
```los
import "products.csv"
import "factories.csv"

set Products
set Factories

param Cost[Products]
param Capacity[Factories]

var qty[Products, Factories] >= 0

minimize:
    sum(qty[p,f] * Cost[p] for p in Products, f in Factories)

subject to:
    capacity_limit:
        sum(qty[p,f] for p in Products) <= Capacity[f]
        for f in Factories
```

### 2. Prepare Data
**`products.csv`**
```csv
Products,Cost
WidgetA,10
WidgetB,15
```

**`factories.csv`**
```csv
Factories,Capacity
Factory1,1000
Factory2,2000
```

### 3. Solve (`solve.py`)
```python
import los

result = los.solve("production.los")

if result.is_optimal:
    print(f"Optimal Cost: {result.objective}")
    print(result.get_variable("qty", as_df=True))
```

---

## Why LOS?

| Feature | LOS | Raw PuLP/Pyomo |
|---|---|---|
| **Readability** | Whiteboard-like syntax | Python boilerplate |
| **Data Binding** | Native CSV imports | Manual DataFrame wrangling |
| **Security** | Sandboxed execution | Full Python access |
| **Debug** | Inspect generated code (`model.code()` or `model.export_python()`) | Black box |
| **Solver** | CBC, GLPK, Gurobi, CPLEX (via PuLP) | Same |
| **Backends** | PuLP (Pyomo planned) | N/A |

---

## Advanced: Manual Data Binding

For dynamic data (APIs, databases), inject DataFrames directly:

```python
import los
import pandas as pd

df = pd.DataFrame({"Products": ["A", "B"], "Cost": [10, 20]})

result = los.solve("model.los", data={"Products": df})
```

---

## Documentation

| Document | Description |
|---|---|
| [User Manual](manual.md) | Full syntax reference and API guide |
| [Security Policy](security.md) | Sandbox details and threat model |
| [Changelog](changelog.md) | Version history |
| [Backlog](backlog.md) | Roadmap and future features |
| [Contributing](contributing.md) | How to contribute |

---

## License

[MIT](./LICENSE) © Jonathan Pereira
