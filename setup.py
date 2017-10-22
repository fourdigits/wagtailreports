#!/usr/bin/env python

import sys

from wagtail import __version__
from wagtail.utils.setup import assets, sdist, check_bdist_egg

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


# Hack to prevent "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when setup.py exits
# (see http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing
except ImportError:
    pass

install_requires = [
   "wagtail>=1.4.0",
   "Django>=1.7.1",
]

# Testing dependencies
testing_extras = [
    # # Required for running the tests
    # 'mock>=1.0.0',
    # 'python-dateutil>=2.2',
    # 'pytz>=2014.7',
    # 'Pillow>=2.7.0',
    # 'elasticsearch>=1.0.0,<3.0',
    # 'Jinja2>=2.8,<3.0',
    # 'boto3>=1.4,<1.5',
    # 'freezegun>=0.3.8',
    #
    # # For coverage and PEP8 linting
    # 'coverage>=3.7.0',
    # 'flake8>=2.2.0',
    # 'isort==4.2.5',
    # 'flake8-blind-except==0.1.1',
    # 'flake8-print==2.0.2',
]

# Documentation dependencies
documentation_extras = [
    # 'pyenchant==1.6.8',
    # 'sphinxcontrib-spelling>=2.3.0',
    # 'Sphinx>=1.5.2',
    # 'sphinx-autobuild>=0.6.0',
    # 'sphinx_rtd_theme>=0.1.9',
]

setup(
    name='wagtailreports',
    version=__version__,
    description='A Wagtail CMS package for reports and report panels',
    author='Coen van der Kamp',
    author_email='coen@fourdigits.nl',
    url='',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
        'docs': documentation_extras
    },
    entry_points="""
            [console_scripts]
            wagtailreports=wagtail.bin.wagtail:main
    """,
    zip_safe=False,
    cmdclass={
        'sdist': sdist,
        'bdist_egg': check_bdist_egg,
        'assets': assets,
    },
)