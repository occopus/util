#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains common OCCO exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class ConfigurationError(Exception):
    """Raised by communication classes, if the given configuration is bad, or
    insufficient."""
    pass
