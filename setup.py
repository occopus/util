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

setuptools.setup(
    name='OCCO-Util',
    version='1.10',
    author='SZTAKI',
    author_email='occopus@lpds.sztaki.hu',
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
    url='https://github.com/occopus',
    license='LICENSE.txt',
    description='Occopus Utility Modules',
    long_description=open('README.txt').read(),
    install_requires=[
        'argparse',
        'dateutils',
        'pika',
        'python-dateutil',
        'pytz',
        'ruamel.yaml',
        'six',
        'requests',
    ],
)
