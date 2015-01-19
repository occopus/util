#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

from __future__ import absolute_import

"""
This module implements a configuration interface, with its main purpose
being the simple merging of statically configured and command line parameters.

The interface proxies ``add_argument`` and ``parse_args calls to the underlying
``argparse.ArgumentParser`` object.

Basically, this module provides an ``ArgumentParser`` that can be pre-filled
with statically defined data.
"""

__all__ = ['Config', 'DefaultConfig', 'DefaultYAMLConfig',
           'load_auth_data']

import yaml
import argparse
from ...util import cfg_file_path
import logging

class Config(object):
    """
    Loads and stores configuration based on command line arguments.

    .. todo:: ``add_argument`` should be exposed.
    """
    def __init__(self, **kwargs):
        self.__parser = argparse.ArgumentParser(**kwargs)

    def parse_args(self, args=None):
        self.__parser.parse_args(namespace=self, args=args)

    def __repr__(self):
        return yaml.dump(self.__dict__, default_flow_style=False)
    def __str__(self):
        # Return only the essential attributes by skipping self.__parser
        return yaml.dump(
                dict((k,v) for k,v in self.__dict__.iteritems()
                     if k != '_Config__parser'),
                default_flow_style=False)

class DefaultConfig(Config):
    """
    Stores configuration based on a default configuration, and command line
    arguments. This Config class uses the DefaultsHelpFormatter to render the
    help message.

    - First, the default configuration is loaded.
    - Then, the command line arguments are parsed to override configuration
      values if necessary.

    :param default_config: Dictionary containing defalt configuration. This
        object will be copied.
    :param kwargs: Keyword arguments to be passed to the underlying
        :py:class:`argparse.ArgumentParser` object.
    """
    def __init__(self, default_config, **kwargs):
        self.__dict__ = dict(default_config)
        kwargs.setdefault('formatter_class',
                          argparse.ArgumentDefaultsHelpFormatter)
        Config.__init__(self, **kwargs)

    def add_argument(self, name, *args, **kwargs):
        """
        Adds an argument to this parser, with default values set based on the
        default configuration.

        Uses the same syntax as :py:func:`argparse.ArgumentParser.add_argument`
        """
        basename = name[2:] if name.startswith('--') else name
        if hasattr(self, basename):
            kwargs.setdefault('default', getattr(self, basename))
        self._Config__parser.add_argument(name, *args, **kwargs)

class DefaultYAMLConfig(DefaultConfig):
    """
    This class works the same way as :class:`.DefaultConfig`.
    It loads the default configuration from a YAML configuration file.
    """
    def __init__(self, config_string, **kwargs):
        DefaultConfig.__init__(self, yaml.load(config_string), **kwargs)

def load_auth_data(auth_data):
    """
    Load authentication data from safe source.

    :param auth_data: Contains the information necessary to construct the data.
    :returns: The resolved authentication data.
    :raises NotImplementedError: if the type of ``auth_data`` cannot be handled.

    Example use in YAML follows. This function will be called with
    ``auth_data='file://auth_data.yaml'``. This will be interpreted as a path
    to a YAML file (either absolute, relative to ``(system prefix)/etc/occo``).
    The file will be loaded, and ``cloud_handler['auth_data']`` will be
    replaced with its content.

    .. code-block:: yaml
        :emphasize-lines: 8,9

        cloud_handler: !CloudHandler
            protocol: boto
            name: LPDS
            dry_run: false
            target:
                endpoint: http://cfe2.lpds.sztaki.hu:4567
                regionname: ROOT
            auth_data: !!python/object/apply:occo.util.config.load_auth_data
                - file://auth_data.yaml

    The result will be something like:

    .. code-block:: yaml
        :emphasize-lines: 9,10

        cloud_handler: !CloudHandler
            protocol: boto
            name: LPDS
            dry_run: false
            target:
                endpoint: http://cfe2.lpds.sztaki.hu:4567
                regionname: ROOT
            auth_data:
                access_key: username
                secret_key: the_data_we_wanted_to_avoid_being_commited_into_git

    Currently, the only input format supported is a string berginning with
    ``'file://'``. Absolute paths must start with ``'/'``, that is:
    ``'file:///'``

    .. todo:: This algorithm is more generic. It can be used to implement
        general importing in YAML.
    """
    log = logging.getLogger('occo.util')
    if auth_data is None:
        log.warning(
            'Tried to resolve auth_data, but there is no such attribute')
        return
    if type(auth_data) is str:
        if auth_data.startswith('file://'):
            filename = cfg_file_path(auth_data[7:])
            log.debug("Loading authentication form '%s'", filename)
            with open(filename) as f:
                return yaml.load(f)
    raise NotImplementedError('Unknown auth_data format', auth_data)
