from setuptools import setup, find_packages

setup(name="polar-python",
      version="0.0.1",
      packages=find_packages(),
      install_requires=["bleak"],
      author="Zhe_Learn",
      author_email="personal@zhelearn.comm",
      description="polar-python is a Python library for connecting to Polar devices via Bluetooth Low Energy (BLE) using Bleak. It allows querying device capabilities (e.g., ECG, ACC, PPG), exploring configurable options, and streaming parsed data through callback functions.")
