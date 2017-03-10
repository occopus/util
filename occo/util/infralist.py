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

"""
Primitives for managing list of infra identifiers 
"""

import os
from ruamel import yaml

#log = logging.getLogger('occo.util.infralist')

class Infralist(object):
    def __init__(self,storefile=None):
        if not storefile:
            storefile = os.path.join(os.path.expanduser('~'),'.occopus/infralist.yaml')
        self.storefile = storefile

    def store(self,infralist):
        dirname = os.path.dirname(self.storefile)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.storefile, 'w') as yaml_file:
            yaml_file.write( 
                yaml.dump( infralist, default_flow_style=False))

    def retrieve(self):
        if os.path.isfile(self.storefile):
            with open(self.storefile, 'r') as stream:
                try:
                    infralist = list(yaml.load(stream,Loader=yaml.Loader))
                except yaml.YAMLError as exc:
                    print(exc)
        else:
            infralist = list()
        return infralist

    def add(self,infraid):
        infralist = self.retrieve()
        infralist.append(infraid)
        self.store(infralist)

    def remove(self,infraid):
        infralist = self.retrieve()
        infralist.remove(infraid)
        self.store(infralist)

    def get(self):
        return self.retrieve()

    def path(self):
        return self.storefile

