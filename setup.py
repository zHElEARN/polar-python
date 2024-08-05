from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="polar-python",
    version="0.0.3",
    packages=find_packages(),
    install_requires=["bleak"],
    author="Zhe_Learn",
    author_email="personal@zhelearn.com",
    description=(
        "polar-python is a Python library for connecting to Polar devices via Bluetooth Low Energy (BLE) "
        "using Bleak. It allows querying device capabilities (e.g., ECG, ACC, PPG), exploring configurable options, "
        "and streaming parsed data through callback functions."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zHElEARN/polar-python",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
)
