# -*- coding: utf-8 -*-
# batteries included
import os
from copy import deepcopy

# thirdparty
import requests
import xmltodict

# this package
from utils import normalize_url
from exceptions import ConfigFetchError

def get_artifactory_config_from_url(host_url, auth):
    """retrieve the artifactory configuration xml doc

    Parameters
    ----------
    host_url:   string
                A url of the form http(s)://domainname:port or
                http(s)://ip:port
    auth:       tuple
                a tuple a la requests auth of the form (user, password)
    """
    headers = {'Accept': 'application/xml'}
    config_url = "{}/artifactory/api/system/configuration".format(
            normalize_url(host_url)
            )

    r = requests.get(config_url, auth=auth, headers=headers)
    if r.ok:
        return(xmltodict.parse(r.text))
    else:
        raise ConfigFetchError("Something went wrong getting the config", r)

def update_ldapSettings_from_dict(config_dict, desired_dict):
    """match the ldap settings in the config_dict to the desired endstate

    Parameters
    ----------
    config_dict : dictionary
                 the source configuration dictionary
    desired_dict : dictionary
                  the ldap subdictionary that we want to use

    Returns
    -------
    return_dict : dictonary
        A copy of the original config dict, plus any modfications made
    changed : boolean
        Whether or not changes were made
    """

    return_dict = deepcopy(config_dict)
    orig_ldap_settings = return_dict['config']['security']['ldapSettings']
    if orig_ldap_settings == desired_dict:
        return return_dict, False

    # RED at the very least, this should validate the resulting xml
    # or, it should only update the changed keys so we know what they are
    # consider using easyXSD, but might want to avoid lxml
    else:
        return_dict['config']['security']['ldapSettings'] = desired_dict
        return return_dict, True

def update_artifactory_config(host_url, auth, config_dict):
    """ take a configuraiton dict and upload it to artifactory

    Parameters
    ----------
    host_url : string
        A url of the form http(s)://domainname:port or http(s)://ip:port
    auth : tuple
        A tuple of (user, password), as used by requests
    config_dict : OrderedDict a dict representation that will be returned to xml

    Returns:
    success : boolean
        true if we succeeded
    """
    headers = {'Content-type': 'application/xml'}
    config_url = "{}/artifactory/api/system/configuration".format(
            normalize_url(host_url)
            )
    xml_config = xmltodict.unparse(config_dict)

    r = requests.post(config_url, auth=auth, headers=headers, data=xml_config)

    if r.ok:
        return True
    else:
        return False


if __name__ == '__main__':
    print("This file is not the entrypoint for artifactory_tool")
    sys.exit(1)
