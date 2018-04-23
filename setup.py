#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import os
import sys
from os import path
from setuptools import find_packages, setup
from distutils.command.bdist import bdist
from distutils.command.sdist import sdist


version = '0.5.0rc1'


def check_versions():
    print('versions checked')
    try:
        curpath = path.abspath(path.realpath(os.getcwd()))
        setuppath = path.abspath(path.realpath(path.split(__file__)[0]))

        if curpath != setuppath:
            sys.path.append(setuppath)
        import iirrational

        modfile = path.abspath(path.realpath(path.split(iirrational.__file__)[0]))
        mod_relpath = path.relpath(modfile, setuppath)
        if mod_relpath == 'iirrational':
            if iirrational.__version__ != version:
                print("WARNING: Stated module version different than setup.py version", file = sys.stderr)
                print("         '{0}' != '{1}'".format(iirrational.__version__, version), file = sys.stderr)
                print("Fix version.py and setup.py for consistency")

        import subprocess
        try:
            git_tag = subprocess.check_output(['git', 'describe', '--tags'])
            git_tag = git_tag.strip()
            git_tag = str(git_tag)
        except subprocess.CalledProcessError:
            pass
        else:
            if git_tag != version:
                if git_tag.startswith(version):
                    print("WARNING: latex git-tag has commits since versioning", file = sys.stderr)
                    print("         '{0}' ---> '{1}'".format(version, git_tag), file=sys.stderr)
                else:
                    print("WARNING: latex git-tag different than setup.py version", file = sys.stderr)
                    print("         '{0}' != '{1}'".format(version, git_tag), file=sys.stderr)
                print("         Perhaps update versions in setup.py and iirrational.version, git commit, then git tag")
                print("         otherwise fix tag if not yet git pushed to remote (see DISTRIBUTION-README.md)")

    except ImportError:
        pass


cmdclass = dict()

class check_bdist(bdist):
    def run(self):
        bdist.run(self)
        check_versions()

class check_sdist(sdist):
    def run(self):
        sdist.run(self)
        check_versions()

cmdclass['bdist'] = check_bdist
cmdclass['sdist'] = check_sdist

try:
    from wheel.bdist_wheel import bdist_wheel
    class check_bdist_wheel(bdist_wheel):
        def run(self):
            bdist_wheel.run(self)
            check_versions()
    cmdclass['bdist_wheel'] = check_bdist_wheel
except ImportError:
    pass


setup_args = dict(
    name             = 'cas9epics',
    version          = version,
    url              = 'https://github.com/mccullerlp/cas9epics',
    author           = 'Lee McCuller',
    author_email     = 'Lee.McCuller@gmail.com',
    description      = "Easy hierarchical generation and host of EPICS control system variables",
    license          = 'Copyright 2017 Lee McCuller',
    install_requires = [
        'declarative',
        'numpy',
        'pcaspy',
        'epics',
    ],
    packages = find_packages(
        exclude = ['docs'],
    ),
    include_package_data = True,
    zip_safe = False,
    keywords = 'EPICS, EZCA, controls, instrumentation, rs232, GPIB',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

if __name__ == "__main__":
    setup(
        cmdclass = cmdclass,
        **setup_args
    )
