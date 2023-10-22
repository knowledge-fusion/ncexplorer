#!/usr/bin/env python


from setuptools import setup

__version__ = "1.1.0"
readme = open("README.md").read()


install_requires = []
develop_requires = []
prod_requires = []
dependency_links = []


setup(
    name="natural-language-understanding",
    version=__version__,
    long_description=readme,
    author="ncexplorer",
    author_email="admin@knowledge-fusion.science",
    packages=[
        "app",
    ],
    dependency_links=dependency_links,
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        "develop": develop_requires,
        "production": prod_requires,
    },
    entry_points={},
)
