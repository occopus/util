#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains common OCCO API exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class InfrastructureIDTakenException(KeyError): pass
class InfrastructureIDNotFoundException(KeyError): pass
