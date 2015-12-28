# -*- coding: utf-8 -*-
# batteries included
import collections
import glob
import json
import os
import sys

# thirdparty libraies
import click
import requests

# This package
#from artifactory_tool import get_artifactory_config_from_url, update_artifactory_config, update_ldapSettings_from_dict
import artifactory_tool as at

def _get_ldap_dict(ldap_json):
    """ return an OrderedDict for the given json file

    Parameters
    ----------
    ldap_json : string
        filepath to json file with config options to be loaded

    Returns
    -------
    ldap_dict : collections.OrderedDict
        ordered dictionary for use in configuring artifactory
    """
    try:
        with click.open_file(ldap_json) as f:
            json_dict = json.load(f, object_pairs_hook=collections.OrderedDict)
    except:
        click.echo("whoops, can't open that ldap json file")
        raise

    return json_dict

def _config_ldap(url, username, password, ldap_json):
    """ _config_ldap gets the current configuration and a json file, and
    update the config if necessary

    Parameters
    ----------
    url : string
        url for artifactory server
    username : string
        admin username on artifactory server
    password : string
        password for admin user
    ldap_json :
        filepath to json file the represents the ldap dictionary
    """
    auth = (username, password)
    current_conf = at.get_artifactory_config_from_url(url, auth)
    ldap_dict = _get_ldap_dict(ldap_json)

    new_conf, changed = at.update_ldapSettings_from_dict(current_conf, ldap_dict)
    if changed:
        click.echo("Modifying ldap settings...")
        success = at.update_artifactory_config(url, auth, new_conf)
    else:
        click.echo("Ldap settings unchanged.")
        success = True

    if not success:
        click.echo("Sorrow.  Something went wrong")
        sys.exit(1)

def _config_repos(url, username, password, repo_dir):
    """ for each file in the directory, create or update that repo

    Each file should be a json file of the format
    https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON

    Parameters
    ----------
    url : string
        url for artifactory server
    username : string
        admin username on artifactory server
    password : string
        password for admin user
    repo_dir : string
        path to a directory with repository config json files

    Notes
    -----
    This function will organize the repositories in two groups:
    first, local and remote repos
    second, virtual repos.

    This is because virtual repos aggregate local and remote repos and thus
    the locals and remotes must be present before we create the virtuals
    """

    repos_list_dict = _get_repos_from_directory(repo_dir)
    ses = requests.Session()
    ses.auth = (username, password)
    for rclass in ['local', 'remote', 'virtual']:
        for repo_dict in repos_list_dict[rclass]:
            success = at.cr_repository(url, repo_dict, session=ses)
            if success:
                click.echo("Successfully updated {}".format(repo_dict['key']))
            else:
                click.echo("Failed updating {}".format(repo_dict['key']))

def _get_repos_from_directory(repo_dir):
    """ return a dictionary of lists with 3 keys:
    local, remote, virtual.

    Each item of the list will be a dictionary representing one of these:
    https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON

    Parameters
    ----------
    repo_dir : string
        path to a directory with repository config json files.  see above

    Returns
    -------
    repos_list_dict : dictionary
        see description above

    Notes
    -----
    This will ONLY find .json files
    """

    if not os.path.isdir(repo_dir):
        click.echo("{} is not a directory.".format(repo_dir))
        sys.exit(1)

    repos_list_dict = {
            "local": [],
            "remote": [],
            "virtual": []
            }
    for jfile in glob.glob('{}/*.json'.format(repo_dir)):
        with click.open_file(jfile) as f:
            jdict = json.loads(f.read())

        try:
            rclass = jdict['rclass']
            repos_list_dict[rclass].append(jdict)
        except KeyError:
            click.echo("file {} as no rclass key.".format(jfile))
            click.echo("Skipping.")

    return repos_list_dict

@click.group()
@click.option('--username', help="username with admin privileges")
@click.option('--password', help="password for user")
@click.option('--url', help="url and port for the artifactotry server")
@click.pass_context
def cli(ctx, **kwargs):
    """ Main entrypoint for artifactory_tool cli """
    ctx.obj = kwargs


@cli.command()
@click.option('--ldap_json', help="json file for ldap settings")
@click.option('--repos_dir', help="Dir with repository configuration files")
@click.pass_context
def configure(ctx, **kwargs):
    ctx.obj.update(kwargs)

    if ctx.obj['ldap_json'] is not None:
        _config_ldap(
            ctx.obj['url'],
            ctx.obj['username'],
            ctx.obj['password'],
            ctx.obj['ldap_json']
            )

    if ctx.obj['repos_dir'] is not None:
        _config_repos(
            ctx.obj['url'],
            ctx.obj['username'],
            ctx.obj['password'],
            ctx.obj['repos_dir']
            )
