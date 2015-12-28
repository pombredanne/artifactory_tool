# -*- coding: utf-8 -*-
# batteries included
import os
from copy import deepcopy

# thirdparty
import requests
import xmltodict

# this package
from utils import normalize_url
from exceptions import ConfigFetchError, InvalidAPICallError

def get_artifactory_config_from_url(host_url, auth):
    """retrieve the artifactory configuration xml doc

    Parameters
    ----------
    host_url:   string
        A url of the form http(s)://domainname:port/context or http(s)://ip:port/context
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
        A url of the form http(s)://domainname:port[/context] or http(s)://ip:port[/context]
    auth : tuple
        A tuple of (user, password), as used by requests
    config_dict : OrderedDict
        a dict representation that will be returned to xml

    Returns:
    --------
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

def cr_repository(host_url, repo_dict, auth=None, session=None):
    """ take a configuration dict and post it host_url

    Should use https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON
    for the inputs.

    Does not error checking; will fail if the json is malformed.

    Parameters
    ----------
    host_url : string
        A url of the form http(s)://domainname:port[/context] or http(s)://ip:port[/context]
    repo_dict : OrderedDict
        a dictionary of the inputs required by artifactroy.  see above.
    auth : tuple, optional
        A tuple of (user, password), as used by requests
    session : requests Session object, optional
        A session object (that has any necessary cookies / headers defined)

    Either auth or session must be defined.  Session overrides auth.

    Returns
    -------
    success : boolean
        true if succeeded

    """
    if session is None and auth is None:
        raise InvalidAPICallError("You must pass either auth or session to cr_repository")

    if session:
        ses = session
    else:
        ses = requests.Session()
        ses.auth = auth

    if 'key' not in repo_dict:
        raise InvalidAPICallError("The repo_dict must include a repo key (repo_dict['key'])")

    repo_url = '{}/artifactory/api/repositories/{}'.format(
            normalize_url(host_url),
            repo_dict['key']
            )

    headers = {'Content-type': 'application/json'}
    exists_resp = ses.get(repo_url)
    if exists_resp.ok:
        resp = ses.post(repo_url, json=repo_dict, headers=headers)
    else:
        resp = ses.put(repo_url, json=repo_dict, headers=headers)

    if resp.ok:
        return True
    else:
        return False

if __name__ == '__main__':
    print("This file is not the entrypoint for artifactory_tool")
    sys.exit(1)
