"""
Setup script for the e24.no crawler package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="e24-crawler",
    version="0.1.0",
    author="OSINT Comments Team",
    author_email="your.email@example.com",
    description="A web crawler for e24.no that identifies articles with comments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/e24-crawler",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "e24-crawler=crawler.cli:main",
        ],
    },
)
