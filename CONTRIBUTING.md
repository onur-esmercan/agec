# Contributing to AGEC

Thank you for your interest in contributing! This document covers everything
you need to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/onur-esmercan/agec.git
cd agec

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# All tests with verbose output
pytest

# With coverage report
pytest --cov=agec --cov-report=term-missing
```

Coverage must stay at or above **80%** (enforced in `pyproject.toml`).

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- All public classes and methods must have docstrings.
- Type annotations are required for all function signatures.

## Pull Request Guidelines

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new behaviour — aim for full branch coverage.
3. Update `CHANGELOG.md` under `[Unreleased]` with a concise entry.
4. Keep commits atomic and descriptive.
5. Open a pull request and fill in the PR template.

## Reporting Issues

Please use the [GitHub issue tracker](https://github.com/onur-esmercan/agec/issues).
Include a minimal reproducible example where possible.

## License

By contributing you agree that your contributions will be licensed under the
[Apache-2.0](LICENSE) license.
