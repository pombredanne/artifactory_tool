# -*- coding: utf-8 -*-
# batteries included
import os
from copy import deepcopy

# thirdparty
import requests
import xmltodict

# this package
from utils import normalize_url
from exceptions import ConfigFetchError, InvalidAPICallError, InvalidCredentialsError, UnknownArtifactoryRestError

ART_REPO_TYPES = ["ALL", "LOCAL", "REMOTE", "VIRTUAL"]
ART_DEFAULT_REPOS = [
            'ext-release-local',
            'ext-snapshot-local',
            'libs-release-local',
            'libs-snapshot-local',
            'plugins-release-local',
            'plugins-snapshot-local',
            'jcenter-cache',
            'libs-release',
            'libs-snapshot',
            'plugins-release',
            'plugins-snapshot',
            'remote-repos',
            'jcenter'
        ]

def update_password(host_url, username, orig_pass, target_pass):
    """ set the password for the user to the target_pass

    Parameters
    ----------
    host_url : string
        A url of the form http(s)://domainname:port/context or
        http(s)://ip:port/context
    username : string
        username of the password to change
    orig_pass : string
        original password to use for the update
    target_pass : string
        the desired new password

    Returns
    -------
    changed : boolean
        True if changes were made

    Raises
    ------
    InvalidCredentialsError :
        If neither the original or target credentials work to update the password
    UnknownArtifactoryRestError :
        If we get a response we haven't encountered and don't kow what to do with
    """

    orig_auth = (username, orig_pass)
    target_auth = (username, target_pass)

    get_pass_url = '{}/artifactory/api/security/encryptedPassword'.format(
            normalize_url(host_url)
            )

    orig_resp = requests.get(get_pass_url, auth=orig_auth)
    if orig_resp.status_code == 401:
        resp = requests.get(get_pass_url, auth=target_auth)
        auth = target_auth
    elif orig_resp.status_code == 200:
        resp = orig_resp
        auth = orig_auth
    else:
        raise UnknownArtifactoryRestError(
                "Unexpected response when verifying credentials",
                orig_resp
                )

    if resp.status_code != 200:
        raise InvalidCrentialsError

    if auth == target_auth:
        return False

    user_json_url = '{}/artifactory/api/security/users/{}'.format(
            normalize_url(host_url),
            username
            )

    headers = {'Content-type': 'application/json'}
    user_dict_resp = requests.get(user_json_url, auth=auth)
    if not user_dict_resp.ok:
        if user_dict_resp.status == 401:
            msg = "Received an unauthorized message after authorization "
            msg += "has been checked.  Wtf?"
            raise UnknownArtifactoryRestError(msg, user_dict_resp)
        else:
            raise UnknownArtifactoryRestError(
                    "Couldn't get user information",
                    user_dict_resp
                    )

    admin_dict = user_dict_resp.json()
    admin_dict.pop('lastLoggedIn')
    admin_dict.pop('realm')
    admin_dict['password'] = target_pass

    update_resp = requests.post(
            user_json_url,
            auth=auth,
            json=admin_dict,
            headers=headers
            )

    if not update_resp.ok:
        if update_resp.status == 401:
            msg = "Received an unauthorized message after authorization "
            msg += "has been checked.  Wtf?"
            raise UnknownArtifactoryRestError(msg, update_resp)
        else:
            raise UnknownArtifactoryRestError(
                    "Couldn't post user password update",
                    update_resp
                    )

    final_check_resp = requests.get(get_pass_url, auth=target_auth)
    if not final_check_resp.ok:
        raise UnknownArtifactoryRestError(
                "Final password check failed.  Could not use new credentials",
                final_check_resp
                )

    else:
        return True

def get_artifactory_config_from_url(host_url, auth):
    """retrieve the artifactory configuration xml doc

    Parameters
    ----------
    host_url:   string
        A url of the form http(s)://domainname:port/context or
        http(s)://ip:port/context
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

    Should use
    https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON
    for the inputs.

    Does not error checking; will fail if the json is malformed.

    Parameters
    ----------
    host_url : string
        A url of the form
        http(s)://domainname:port[/context] or http(s)://ip:port[/context]
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
    ses = _get_artifactory_session(auth, session)
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

    # YELLOW need to add more logic to make this aware of if the configuration
    # is changing
    if resp.ok:
        return True
    else:
        return False

def _get_artifactory_session(username=None, passwd=None, auth=None,
        session=None):
    """ return a session with auth set.  prioritizes existing sessions,
        but validates that auth is set

    Parameters
    ----------
    username : string, optional
        username to create auth tuple from
    password : string, optional
        password for auth tuple
    auth : tuple, optional
        A tuple of (user, password), as used by requests
    session : requests.Session
        A requests.Session object, with auth

    Returns
    -------
    InvalidAPICallError
        When no combination of required inputs is given
    """
    if session is None and auth is None and username is None and passwd is None:
        raise InvalidAPICallError(
                "You must pass either username/password, auth, or session"
                )
    ses = None
    if session:
        if s.auth:
            ses = session

    if auth and not ses:
        ses = requests.Session()
        ses.auth = auth

    if (username and passwd) and not ses:
        auth = (username, passwd)
        ses = requests.Session()
        ses.auth = auth

    if not ses:
        raise InvalidAPICallError(
                "You must pass either username/password, auth, or session"
                )

    return ses

def get_repo_configs(host_url, repo_list, username=None, passwd=None,
        auth=None, session=None):
    """ return repository configuration dictionaries for specified set of repos

    Parameters
    ----------
    host_url : string
        An artifactory url of the form
        http(s)://domainname:port[/context] or http(s)://ip:port[/context]
    repo_list : list of strings
        A list of repo keys that you want to get configs for.  repo
        keys should match the url in the artifactory rest call
    username : string, optional
        username to create auth tuple from
    passwd : string, optional
        password for auth tuple
    auth : tuple, optional
        A tuple of (user, password), as used by requests
    session : requests.Session
        A requests.Session object, with auth

    Either session, auth, or user/pass must be defined.
    Session overrides auth overides username/password
    See _get_artifactory_session for details
    """
    ses = _get_artifactory_session(
            username=username,
            passwd=passwd,
            auth=auth,
            session=session
            )

    repo_configs_list = []
    for repo in repo_list:
        repo_url = '{}/artifactory/api/repositories/{}'.format(
                normalize_url(host_url),
                repo
                )
        resp = ses.get(repo_url)
        if not resp.ok:
            msg = "Failed to fetch config for {}".format(repo)
            raise UnknownArtifactoryRestError(msg, resp)

        repo_dict = resp.json()
        repo_configs_list.append(repo_dict)

    return repo_configs_list


def get_repo_list(host_url, repo_type="ALL", include_defaults=False,
        include_filter=None):
    """ return repository configuration dictionaries for specified set of repos

    Parameters
    ----------
    host_url : string
        An artifactory url of the form
        http(s)://domainname:port[/context] or http(s)://ip:port[/context]
    repo_type : {'all', 'LOCAL', 'REMOTE', 'VIRTUAL'}
        What types of repo (as defined by artifactory) to fetch.
    include_defaults : boolean
        Whether to include repos that ship with artifactory
    include_filter : string
        String which is used to do a simple filter of repo names. (in)
        Using this + naming convention can filter by package type.

    Either session, auth, or user/pass must be defined.
    Session overrides auth overides username/password
    See _get_artifactory_session for details
    """
    repos_url = '{}/artifactory/api/repositories'.format(host_url)
    resp = requests.get(repos_url)
    if not resp.ok:
        raise UnknownArtifactoryRestError("Error fetching repos", resp)

    final_repo_list = resp.json()

    if repo_type.upper() != "ALL":
        if repo_type.upper() not in ART_REPO_TYPES:
            raise InvalidAPICallError("repo_type must be one of {}".format(
                ART_REPO_TYPES
                )
            )
        final_repo_list = [r for r in final_repo_list
            if r['type'] == repo_type.upper()]

    if include_filter:
        final_repo_list = [r for r in final_repo_list
            if include_filter in r['url'].split('/')[-1]]

    if not include_defaults:
        final_repo_list = [r for r in final_repo_list
            if r['key'] not in ART_DEFAULT_REPOS]

    return final_repo_list


if __name__ == '__main__':
    print("This file is not the entrypoint for artifactory_tool")
    sys.exit(1)
