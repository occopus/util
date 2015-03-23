#
# Copyright (C) 2014 MTA SZTAKI
#

from __future__ import absolute_import

"""
Configuration primitives for the SZTAKI Cloud Orchestrator.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module implements a configuration interface, with its main purpose
being the simple merging of statically configured and command line parameters.

The interface proxies ``add_argument`` and ``parse_args calls to the underlying
``argparse.ArgumentParser`` object.

Basically, this module provides an ``ArgumentParser`` that can be pre-filled
with statically defined data.
"""

__all__ = ['Config', 'DefaultConfig', 'DefaultYAMLConfig', 'config',
           'PythonImport', 'YAMLImport']

import yaml
import argparse
from ...util import curried, cfg_file_path, rel_to_file, \
    path_coalesce, file_locations, set_config_base_dir
import occo.util.factory as factory
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

        See also: `Python docs <https://docs.python.org/2/library/argparse.html#the-add-argument-method>`_
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

class YAMLImport(object):
    """
    YAML constructor. Import an external YAML file and replace the current node
    with its content.

    :param callable parser: The parser function used to interpret the content
        of the external file.

    The mapping must contain a node called 'url'. The schema of the URL will
    determine how the mapping will be interpreted.

    The following schema are supported:

        ``file``

            Reads and parses a YAML file specified by the URL. The path can be
            either absolute or relative; e.g.: ``file:///etc/global_config`` or
            ``file://global_config``.

            Relative paths are interpreted using
            :func:`~occo.util.general.cfg_file_path`.

    .. code-block:: yaml
        :emphasize-lines: 8,9

        cloud_handler: !CloudHandler
            protocol: boto
            name: LPDS
            dry_run: false
            target:
                endpoint: http://cfe2.lpds.sztaki.hu:4567
                regionname: ROOT
            auth_data: !yaml_import
                url: file://auth_data.yaml
    """

    def __init__(self, parser):
        self.parser = parser

    def __call__(self, loader, node):
        return self._load(**loader.construct_mapping(node, deep=True))

    def _load(self, **kwargs):
        log = logging.getLogger('occo.util')
        log.debug(yaml.dump(self, default_flow_style=False))

        from urlparse import urlparse
        url = urlparse(kwargs['url'])
        log.info('%r', kwargs)
        importer = YAMLImporter(
            protocol=url.scheme, parser=self.parser, **kwargs)
        return importer._load()

class YAMLImporter(factory.MultiBackend):
    def __init__(self, protocol, parser, **data):
        self.parser = parser
        self.__dict__.update(data)
    def _load(self):
        raise NotImplementedError()
@factory.register(YAMLImporter, 'file')
class FileImporter(YAMLImporter):
    def _load(self):
        log = logging.getLogger('occo.util')
        # TODO This should be relative to the importing config file
        filename = cfg_file_path(self.url[7:])
        log.debug("Importing YAML file: '%s'", filename)
        with open(filename) as f:
            return self.parser(f)

def filetext(f):
    return f.read()

yaml.add_constructor('!yaml_import', YAMLImport(yaml.load))
yaml.add_constructor('!text_import', YAMLImport(filetext))

class PythonImport:
    """
    YAML constructor. Appliable to string lists; imports all modules listed.

    This can be used to pre-load factory-implementation modules at the
    beginning of a YAML file. E.g.:
    :class:`~occo.cloudhandler.backends.boto.BotoCloudHandler`.

    In effect, importing these modules from generic programs becomes
    unnecessary; therefore these programs become future proof. For example:
    they cannot know about future backends; and they don't need to.

    Example:

    .. code-block:: yaml

        autoimport: !python_import
            - occo.infobroker
            - occo.infobroker.cloud_provider
            - occo.infobroker.uds
            - occo.cloudhandler
            - occo.cloudhandler.backends.boto
            - occo.infraprocessor

        # The following would fail without (auto)importing the necessary modules
        cloud_handler: !CloudHandler
            protocol: boto
            name: LPDS
    """
    def __call__(self, loader, node):
        return [__import__(module.value) for module in node.value]
yaml.add_constructor('!python_import', PythonImport())

def config(default_config=dict(), setup_args=None):
    default_config.setdefault('cfg', None)

    #
    ## Find and load main config file
    #
    cfg = DefaultConfig(default_config)
    cfg.add_argument(name='--cfg', dest='cfg_path', type=cfg_file_path)
    if setup_args:
        setup_args(cfg)
    cfg.parse_args()

    if not cfg.cfg_path:
        possible_locations = file_locations('occo.yaml',
            '.',
            curried(rel_to_file, basefile=__file__),
            cfg_file_path)

        cfg.cfg_path = path_coalesce(*possible_locations)

    import os
    set_config_base_dir(os.path.dirname(cfg.cfg_path))

    with open(cfg.cfg_path) as f:
        cfg.configuration = yaml.load(f)

    #
    ## Setup logging
    #
    import os
    import logging
    import logging.config
    logging.config.dictConfig(cfg.configuration['logging'])

    log = logging.getLogger('occo')
    log.info('Staring up; PID = %d', os.getpid())

    return cfg
