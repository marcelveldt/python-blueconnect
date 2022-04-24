"""Setup module for blueconnect."""
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
VERSION = "1.0.3"


setup(
    name="blueconnect",
    version=VERSION,
    url="https://github.com/marcelveldt/python-blueconnect",
    download_url="https://github.com/marcelveldt/python-blueconnect",
    author="Marcel van der Veldt",
    author_email="m.vanderveldt@outlook.com",
    description="Unofficial API client for Blue Riiot/Blue Connect devices.",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["test.*", "test"]),
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
    ],
)
