# File Mapping Guide

This guide shows which artifact content goes into which file.

## ✅ Core Package Files (Ready to Copy)

### pgdn_orchestrator/__init__.py
- **Copy from**: `init_py` artifact

### pgdn_orchestrator/models.py  
- **Copy from**: `models_py` artifact

### pgdn_orchestrator/exceptions.py
- **Copy from**: `exceptions_py` artifact

### pgdn_orchestrator/prompts.py
- **Copy from**: `prompts_py` artifact

### pgdn_orchestrator/agent.py
- **Copy from**: `agent_py` artifact

### pgdn_orchestrator/config.py
- **Copy from**: `config_py` artifact

## ✅ Root Configuration Files (Ready to Copy)

### setup.py
- **Copy from**: `setup_py` artifact

### requirements.txt
- **Copy from**: `requirements_txt` artifact

### pyproject.toml
- **Copy from**: `pyproject_toml` artifact

### Makefile
- **Copy from**: `makefile` artifact

### .gitignore
- **Copy from**: `gitignore` artifact

### .env.example
- **Copy from**: `env_example` artifact

### LICENSE
- **Copy from**: `license` artifact

### FILE_MAPPING.md
- **Copy from**: `file_mapping_md` artifact (this file!)

## 🔄 Still Need Individual Artifacts

These files are in the larger artifacts and need to be extracted:

### pgdn_orchestrator/cli.py
- **From**: "pgdn-orchestrator: CLI Interface and Integration" artifact
- **Section**: `# pgdn_orchestrator/cli.py`

### pgdn_orchestrator/integration.py
- **From**: "pgdn-orchestrator: CLI Interface and Integration" artifact
- **Section**: `# pgdn_orchestrator/integration.py`

### README.md
- **From**: "pgdn-orchestrator: Documentation and Usage Guide" artifact (entire content)

## 📋 Additional Files to Create

Create these files manually:

### requirements-dev.txt
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
isort>=5.0.0
pre-commit>=3.0.0
twine>=4.0.0
```

### CHANGELOG.md
```
# Changelog

## [0.1.0] - 2025-06-24
### Added
- Initial release of pgdn-orchestrator
- AI-powered scan orchestration
- Progressive scan escalation (light → medium → ferocious)
- Protocol discovery automation
- Permission management
- pgdn integration
- CLI interface
```

## 🚀 Quick Setup Commands

After copying all files:

```bash
cd pgdn-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
make test

# Format code
make format

# Try the CLI
pgdn-orchestrate --help
```

## 📁 Final Project Structure

```
pgdn-orchestrator/
├── pgdn_orchestrator/
│   ├── __init__.py          ✅ Ready
│   ├── agent.py             ✅ Ready
│   ├── models.py            ✅ Ready
│   ├── prompts.py           ✅ Ready
│   ├── exceptions.py        ✅ Ready
│   ├── config.py            ✅ Ready
│   ├── cli.py               🔄 Extract from large artifact
│   └── integration.py       🔄 Extract from large artifact
├── tests/                   (empty files created by script)
├── examples/                (empty files created by script)
├── setup.py                 ✅ Ready
├── requirements.txt         ✅ Ready
├── pyproject.toml          ✅ Ready
├── Makefile                ✅ Ready
├── .gitignore              ✅ Ready
├── .env.example            ✅ Ready
├── LICENSE                 ✅ Ready
├── README.md               🔄 Extract from docs artifact
└── FILE_MAPPING.md         ✅ Ready (this file!)
```
