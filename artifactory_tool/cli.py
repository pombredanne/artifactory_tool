# -*- coding: utf-8 -*-
# batteries included
import collections
import json
import os
import sys

# thirdparty libraies
import click

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
@click.pass_context
def configure(ctx, **kwargs):
    ctx.obj.update(kwargs)

    _config_ldap(
            ctx.obj['url'],
            ctx.obj['username'],
            ctx.obj['password'],
            ctx.obj['ldap_json']
            )
