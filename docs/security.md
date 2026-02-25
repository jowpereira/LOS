# Security Policy

This document describes the security model and protections implemented in the LOS compiler.

## Threat Model

LOS works as a **transpiler**: it converts `.los` code (safe by design) into Python code (powerful and potentially dangerous).

The primary attack vector is **Code Injection (RCE)** through:
1. Malicious strings attempting to escape quotes in generated code.
2. Unauthorized function calls (e.g., `__import__('os')`) injected as expressions.

## Mitigations

### 1. Execution Sandbox (`los_model.py`)
All generated code runs inside a restricted `exec()` environment:
- **Builtins disabled**: `open`, `__import__`, `eval`, `exec`, and all dangerous builtins are blocked.
- **Strict whitelist**: Only math and optimization libraries are allowed: `pulp`, `pandas`, `numpy`, `math`.
- **Safe builtins**: Only `range`, `list`, `set`, `dict`, `tuple`, `len`, `sum`, `min`, `max`, `abs`, `round`, `sorted`, `enumerate`, `zip`, `int`, `float`, `str`, `bool`, `print`.

### 2. String Escaping (`pulp_translator.py`)
All string literals from the LOS model are processed with `repr()` during translation, ensuring that escape characters (`'`, `"`, `\`) are neutralized correctly.

### 3. Name Sanitization
All identifiers (variable names, set names, parameter names) are sanitized with `re.sub(r'[^a-zA-Z0-9_]', '', name)`, preventing any special characters from reaching the generated code.

## Limitations

- **Untrusted input**: Although the sandbox is hardened, **never execute LOS models from unknown or untrusted sources** without prior audit. New sandbox bypass techniques may emerge.
- **DoS (Denial of Service)**: Models can still consume excessive resources (CPU/RAM) with large loops or matrices. Use `time_limit` on the solver.

## Reporting Vulnerabilities

If you find a security flaw (e.g., sandbox bypass), please **DO NOT** open a public Issue.

Report confidentially to: **lethanconsultoria@gmail.com**
