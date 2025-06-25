from setuptools import setup, find_packages

setup(
    name="pgdn-orchestrator",
    version="0.1.0",
    description="Intelligent scan orchestration for DePIN validator networks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DePIN Security Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.21.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.0.0",
        "pgdn",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "pgdn-orchestrate=pgdn_orchestrator.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
