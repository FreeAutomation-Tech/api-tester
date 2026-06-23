from setuptools import setup, find_packages

setup(
    name="api-tester",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.28",
    ],
    extras_require={
        "ai": ["openai>=1.0", "anthropic>=0.30"],
    },
    entry_points={
        "console_scripts": [
            "api-tester=src.cli:main",
        ],
    },
)
