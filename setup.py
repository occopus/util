### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.
#!/usr/bin/env -e python

import setuptools
from pip.req import parse_requirements

setuptools.setup(
    name='OCCO-Util',
    version='0.1.0',
    author='Adam Visegradi',
    author_email='adam.visegradi@sztaki.mta.hu',
    namespace_packages=[
        'occo',
    ],
    packages=[
        'occo.util',
        'occo.util.config',
        'occo.util.communication',
        'occo.util.factory',
        'occo.exceptions',
        'occo.constants',
    ],
    url='http://www.lpds.sztaki.hu/',
    license='LICENSE.txt',
    description='OCCO Utility Modules',
    long_description=open('README.txt').read(),
    install_requires=[
        'argparse',
        'dateutils',
        'pika',
        'python-dateutil',
        'pytz',
        'PyYAML',
        'six',
        'wsgiref',
        'requests',
    ],
)
