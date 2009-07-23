# -*- coding: utf-8 -*-
#
# Copyright 2009 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Setup script."""

from ez_setup import use_setuptools
use_setuptools()

import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(*rnames)).read()


setup(
    name='twistedae',
    version='0.1.0a1',
    author="Tobias Rodaebel",
    author_email="tobias dot rodaebel at googlemail dot com",
    description="Google App Engine on Twisted.",
    long_description=(
        read('README.txt')
        + '\n\n' +
        read('TODO.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license="Apache License 2.0",
    keywords="gae appengine twisted wsgi",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        ],
    url='',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    install_requires=[
        'Twisted',
        'setuptools',
        ],
    entry_points={
        'console_scripts': ['appserver = twistedae.appserver:main'],
        'paste.app_factory': ['main = twistedae.appserver:app_factory'],
        # TODO: We'll see if we want to use paste
    },
    zip_safe=False,
    )
