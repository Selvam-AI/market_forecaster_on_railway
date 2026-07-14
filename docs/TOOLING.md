# Project Tooling

This file records local tools and editor extensions used for the Geopolitical Market Forecaster project.

## System Tools

- `python3.12-venv`: creates isolated Python virtual environments for the backend.
- `python3-pip`: installs Python dependencies from `requirements.txt` or `pyproject.toml`.

## VS Code Extensions

- Python by Microsoft: Python language support, interpreter selection, debugging, and test integration.
- Pylance: faster Python IntelliSense, type checking, and code navigation.
- Ruff: linting and formatting support for Python code quality.
- SQLite Viewer: inspect local SQLite database files created by the prototype.

## Optional VS Code Extensions

- GitLens: richer Git history and blame views. Optional because built-in VS Code Git is enough for this project.
- REST Client: quick API endpoint testing from `.http` files. Optional because `curl`, browser docs, or Thunder Client can cover the same need.
- Thunder Client: GUI API testing inside VS Code. Optional alternative to REST Client.
- Prettier: optional formatting for dashboard HTML, CSS, and JavaScript if the frontend grows.
- ESLint: optional linting if dashboard JavaScript becomes more complex.

## Not Added Yet

- CrewAI: not used in the current implementation. The application uses plain Python agent classes coordinated by the local `ForecastPipeline`.
