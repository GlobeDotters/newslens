from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="newslens",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "feedparser>=6.0.0",
        "pycountry>=20.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "flake8>=3.9.0",
            "mypy>=0.812",
            "isort>=5.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "newslens=newslens.cli.main:cli",
        ],
    },
    python_requires=">=3.7",
    author="Ivan Todorov",
    author_email="your.email@example.com",
    description="A CLI tool for analyzing news bias and detecting blindspots in coverage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/newslens",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: News/RSS",
        "Topic :: Utilities",
    ],
    package_data={
        "newslens": ["data/defaults/*.json"],
    },
)
