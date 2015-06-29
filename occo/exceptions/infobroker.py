#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains common OCCO InfoBroker exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class KeyNotFoundError(KeyError):
    """Thrown by :meth:`InfoProvider.get` functions when a given key cannot be
    handled."""
    pass

class ArgumentError(ValueError):
    """Thrown by :meth:`InfoProvider.get` functions when there is an error in
    its arguments."""
    pass
