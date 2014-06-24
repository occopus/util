#!/usr/bin/env -e python

import setuptools
from pip.req import parse_requirements

reqs = [ str(i.req) for i in parse_requirements('requirements.txt') ]

setuptools.setup(
    name='OCCO-Util',
    version='0.1.0',
    author='Adam Visegradi',
    author_email='adam.visegradi@sztaki.mta.hu',
    packages=['occo.util', 'occo.util.config'],
#    scripts=['bin/stowe-towels.py','bin/wash-towels.py'],
    url='http://www.lpds.sztaki.hu/',
    license='LICENSE.txt',
    description='OCCO Utility Modules',
    long_description=open('README.txt').read(),
    install_requires=reqs,
)