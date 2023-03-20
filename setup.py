from setuptools import setup, find_packages
import os

setup(
    author="Lucas Abreu",
    author_email='lag.programmer@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="extract all the data like: price, address, features from imovelweb.com.br",
    include_package_data=True,
    name='real2scrap',
    packages=find_packages(),
    version='0.2.1',
)
