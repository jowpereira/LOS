# Contributing to LOS

Thank you for your interest in contributing to LOS! This guide will help you get started.

## Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/jpereiramp/los-lang.git
cd los-lang

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Run tests
python run_tests.py
```

## How to Contribute

### Reporting Bugs
- Use [GitHub Issues](https://github.com/jpereiramp/los-lang/issues).
- Include a minimal `.los` model that reproduces the problem.
- Include the generated Python code (`model.code()`).

### Suggesting Features
- Open a [Discussion](https://github.com/jpereiramp/los-lang/discussions) first.
- Describe the use case, not just the solution.

### Submitting Code
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Write tests for your changes.
4. Ensure all tests pass (`python run_tests.py`).
5. Submit a Pull Request with a clear description.

## Code Style
- **Formatter**: `black` (120 chars per line).
- **Linter**: `flake8`.
- **Type hints**: Encouraged on all public APIs.

## Architecture Overview
```
los/
├── domain/         # Entities, value objects (pure logic, no deps)
├── application/    # Use cases, compiler pipeline
├── infrastructure/ # Parser (Lark), Translator (PuLP), Validators
├── adapters/       # CLI, File processor
└── shared/         # Logging, error hierarchy
```

The compiler pipeline is: **Parse → Bind Data → Translate → Execute**.

## Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `fix(parser): handle escaped quotes in strings`
- `feat(translator): add support for != operator`
- `docs: update README installation section`
- `test: add regression test for indexed variables`
