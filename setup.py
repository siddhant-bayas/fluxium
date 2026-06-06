from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="fluxium",
    version="1.0.0",
    author="Siddhant Bayas",
    description="A fast, modern HTTP client for Python",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx[http2]>=0.27.0",
        "idna>=3.4",
        "chardet>=5.0",
        "brotli>=1.1.0",
    ],
    extras_require={
        "socks": ["httpx-socks>=0.7"],
        "all": ["httpx-socks>=0.7"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
