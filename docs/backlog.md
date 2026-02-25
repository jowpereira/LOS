# 📋 LOS Roadmap & Backlog

**Language for Optimization Specification (LOS)** project roadmap. This document outlines the planned features, optimizations, and community goals for future releases.

---

## 1. Core & Parser Improvements

*   **Matrix-Based Expansion**: Direct generation of CSR/CSC sparse matrices to bypass PuLP's object-heavy instantiation for large-scale models.
*   **Syntax Error Precision**: Improve `Lark` transformer to provide line/column numbers and "Did you mean?" suggestions for identifier typos.
*   **Internal Data Structures**: Refactor AST representation for faster data binding during large-scale model expansion.
*   **Robust String Support**: Enable usage of strings as parameters and indexed keys beyond basic labels.

---

## 2. Solvers & Backends

*   **Pyomo Support**: Implement `PyomoTranslator` to enable Non-Linear Programming (NLP) and a wider range of academic solvers.
*   **Gurobi Direct Adapter**: Implement a specialized adapter for Gurobi to leverage its C-API performance without intermediate Python overhead.
*   **SciPy/NumPy Integration**: Support for small-scale standard problems without external system dependencies.

---

## 3. Tooling & Ecosystem

*   **VS Code Extension**: Dedicated extension for `.los` files including syntax highlighting, bracket matching, and basic autocompletion.
*   **LOS CLI v2**: Enhancing the command-line interface to support batch processing, report generation, and direct CSV exporting.
*   **Interactive Sandbox**: Web-based LOS compiler (via Pyodide) for the project website.

---

## 4. Documentation & Research

*   **Expansion Benchmarks**: Automated performance testing suite against AMPL, GAMS, and Pyomo.
*   **Real-World Case Studies**: Industry-standard examples for Supply Chain, Route Optimization, and Production Planning.
*   **Mathematical Proofs**: Formal documentation of the LOS-to-MILP translation and mapping logic.

---

## 5. Stability & Maintenance

*   **Type Hinting**: Achieve full Mypy compliance across the core codebase (`los/`).
*   **Multi-OS CI**: GitHub Actions matrix for automated testing on Windows, Linux, and macOS.
*   **Standard Library Tests**: Comprehensive test suite for mathematical function correctness (`sum`, `log`, `min`, `max`).

---

> [!TIP]
> Features are prioritized based on community feedback. Feel free to open an Issue or a Discussion on GitHub!
