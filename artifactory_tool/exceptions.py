 # -*- coding: utf-8 -*-

class ConfigFetchError(Exception):
    """Raised when we were unable to fetch the config from the server
    """

    def __init__(self, msg, response):
        self.msg = msg
        self.response = response
        super(ConfigFetchError, self)

class InvalidAPICallError(Exception):
    pass
