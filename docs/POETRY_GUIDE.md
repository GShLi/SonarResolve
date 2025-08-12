# Poetry Installation and Usage Guide

## Installation

### Install Poetry
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Or using pip
pip install poetry
```

### Verify Installation
```bash
poetry --version
```

## Project Setup

### Initialize Project (if starting fresh)
```bash
poetry init
```

### Install Dependencies
```bash
# Install all dependencies
poetry install

# Install only production dependencies
poetry install --no-dev

# Install with specific groups
poetry install --with dev
```

## Dependency Management

### Add Dependencies
```bash
# Add production dependency
poetry add requests

# Add development dependency
poetry add --group dev pytest

# Add from git repository
poetry add git+https://github.com/user/repo.git

# Add with version constraints
poetry add "requests>=2.25.0,<3.0.0"
```

### Remove Dependencies
```bash
poetry remove requests
poetry remove --group dev pytest
```

### Update Dependencies
```bash
# Update all dependencies
poetry update

# Update specific package
poetry update requests

# Show outdated packages
poetry show --outdated
```

## Virtual Environment

### Activate Virtual Environment
```bash
poetry shell
```

### Run Commands in Virtual Environment
```bash
# Run Python script
poetry run python main.py

# Run custom scripts (defined in pyproject.toml)
poetry run sonar-jira
poetry run sonar-autofix
poetry run sonar-test
```

### Environment Information
```bash
# Show virtual environment path
poetry env info

# List environments
poetry env list

# Remove environment
poetry env remove python
```

## Development Workflow

### Code Quality Tools
```bash
# Format code with black
poetry run black .

# Sort imports with isort
poetry run isort .

# Lint with flake8
poetry run flake8 .

# Type checking with mypy
poetry run mypy .
```

### Testing
```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_sonarqube.py

# Run tests with markers
poetry run pytest -m "not slow"
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run pre-commit on all files
poetry run pre-commit run --all-files
```

## Building and Publishing

### Build Package
```bash
poetry build
```

### Publish to PyPI
```bash
# Configure PyPI credentials
poetry config pypi-token.pypi your-token

# Publish
poetry publish
```

### Export Requirements
```bash
# Export requirements.txt
poetry export -f requirements.txt --output requirements.txt

# Export with dev dependencies
poetry export -f requirements.txt --output requirements-dev.txt --with dev
```

## Configuration

### Configure Poetry Settings
```bash
# Set virtual environment to be created in project directory
poetry config virtualenvs.in-project true

# Show configuration
poetry config --list

# Set PyPI repository
poetry config repositories.testpypi https://test.pypi.org/legacy/
```

## Useful Commands

### Project Information
```bash
# Show project information
poetry show

# Show dependency tree
poetry show --tree

# Show specific package info
poetry show requests

# Check for security vulnerabilities
poetry audit
```

### Cache Management
```bash
# Clear cache
poetry cache clear pypi --all

# Show cache info
poetry cache list
```
