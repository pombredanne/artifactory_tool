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
import artifactory_tool as at
from artifactory_tool.exceptions import UnknownArtifactoryRestError

# "CONSTANTS"
FETCH_WHAT_HELP_STR = """ What type of configs you want to fetch.  current options are repos (which takes optional --include_defaults and --include_filter arguements
"""
FETCH_REPO_TYPE_HELP_STR = """Artifactory repo type.  One of LOCAL, REMOTE, VIRTUAL.  If not given, all will be retreived."""

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

def _config_admin_pass(host_url, password, target_password):
    """ set the admin password for artifactory

    Parameters
    ----------
    host_url : string
        url for artifactory server, sans artifactory
    password : string
        password for admin user
    target_password : string
        desired password for admin user
    """
    try:
        changed = at.update_password(
                host_url,
                'admin',
                password,
                target_password
                )
    except UnknownArtifactoryRestError as ae:
        click.echo("Failed to update password.")
        click.echo(ae.msg)
        raise
    except:
        click.echo("Failed to update password for reasons unknown.")
        raise

    if changed:
        click.echo("Password successfully changed")
    else:
        click.echo("Password already at target")

def _fetch_repos(host_url, username, password, inc_defaults, inc_filter,
        output_dir, repo_type):
    """ download json configurations for repos, place them in output dir

    Parameters
    ----------
    host_url : string
        url for artifactory server, don't include /artifactory context
    username : string
        admin username on artifactory server
    password : string
        password for admin user
    inc_defaults : boolean
        Whether we should include the repos artifactory ships with
    inc_filter : string
        Only include repos whose key includes this filter
    output_dir : string
        directory to write json files to
    repo_type : string
        One of the 3 artifactory repo types (LOCAL, REMOTE, VIRTUAL)
    """
    if repo_type is not None:
        repo_type = repo_type.upper()
        if repo_type not in ["LOCAL", "REMOTE", "VIRTUAL"]:
            click.echo("repo_type must be one of LOCAL, REMOTE, VIRTUAL")
            sys.exit(1)
    else:
        repo_type = "ALL"

    if not os.path.isdir(output_dir):
        click.echo("Can't find target directory.  Exiting")
        sys.exit(1)

    repo_obj_list = at.get_repo_list(
            host_url,
            repo_type=repo_type,
            include_defaults=inc_defaults,
            include_filter=inc_filter
            )

    if len(repo_obj_list) == 0:
        click.echo("No repos found.  Check your options")
        sys.exit(1)

    repo_list = [r['key'] for r in repo_obj_list]
    repo_config_list = at.get_repo_configs(
            host_url,
            repo_list,
            username=username,
            passwd=password
            )

    for repo in repo_config_list:
        repo_conf_file = os.path.join(output_dir, '{}.json'.format(repo['key']))
        with open(repo_conf_file, 'w') as f:
            f.write(json.dumps(repo, indent=4))

@click.group()
@click.option('--username', help="username with admin privileges")
@click.option('--password', help="password for user")
@click.option('--url', help="url and port for the artifactotry server")
@click.pass_context
def cli(ctx, **kwargs):
    """ Main entrypoint for artifactory_tool cli """
    ctx.obj = kwargs

@cli.group()
@click.pass_context
def fetch(ctx, **kwargs):
    """ fetch command group """
    ctx.obj.update(kwargs)

@fetch.command()
@click.option('--include_defaults', is_flag=True, default=False,
        help="include artifactory default repos with the repos arg")
@click.option('--include_filter',
        help="only repos that include this in their key will be fetched")
@click.option('--output_dir', default=os.getcwd(),
        help="directory to place files")
@click.option('--repo_type', help=FETCH_REPO_TYPE_HELP_STR)
@click.pass_context
def repos(ctx, **kwargs):
    """ commands for retreiving configs from artifactory
    """
    ctx.obj.update(kwargs)

    _fetch_repos(
        ctx.obj['url'],
        ctx.obj['username'],
        ctx.obj['password'],
        ctx.obj['include_defaults'],
        ctx.obj['include_filter'],
        ctx.obj['output_dir'],
        ctx.obj['repo_type']
        )

@cli.command()
@click.option('--ldap_json', help="json file for ldap settings")
@click.option('--repos_dir', help="Dir with repository configuration files")
@click.option('--admin_pass', help="set new admin password to this")
@click.pass_context
def configure(ctx, **kwargs):
    """ command(s) for configuring artifactory
    """
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

    if ctx.obj['admin_pass'] is not None:
        if ctx.obj['username'] != 'admin':
            click.echo("Must use the admin user to update the admin user")
            sys.exit(1)

        _config_admin_pass(
            ctx.obj['url'],
            ctx.obj['password'],
            ctx.obj['admin_pass']
            )

