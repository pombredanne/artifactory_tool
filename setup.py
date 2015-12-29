#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "xmltodict",
    "requests",
    "click"
]

test_requirements = [
    # TODO: put package test requirements here
    "pytest"
]

setup(
    name='artifactory_tool',
    version='0.1.0',
    description="Artifactory Configurater and Maniuplator",
    long_description=readme + '\n\n' + history,
    author="Sean Abbott",
    author_email='sean.abbott@datarobot.com',
    url='https://github.com/sean-abbott/artifactory_tool',
    packages=[
        'artifactory_tool',
    ],
    package_dir={'artifactory_tool':
                 'artifactory_tool'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='artifactory_tool',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': ['artifactory_tool=artifactory_tool.cli:cli']
    }
)
