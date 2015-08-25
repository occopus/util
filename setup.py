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
