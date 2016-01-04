 # -*- coding: utf-8 -*-

class ConfigFetchError(Exception):
    """Raised when we were unable to fetch the config from the server
    """

    def __init__(self, msg, response):
        self.msg = msg
        self.response = response
        super(Exception, self)

class InvalidAPICallError(Exception):
    pass

class UnknownArtifactoryRestError(Exception):
    """ Raised if we don't know what happened with an artifactory rest call"""

    def __init__(self, msg, response):
        self.msg = msg
        self.response = response
        super(Exception, self)

class InvalidCredentialsError(Exception):
    """
    Raised if none of the provided crendentials provide the correct
    authorization
    """
    pass
