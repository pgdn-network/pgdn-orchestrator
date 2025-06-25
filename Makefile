.PHONY: install test lint format clean build upload

# Development setup
install:
	pip install -e .[dev]
	pip install pre-commit
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=pgdn_orchestrator --cov-report=html

test-integration:
	pytest tests/test_integration.py -v -s

# Code quality
lint:
	flake8 pgdn_orchestrator/ tests/
	mypy pgdn_orchestrator/

format:
	black pgdn_orchestrator/ tests/ examples/
	isort pgdn_orchestrator/ tests/ examples/

# Build and distribution
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

build: clean
	python setup.py sdist bdist_wheel

upload: build
	twine upload dist/*

# Development helpers
demo:
	python examples/basic_usage.py

integration-demo:
	python examples/integration_workflow.py

# Docker support
docker-build:
	docker build -t pgdn-orchestrator .

docker-test:
	docker run --rm pgdn-orchestrator pytest

# Documentation
docs:
	cd docs && make html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Project structure for reference
project-structure:
	@echo "pgdn-orchestrator/"
	@echo "├── pgdn_orchestrator/"
	@echo "│   ├── __init__.py"
	@echo "│   ├── agent.py"
	@echo "│   ├── models.py"
	@echo "│   ├── prompts.py"
	@echo "│   ├── exceptions.py"
	@echo "│   ├── cli.py"
	@echo "│   ├── integration.py"
	@echo "│   └── config.py"
	@echo "├── tests/"
	@echo "│   ├── test_agent.py"
	@echo "│   ├── test_integration.py"
	@echo "│   └── test_cli.py"
	@echo "├── examples/"
	@echo "│   ├── basic_usage.py"
	@echo "│   ├── integration_workflow.py"
	@echo "│   └── config_examples/"
	@echo "│       └── orchestration.json"
	@echo "├── setup.py"
	@echo "├── README.md"
	@echo "├── Makefile"
	@echo "├── requirements.txt"
	@echo "└── pyproject.toml"
