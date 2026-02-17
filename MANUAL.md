# 📘 LOS User Manual v3.3.1

**Linear Optimization Specification (LOS)** is a domain-specific language for modeling mathematical optimization problems.

This manual serves as the definitive reference for the LOS language syntax and Python API.

---

## 1. Syntax Overview

**Important Rules:**
1.  **Lowercase Keywords**: LOS is strictly case-sensitive. Keywords like `set`, `var`, `minimize` must be lowercase.
2.  **Comments**: Use `#` for comments.
3.  **Blocks**: Indentation is not significant, but recommended for readability. Blocks (like constraints) use colons `:`.

---

## 2. Model Structure

A valid LOS model consists of declarations in roughly this order:

1.  **Imports** (Data Sources)
2.  **Sets** (Indices)
3.  **Parameters** (Data)
4.  **Variables** (Decisions)
5.  **Objective** (Goal)
6.  **Constraints** (Rules)

### 2.1 Imports (The Power Way)

Instead of passing data via Python, **import it directly**.

```los
import "data/products.csv"
import "data/factories.csv"
```

The compiler will read the CSVs and make their columns available for Sets and Parameters.

### 2.2 Sets

Sets define the dimensions of your problem.

**Syntax:**
```los
# 1. Native Import (Recommended)
# Automatically populated from the 'Products' column in any imported CSV.
set Products

# 2. Simple set literal
set Colors = {"Red", "Green", "Blue"}

# 3. Range set (inclusive)
set Time = 1..12
```

### 2.3 Parameters

Parameters hold the constant data values.

**Syntax:**
```los
# 1. Native Import (Recommended)
# Automatically populated from the 'Cost' column in any imported CSV.
# Must declare index [Products] to validate size.
param Cost[Products]

# 2. Scalar parameter
param MaxTotalCost = 1000

# 3. Multi-index parameter (Matrix)
# "Distance from Factories to Customers"
param Distance[Factories, Customers]
```

### 2.4 Variables

Variables are the decisions the solver will make.

**Syntax:**
```los
# Continuous variable (default) with bounds
var qty[Products] >= 0

# Binary variable (0 or 1)
var is_active[Factories] bin

# Integer variable
var workers[Time] int >= 0
```

### 2.5 Objective Function

The goal to minimize or maximize. Note that the objective **does not have a name**.

**Syntax:**
```los
# Minimize cost
# Use iterators (p) inside the expression to reference indices
minimize:
    sum(qty[p] * Cost[p] for p in Products)
```

### 2.6 Constraints

Rules that must be satisfied. Constraints are grouped in a `subject to:` (or `st:`) block.

**Syntax:**
```los
subject to:
    # 1. Simple constraint
    total_limit: sum(qty[p] for p in Products) <= 1000

    # 2. For-each constraint (indexed constraint)
    # "For each factory f, production <= capacity"
    capacity_limit:
        sum(qty[p, f] for p in Products) <= Capacity[f]
        for f in Factories
```

---

## 3. Python API Integration

### 3.1 Basic Usage

```python
import los

# 1. Run model (data is loaded from imports inside .los)
result = los.solve("model.los")

# 2. Inspect
if result.is_optimal:
    print(f"Objective: {result.objective}")
    print(result.get_variable("qty", as_df=True))
```

### 3.2 Advanced: Manual Data Binding

If you are building a web app or generating data on the fly in Python, you can inject DataFrames manually. This overrides imported data.

```python
import los
import pandas as pd

# DataFrames
df_data = pd.DataFrame({'Products': ['A', 'B'], 'Cost': [10, 20]})

# Inject 'Products' Set and 'Cost' Param from this DataFrame
result = los.solve("model.los", data={'Products': df_data})
```

---

## 4. Security

LOS runs generated code in a **Sandboxed Environment**.
*   **Blocked**: `open`, `__import__`, `eval`, `exec`.
*   **Allowed**: Math functions, `pulp`, `pandas`, `numpy`.

See [SECURITY.md](./SECURITY.md) for details.

---

## 5. Troubleshooting Common Errors

### `ParseError: Unexpected token ...`
*   **Check Case**: Did you write `SET` instead of `set`?
*   **Check Brackets**: Sets use `{}`, Lists/Indices use `[]`.

### `KeyError: 'X'`
*   **Check Data**: A Param `X` was declared but not found in any imported CSV or provided DataFrame. Column names must match exactly.
