#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup

__version__ = '1.1.0'
readme = open('README.rst').read()


def which(program):
    """
    Detect whether or not a vcs program is installed.
    Thanks to http://stackoverflow.com/a/377028/70191
    """

    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


EDITABLE_REQUIREMENT = re.compile(
    r'^(-e )?(?P<link>(?P<vcs>git|svn|hg|bzr).+#egg=(?P<package>.+)-(?P<version>\d+(?:\.\d+)*))(?P<extras>\[.+\])?$')


def parse_requirements(fname, installs, dependencies):
    with open(fname) as f:
        for line in f.readlines():
            requirement = line.strip('\n')
            if not requirement or 'requirement' in requirement:
                continue
            match = EDITABLE_REQUIREMENT.match(requirement)
            if match:
                if not which(match.group('vcs')):
                    raise AssertionError(
                        "'%(vcs)s' must be installed in order to install" +
                        " %(link)s" % match.groupdict())
                installs.append(
                    "%(package)s==%(version)s" % match.groupdict())
                dependencies.append(match.group('link'))
            else:
                installs.append(requirement)


install_requires = []
develop_requires = []
prod_requires = []
dependency_links = []

parse_requirements('requirements.txt', install_requires, dependency_links)
#parse_requirements('requirements_prod.txt', prod_requires, dependency_links)
#parse_requirements('requirements_dev.txt', develop_requires, dependency_links)
#prod_requires.extend(install_requires)
#develop_requires.extend(install_requires)

setup(
    name='natural-language-understanding',
    version=__version__,
    long_description=readme,
    author='knowledgefusion',
    author_email='admin@knowledge-fusion.science',
    packages=[
        'app',
    ],
    dependency_links=dependency_links,
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'develop': develop_requires,
        'production': prod_requires,
    },
    entry_points={

    },
)
