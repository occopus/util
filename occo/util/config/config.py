#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

"""
This module implements a configuration interface, with its main purpose
being the simple merging of istatically configured and command line parameters.
"""

__all__ = ['Config', 'DefaultConfig', 'DefaultYAMLConfig']

import yaml
import argparse

class Config(object):
    """
    Loads and stores configuration based on command line arguments.
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
    Stores configuration based on a default configuration,
    and command line arguments. This Config class uses the
    DefaultsHelpFormatter to render the help message.

    - First, the default configuration is loaded.
    - Then, the command line arguments are parsed to override
      configuration values if necessary.
    """
    def __init__(self, default_config, **kwargs):
        """
        Creates a DefaultConfig parser using the default configuration
        in default_config.

        default_config must be an object that can be converted to type dict
        """
        self.__dict__ = dict(default_config)
        kwargs.setdefault('formatter_class',
                          argparse.ArgumentDefaultsHelpFormatter)
        Config.__init__(self, **kwargs)

    def add_argument(self, name, *args, **kwargs):
        """
        Adds an argument to this parser, with default values set
        based on the default configuration.

        Uses the same syntax as ArgumentParser.add_argument
        """
        basename = name[2:] if name.startswith('--') else name
        if hasattr(self, basename):
            kwargs.setdefault('default', getattr(self, basename))
        self._Config__parser.add_argument(name, *args, **kwargs)

class DefaultYAMLConfig(DefaultConfig):
    """
    This class works the same way as DefaultConfig.
    It loads the default configuration from a YAML configuration file.
    """
    def __init__(self, config_string, **kwargs):
        DefaultConfig.__init__(self, yaml.load(config_string), **kwargs)
