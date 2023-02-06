#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

test_requirements = []

setup(
    author="Lucas Abreu",
    author_email='lucasabreu@me.com',
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
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='real_state_scrap',
    name='realstate_scrap',
    packages=find_packages(include=['realstate_scrap1', 'realstate_scrap.*']),
    install_requires=['pandas', 'urllib.request', 'bs4', 're', 'csv'],
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/LucasAbreu89/webscrap',
    version='0.1.0',
    zip_safe=False,
)
