# LOS (Linear Optimization Specification)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Security: Hardened](https://img.shields.io/badge/Security-Hardened-green.svg)](./SECURITY.md)

**LOS** is a professional Domain-Specific Language (DSL) for mathematical optimization. It decouples the *business logic* of your problem from the *solver implementation*, allowing you to write clean, maintainable, and mathematically robust models.

> **"Write Math, Run Python."**

---

## 🚀 Why LOS?

*   **Readable**: Syntax designed to look like a whiteboard math model, not a script.
*   **Separation of Concerns**: Keep your model logic separate from your data pipeline.
*   **Data-Driven**: **Native support for CSV imports.** Bind data directly in your model.
*   **Secure**: Sandboxed execution environment prevents code injection vulnerabilities.
*   **Solver Agnostic**: Powered by [PuLP](https://coin-or.github.io/pulp/), supporting CBC, GLPK, Gurobi, CPLEX.

---

## 💡 The "Power Way": Native Imports

Don't clutter your Python scripts with data loading logic. Let LOS handle it.

**`production.los`**
```los
# 1. Import Data
# Automatically extracts columns matching Set/Param names.
import "products.csv"
import "factories.csv"

# 2. Sets (Populated from CSVs)
set Products
set Factories

# 3. Parameters (Populated from CSVs)
# Extracts 'Cost' column from products.csv (since 'Products' is there)
param Cost[Products]
# Extracts 'Capacity' column from factories.csv
param Capacity[Factories]

# 4. Variables
var qty[Products, Factories] >= 0

# 5. Objective
minimize: 
    sum(qty[p,f] * Cost[p] for p in Products, f in Factories)

# 6. Constraints
subject to:
    limit: 
        sum(qty[p,f] for p in Products) <= Capacity[f]
        for f in Factories
```

---

## ⚡ Quick Start

### 1. Model (`production.los`)
Save the code above.

### 2. Data (`products.csv`, `factories.csv`)
Save your data files in the same folder.

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

### 3. Run (`solve.py`)
No panda-wrangling required.

```python
import los

# Compile, bind data, and solve in one go.
result = los.solve("production.los")

if result.is_optimal:
    print(f"Optimal Cost: {result.objective}")
    print(result.get_variable("qty", as_df=True))
```

---

## 📚 Documentation

*   **[User Manual](./MANUAL.md)**: Full syntax reference and advanced features.
*   **[Security Policy](./SECURITY.md)**: Details on the sandbox and secure usage.

---

## 📄 License

This project is licensed under the **MIT License**.
