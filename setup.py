from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import bluefloodserver

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--twisted']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='graphite-blueflood',
    version="0.0.1",
    url='https://github.com/rampage644/graphite-http-wrapper',
    license='Apache Software License',
    author='Sergei Turukin',
    tests_require=['pytest', 'mock', 'twisted', 'pytest-twisted'],
    install_requires=['twisted', 'txKeystone'],
    cmdclass={'test': PyTest},
    author_email='sergei.turukin@rackspace.com',
    description='Sending graphite metrics to blueflood',
    long_description=long_description,
    packages=['bluefloodserver'],
    include_package_data=True,
    platforms='any',
    test_suite='tests.test_bluefloodserver.py',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    extras_require={
        'testing': ['pytest'],
    }
)